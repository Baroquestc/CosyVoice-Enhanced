import os
import sys
import time
import argparse
import subprocess
import threading
from pathlib import Path
from io import BytesIO
import tempfile
from collections import OrderedDict

import torch
import torchaudio
import librosa
import numpy as np
import pyloudnorm
from flask import Flask, request, Response, jsonify, stream_with_context

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from cosyvoice.cli.cosyvoice import CosyVoice, CosyVoice2
from cosyvoice.utils.file_utils import load_wav

# Setup paths
root_dir = Path(__file__).parent.parent.absolute()

# FFmpeg path setup
if sys.platform == 'win32':
    ffmpeg_path = root_dir / 'ffmpeg' / 'bin'
    os.environ['PATH'] = f"{root_dir};{ffmpeg_path};{os.environ['PATH']}"
else:
    ffmpeg_path = root_dir / 'ffmpeg'
    os.environ['PATH'] = f"{root_dir}:{ffmpeg_path}:{os.environ['PATH']}"

sys.path.append(str(root_dir / 'third_party' / 'Matcha-TTS'))

# Import VLLM utilities for auto-detection
from utils.vllm_utils import check_vllm_availability, should_enable_vllm_for_model, log_vllm_status, register_cosyvoice2_vllm

# Model downloading utilities
try:
    from modelscope import snapshot_download
    MODELSCOPE_AVAILABLE = True
except ImportError:
    MODELSCOPE_AVAILABLE = False

# Create directories
for dir_name in ['tmp', 'logs']:
    (root_dir / dir_name).mkdir(exist_ok=True)

print(f"Root directory: {root_dir}")

# Log VLLM availability status
log_vllm_status()

# Voice mapping for OpenAI compatibility

SUPPORTED_FORMATS = ['mp3', 'opus', 'aac', 'flac', 'wav', 'pcm']
supported_voices = None
# Global model instance
tts_model = None
is_cosyvoice2 = False
model_lock = threading.Lock()

# 最大缓存数量和全局缓存
MAX_VOICE_CACHE_SIZE = 100  # 可调整
voice_cache = OrderedDict()
voice_cache_lock = threading.Lock()

# Audio normalization parameters
TARGET_LOUDNESS_LUFS = -16.0  # Target loudness in LUFS (Loudness Units Full Scale)
LOUDNESS_RANGE_LU = 7.0  # Target loudness range in LU
audio_norm_state = {
    'lufs_history': [],
    'window_size': 5,  # Number of chunks to consider for adaptive normalization
    'target_lufs': -16.0,  # Default target LUFS for normalization (broadcast standard)
    'previous_gain': 1.0,  # Store previous gain for smoothing
    'max_gain_change': 1.5,  # Maximum allowed gain change ratio between chunks
    'meter': None,  # Will store the pyloudnorm meter instance
}
audio_norm_lock = threading.Lock()

def normalize_audio(audio, sample_rate, target_lufs=None, adaptive=True):
    """
    Apply automatic gain control and loudness balancing to audio using pyloudnorm
    
    Args:
        audio: PyTorch tensor or numpy array containing audio data
        sample_rate: Audio sample rate
        target_lufs: Target LUFS level for normalization (if None, use the current state value)
        adaptive: Whether to use adaptive gain based on history
        
    Returns:
        Normalized audio in the same format and shape as input
    """
    global audio_norm_state
    
    # Track input type and shape for consistent output format
    is_tensor = isinstance(audio, torch.Tensor)
    original_shape = audio.shape if is_tensor else np.shape(audio)
    is_1d = len(original_shape) == 1
    
    # Use global target_lufs if none provided
    if target_lufs is None:
        target_lufs = audio_norm_state['target_lufs']
    else:
        # Ensure target_lufs is within reasonable limits
        target_lufs = min(max(target_lufs, -30), -10)
    
    # Convert PyTorch tensor to numpy if needed
    if is_tensor:
        audio_np = audio.detach().cpu().numpy()
    else:
        audio_np = audio
    
    # Store original data type for consistent output
    original_dtype = audio_np.dtype
    
    # Ensure audio is properly shaped for pyloudnorm (samples, channels)
    if audio_np.ndim == 1:
        # Mono audio - reshape to (samples, 1)
        audio_np = audio_np.reshape(-1, 1)
    elif audio_np.ndim > 2:
        # Too many dimensions - flatten to mono
        audio_np = np.mean(audio_np, axis=tuple(range(1, audio_np.ndim))).reshape(-1, 1)
    
    # Skip processing if audio is too short or silent
    if len(audio_np) < 256 or np.max(np.abs(audio_np)) < 1e-6:
        # Return in the original format and shape
        if is_1d and audio_np.shape[1] == 1:
            result = audio_np.reshape(-1)
        else:
            result = audio_np
            
        # Convert back to tensor if input was tensor
        if is_tensor:
            return torch.from_numpy(result).to(audio.dtype).to(audio.device)
        return result
    
    try:
        # Initialize meter if needed - do this outside the lock
        meter = None
        if audio_norm_state['meter'] is None or audio_norm_state['meter'].rate != sample_rate:
            try:
                # Create a new meter instance
                meter = pyloudnorm.Meter(sample_rate)
                # Only update the global meter if it's still None or has a different rate
                with audio_norm_lock:
                    if audio_norm_state['meter'] is None or audio_norm_state['meter'].rate != sample_rate:
                        audio_norm_state['meter'] = meter
            except Exception as e:
                print(f"Failed to create loudness meter: {e}")
                # Continue with existing meter or None
        
        # Use the meter we created or get from global state
        if meter is None:
            meter = audio_norm_state['meter']
        
        # Skip loudness processing if meter creation failed
        if meter is None:
            print("Skipping normalization: No valid loudness meter")
            # Return in the original format and shape
            if is_1d and audio_np.shape[1] == 1:
                result = audio_np.reshape(-1)
            else:
                result = audio_np
                
            # Convert back to tensor if input was tensor
            if is_tensor:
                return torch.from_numpy(result).to(audio.dtype).to(audio.device)
            return result
        
        # Measure the current loudness (LUFS)
        try:
            current_lufs = meter.integrated_loudness(audio_np)
        except (ValueError, RuntimeWarning, ZeroDivisionError) as e:
            # If measurement fails (e.g., audio too short), use a default value
            print(f"Loudness measurement warning: {e}")
            current_lufs = -30.0
        
        # Handle silence or very quiet audio
        if current_lufs < -70 or np.isnan(current_lufs):
            current_lufs = -30.0
        
        # Get previous gain for smoothing (with safety default)
        previous_gain = 1.0
        try:
            # Short lock to read previous gain
            if audio_norm_lock.acquire(blocking=True, timeout=0.005):
                try:
                    previous_gain = audio_norm_state['previous_gain']
                    if not (0.1 <= previous_gain <= 10.0):
                        previous_gain = 1.0
                finally:
                    audio_norm_lock.release()
        except Exception:
            # If lock acquisition fails, use default
            previous_gain = 1.0
        
        # Adaptive target LUFS calculation
        adaptive_target = target_lufs  # Default to non-adaptive target
        if adaptive:
            # Try to acquire lock for history update, but don't block for too long
            lock_acquired = False
            try:
                lock_acquired = audio_norm_lock.acquire(blocking=True, timeout=0.01)
                if lock_acquired:
                    # Update history
                    audio_norm_state['lufs_history'].append(current_lufs)
                    if len(audio_norm_state['lufs_history']) > audio_norm_state['window_size']:
                        audio_norm_state['lufs_history'].pop(0)
                    
                    # Calculate adaptive target based on history with outlier detection
                    if len(audio_norm_state['lufs_history']) >= 3:
                        # Filter out outliers (values more than 10 LUFS from median)
                        history = np.array(audio_norm_state['lufs_history'])
                        median_lufs = np.median(history)
                        filtered_history = history[np.abs(history - median_lufs) < 10.0]
                        
                        # If we filtered out everything, use the original history
                        if len(filtered_history) == 0:
                            filtered_history = history
                        
                        # Use the average of filtered history as adaptive target
                        adaptive_target = np.mean(filtered_history)
                        
                        # Gradually adjust global target toward specified target with more weight on stability
                        audio_norm_state['target_lufs'] = 0.95 * audio_norm_state['target_lufs'] + 0.05 * target_lufs
                        
                        # Blend adaptive and global targets with more weight on global for stability
                        target_lufs = 0.4 * adaptive_target + 0.6 * audio_norm_state['target_lufs']
            finally:
                if lock_acquired:
                    audio_norm_lock.release()
        
        # Calculate gain needed
        delta_lufs = target_lufs - current_lufs
        raw_gain = np.power(10.0, delta_lufs / 20.0)
        
        # Apply gain with safety limits to prevent excessive amplification
        raw_gain = min(max(raw_gain, 0.1), 10.0)
        
        # Apply gain smoothing to prevent sudden changes
        max_change_ratio = 1.5  # Default
        try:
            # Short lock to read max_change_ratio
            if audio_norm_lock.acquire(blocking=True, timeout=0.005):
                try:
                    max_change_ratio = audio_norm_state.get('max_gain_change', 1.5)
                finally:
                    audio_norm_lock.release()
        except Exception:
            pass
            
        # Ensure max_change_ratio is reasonable
        max_change_ratio = min(max(max_change_ratio, 1.1), 3.0)
            
        # Apply gain limiting based on previous gain
        if raw_gain > previous_gain * max_change_ratio:
            gain = previous_gain * max_change_ratio
        elif raw_gain < previous_gain / max_change_ratio:
            gain = previous_gain / max_change_ratio
        else:
            gain = raw_gain
            
        # Further smooth the gain change
        gain = 0.7 * previous_gain + 0.3 * gain
        
        # Store the current gain for next chunk - short lock
        try:
            if audio_norm_lock.acquire(blocking=True, timeout=0.005):
                try:
                    audio_norm_state['previous_gain'] = gain
                finally:
                    audio_norm_lock.release()
        except Exception:
            # If we can't store the gain, continue without updating
            pass
        
        # Apply gain to audio
        normalized_audio = audio_np * gain
        
        # Apply soft limiting to prevent clipping
        if np.max(np.abs(normalized_audio)) > 0.95:
            normalized_audio = np.tanh(normalized_audio)
        
        # Return in the same format and shape as input
        if is_1d and normalized_audio.shape[1] == 1:
            result = normalized_audio.reshape(-1)
        else:
            result = normalized_audio
            
        # Convert back to tensor if input was tensor
        if is_tensor:
            return torch.from_numpy(result).to(audio.dtype).to(audio.device)
        return result
        
    except Exception as e:
        print(f"Audio normalization error: {e}")
        # Return original audio in the same format as input
        if is_1d and audio_np.shape[1] == 1:
            result = audio_np.reshape(-1)
        else:
            result = audio_np
            
        # Convert back to tensor if input was tensor
        if is_tensor:
            return torch.from_numpy(result).to(audio.dtype).to(audio.device)
        return result

def tensor_to_audio_bytes(tensor, sample_rate, output_format='wav'):
    """Convert PyTorch tensor to audio bytes in specified format"""
    try:
        # Ensure tensor is on CPU and in correct format
        if isinstance(tensor, torch.Tensor):
            audio = tensor.detach().cpu().float()
            
            # Handle different tensor shapes
            if audio.dim() == 2:
                if audio.shape[0] == 1:
                    audio = audio.squeeze(0)  # Remove batch dimension
                elif audio.shape[1] == 1:
                    audio = audio.squeeze(1)  # Remove channel dimension
                else:
                    audio = audio[0]  # Take first channel
            
            # Apply automatic gain control and loudness balancing using global settings
            normalized_audio = normalize_audio(audio, sample_rate)
            
            # Convert back to tensor if needed
            if isinstance(normalized_audio, np.ndarray):
                audio = torch.from_numpy(normalized_audio).float()
            else:
                audio = normalized_audio
            
            # Handle PCM format specially
            if output_format == 'pcm':
                # PCM: Convert to 16-bit signed integers at 24kHz as per OpenAI spec
                target_sample_rate = 24000
                
                # Resample if needed
                if sample_rate != target_sample_rate:
                    resampler = torchaudio.transforms.Resample(
                        orig_freq=sample_rate,
                        new_freq=target_sample_rate
                    )
                    audio = resampler(audio)
                
                # Convert to 16-bit PCM
                audio_int16 = (audio * 32767.0).clamp(-32768, 32767).to(torch.int16)
                return audio_int16.numpy().tobytes()
            else:
                # For other formats, use torchaudio
                buffer = BytesIO()
                torchaudio.save(buffer, audio.unsqueeze(0), sample_rate, format=output_format)
                return buffer.getvalue()
        
        return tensor  # Already bytes
        
    except Exception as e:
        print(f"Error converting tensor to audio: {e}")
        raise

def convert_audio_format(audio_bytes, input_format='wav', output_format='mp3'):
    """Convert audio bytes from one format to another using FFmpeg"""
    if input_format == output_format:
        return audio_bytes
    
    # PCM doesn't need FFmpeg conversion since it's handled in tensor_to_audio_bytes
    if output_format == 'pcm':
        return audio_bytes
    
    try:
        # FFmpeg command for format conversion
        cmd = [
            'ffmpeg', '-hide_banner', '-loglevel', 'error',
            '-f', input_format, '-i', 'pipe:0',
        ]
        
        # Output format specific settings
        if output_format == 'mp3':
            cmd.extend(['-acodec', 'libmp3lame', '-b:a', '128k'])
        elif output_format == 'opus':
            cmd.extend(['-acodec', 'libopus', '-b:a', '64k'])
        elif output_format == 'aac':
            cmd.extend(['-acodec', 'aac', '-b:a', '128k'])
        elif output_format == 'flac':
            cmd.extend(['-acodec', 'flac'])
        
        cmd.extend(['-f', output_format, 'pipe:1'])
        
        # Run FFmpeg
        process = subprocess.run(
            cmd,
            input=audio_bytes,
            capture_output=True,
            check=True
        )
        
        return process.stdout
        
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg error: {e.stderr.decode()}")
        raise Exception(f"Audio conversion failed: {e.stderr.decode()}")
    except Exception as e:
        print(f"Conversion error: {e}")
        raise

def check_model_exists(model_dir):
    """Check if model directory exists and contains required files"""
    if not os.path.exists(model_dir):
        return False
    
    # Check for essential model files
    required_files = ['cosyvoice.yaml']
    for file in required_files:
        if not os.path.exists(os.path.join(model_dir, file)):
            return False
    
    return True

def get_model_id_from_path(model_dir):
    """Get ModelScope model ID from model directory path"""
    model_mapping = {
        'CosyVoice2-0.5B': 'iic/CosyVoice2-0.5B',
        'CosyVoice-300M': 'iic/CosyVoice-300M', 
        'CosyVoice-300M-SFT': 'iic/CosyVoice-300M-SFT',
        'CosyVoice-300M-Instruct': 'iic/CosyVoice-300M-Instruct',
        'CosyVoice-ttsfrd': 'iic/CosyVoice-ttsfrd'
    }
    
    # Extract model name from path
    model_name = os.path.basename(model_dir.rstrip('/'))
    return model_mapping.get(model_name)

def download_model(model_dir):
    """Download model from ModelScope if not exists"""
    if not MODELSCOPE_AVAILABLE:
        print("❌ ModelScope not available. Please install with: pip install modelscope")
        return False
    
    model_id = get_model_id_from_path(model_dir)
    if not model_id:
        print(f"❌ Unknown model directory: {model_dir}")
        print("Supported models: CosyVoice2-0.5B, CosyVoice-300M, CosyVoice-300M-SFT, CosyVoice-300M-Instruct, CosyVoice-ttsfrd")
        return False
    
    try:
        print(f"📥 Downloading model {model_id} to {model_dir}...")
        snapshot_download(model_id, local_dir=model_dir)
        print(f"✅ Model downloaded successfully!")
        return True
    except Exception as e:
        print(f"❌ Failed to download model: {e}")
        return False

def ensure_model_available(model_dir):
    """Ensure model is available, download if necessary"""
    if check_model_exists(model_dir):
        print(f"✅ Model found: {model_dir}")
        return True
    
    print(f"⚠️  Model not found: {model_dir}")
    
    # Create parent directory if it doesn't exist
    os.makedirs(os.path.dirname(model_dir), exist_ok=True)
    
    return download_model(model_dir)

def get_mime_type(format_type):
    """Get MIME type for audio format"""
    mime_types = {
        'mp3': 'audio/mpeg',
        'opus': 'audio/opus',
        'aac': 'audio/aac', 
        'flac': 'audio/flac',
        'wav': 'audio/wav',
        'pcm': 'audio/L16; rate=24000; channels=1'  # Proper PCM MIME type with specs
    }
    return mime_types.get(format_type, 'audio/wav')

def validate_request(data):
    """Validate OpenAI TTS API request"""
    if not data:
        raise ValueError("Request body must be JSON")
    
    # Required parameters
    input_text = data.get('input', '').strip()
    if not input_text:
        raise ValueError("Missing required parameter: 'input'")
    
    voice = data.get('voice', '').strip()
    if not voice:
        raise ValueError("Missing required parameter: 'voice'")
    
    # Optional parameters with validation
    response_format = data.get('response_format', 'mp3').lower()
    if response_format not in SUPPORTED_FORMATS:
        raise ValueError(f"Invalid response_format '{response_format}'. Supported formats: {SUPPORTED_FORMATS}")
    
    speed = float(data.get('speed', 1.0))
    if not (0.25 <= speed <= 4.0):
        raise ValueError("Speed must be between 0.25 and 4.0")
    
    # Stream parameter (optional, defaults to False)
    stream = bool(data.get('stream', False))
    
    # Create result dictionary with required and common optional parameters
    result = {
        'input': input_text,
        'voice': voice,
        'response_format': response_format,
        'speed': speed,
        'model': data.get('model', 'tts-1'),
        'stream': stream
    }
    
    # Only include audio normalization parameters if explicitly provided
    if 'target_lufs' in data:
        target_lufs = float(data['target_lufs'])
        if not (-30 <= target_lufs <= -10):
            raise ValueError("target_lufs must be between -30 and -10")
        result['target_lufs'] = target_lufs
        
    if 'adaptive_gain' in data:
        result['adaptive_gain'] = bool(data['adaptive_gain'])
    
    return result

def create_app():
    app = Flask(__name__)
    
    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({
            "status": "healthy",
            "model_loaded": tts_model is not None
        })
    
    @app.route('/v1/audio/speech', methods=['POST'])
    def text_to_speech():
        try:
            # Validate request
            data = request.get_json()
            params = validate_request(data)
            
            # Check if model is loaded
            if tts_model is None:
                return jsonify({
                    "error": {
                        "message": "Model not loaded",
                        "type": "server_error",
                        "code": "model_not_loaded"
                    }
                }), 500
            
            # Map voice to internal format
            voice = params['voice']
            speed = params['speed']
            # if voice in the tts_model.
            is_voice_supported = voice in supported_voices;

            if not is_voice_supported:
                # if the voice is not supported, return the error
                return jsonify({
                    "error": {
                        "message": "Voice not supported",
                        "type": "invalid_request_error",
                        "code": "voice_not_supported"
                    }
                }), 500

            stream = params['stream']
            # check if the input contains <|endofprompt|>
            # if input contains <|endofprompt|>, then split the input into two parts use <|endofprompt|>, the first part as the prompt for zero shot and the second part as the input
            use_instruct = "<|endofprompt|>" in params['input']

            if use_instruct:
                instruct_text = params['input'].split("<|endofprompt|>")[0]
                tts_text = params['input'].split("<|endofprompt|>")[1]
            else:
                instruct_text = ""
                tts_text = params['input']
            
            def generate_audio_stream():
                """Generator function for streaming audio"""
                try:
                    # Reset audio normalization state for new stream
                    with audio_norm_lock:
                        audio_norm_state['lufs_history'] = []
                        # Use user-specified target_lufs if provided, otherwise use default value
                        audio_norm_state['target_lufs'] = params.get('target_lufs', audio_norm_state['target_lufs'])
                        # Reset previous gain to default value for a new stream
                        audio_norm_state['previous_gain'] = 1.0
                    
                    print(f"Target LUFS: {audio_norm_state['target_lufs']}")
                    
                    with model_lock:
                        if use_instruct:
                            if is_cosyvoice2:
                                audio_generator = tts_model.inference_instruct2(
                                    tts_text=tts_text,
                                    instruct_text=instruct_text,
                                    zero_shot_spk_id=voice,
                                    stream=stream,
                                    speed=speed
                                )
                            else:
                                audio_generator = tts_model.inference_instruct(
                                    tts_text=tts_text,
                                    spk_id=voice,
                                    instruct_text=instruct_text,
                                    stream=stream,
                                    speed=speed
                                )
                        else:   
                            audio_generator = tts_model.inference_sft(
                                tts_text=tts_text,
                                spk_id=voice,
                                stream=stream,
                                speed=speed
                            )
                    
                    # Process each audio chunk
                    for chunk in audio_generator:
                        try:
                            # Extract audio tensor from chunk
                            if isinstance(chunk, dict) and 'tts_speech' in chunk:
                                audio_tensor = chunk['tts_speech']
                            else:
                                audio_tensor = chunk
                            
                            if audio_tensor is None:
                                continue
                            
                            # Convert tensor to target format
                            if params['response_format'] == 'pcm':
                                # Direct PCM conversion without intermediate WAV
                                pcm_bytes = tensor_to_audio_bytes(
                                    audio_tensor,
                                    tts_model.sample_rate,
                                    'pcm'
                                )
                                yield pcm_bytes
                            else:
                                # Convert tensor to WAV bytes first for other formats
                                wav_bytes = tensor_to_audio_bytes(
                                    audio_tensor, 
                                    tts_model.sample_rate, 
                                    'wav'
                                )
                                
                                # Convert to target format if needed
                                if params['response_format'] != 'wav':
                                    try:
                                        converted_bytes = convert_audio_format(
                                            wav_bytes, 
                                            'wav', 
                                            params['response_format']
                                        )
                                        yield converted_bytes
                                    except Exception as conv_error:
                                        print(f"Format conversion failed: {conv_error}")
                                        # Fallback to WAV if conversion fails
                                        yield wav_bytes
                                else:
                                    yield wav_bytes
                                
                        except Exception as chunk_error:
                            print(f"Error processing chunk: {chunk_error}")
                            continue
                            
                except Exception as e:
                    print(f"Audio generation error: {e}")
                    raise
            
            # Return streaming response with proper headers
            response = Response(
                stream_with_context(generate_audio_stream()),
                mimetype=get_mime_type(params['response_format']),
                headers={ 
                    # 'Transfer-Encoding': 'chunked', AssertionError: Transfer-Encoding is a "hop-by-hop" header; it cannot be used by a WSGI application (see PEP 3333)
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0'
                }
            )
            
            return response
            
        except ValueError as e:
            return jsonify({
                "error": {
                    "message": str(e),
                    "type": "invalid_request_error",
                    "code": "invalid_parameter"
                }
            }), 400
            
        except Exception as e:
            print(f"TTS API error: {e}")
            return jsonify({
                "error": {
                    "message": "Internal server error",
                    "type": "server_error", 
                    "code": "internal_error"
                }
            }), 500
    
    return app

def load_model(model_dir, **kwargs):
    """Load TTS model with error handling and automatic VLLM integration"""
    global tts_model
    global supported_voices
    global is_cosyvoice2

    try:
        # Check if model directory exists
        if not os.path.exists(model_dir):
            print(f"Model directory not found: {model_dir}")
            return False
        
        # Determine model type
        is_cosyvoice2 = 'CosyVoice2' in model_dir or os.path.exists(os.path.join(model_dir, 'cosyvoice2.yaml'))
        
        print(f"Loading {'CosyVoice2' if is_cosyvoice2 else 'CosyVoice'} model from: {model_dir}")
        
        # Auto-enable VLLM for CosyVoice2 models if available and not explicitly disabled
        if is_cosyvoice2 and 'load_vllm' not in kwargs:
            auto_vllm = should_enable_vllm_for_model(model_dir)
            if auto_vllm:
                print("🚀 Auto-enabling VLLM acceleration for CosyVoice2 model")
                # Register CosyVoice2 with VLLM
                register_cosyvoice2_vllm()
                kwargs['load_vllm'] = True
            else:
                kwargs['load_vllm'] = False
        
        # Load appropriate model
        if is_cosyvoice2:
            tts_model = CosyVoice2(model_dir, **kwargs)
        else:
            # Remove CosyVoice2-specific parameters
            filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ['load_vllm']}
            tts_model = CosyVoice(model_dir, **filtered_kwargs)

        supported_voices = tts_model.list_available_spks()
        
        print("Model loaded successfully!")
        print(f"Available speakers: {supported_voices}")
        print(f"VLLM enabled: {kwargs.get('load_vllm', False)}")
        return True
        
    except Exception as e:
        print(f"Failed to load model: {e}")
        return False

def parse_args():
    """Parse command line arguments with environment variable fallbacks"""
    parser = argparse.ArgumentParser(description='CosyVoice OpenAI Compatible TTS API')
    parser.add_argument('--model', type=str, 
                       default=os.getenv('MODEL_DIR', 'pretrained_models/CosyVoice-300M-SFT'),
                       help='Path to model directory')
    parser.add_argument('--host', type=str, 
                       default=os.getenv('API_HOST', '0.0.0.0'),
                       help='Host address')
    parser.add_argument('--port', type=int, 
                       default=int(os.getenv('API_PORT', '9996')),
                       help='Port number')
    parser.add_argument('--load-jit', action='store_true',
                       default=os.getenv('LOAD_JIT', 'false').lower() == 'true',
                       help='Enable JIT compilation')
    parser.add_argument('--load-trt', action='store_true',
                       default=os.getenv('LOAD_TRT', 'false').lower() == 'true', 
                       help='Enable TensorRT optimization')
    parser.add_argument('--fp16', action='store_true',
                       default=os.getenv('FP16', 'false').lower() == 'true',
                       help='Enable FP16 precision')
    parser.add_argument('--load-vllm', action='store_true',
                       default=os.getenv('LOAD_VLLM', 'auto').lower() == 'true',
                       help='Explicitly enable VLLM acceleration (auto-detected for CosyVoice2)')
    parser.add_argument('--no-auto-vllm', action='store_true',
                       default=os.getenv('NO_AUTO_VLLM', 'false').lower() == 'true',
                       help='Disable automatic VLLM detection and acceleration')
    
    return parser.parse_args()

def main():
    """Main function"""
    args = parse_args()
    
    # Check FFmpeg availability
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: FFmpeg not found. Please install FFmpeg.")
        sys.exit(1)
    
    # Load model
    model_kwargs = {
        'load_jit': args.load_jit,
        # 'load_trt': args.load_trt, 
        'fp16': args.fp16,
    }
    
    # DEBUG: Check CUDA availability before loading model
    print(f"DEBUG: torch.cuda.is_available() = {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"DEBUG: torch.cuda.device_count() = {torch.cuda.device_count()}")
        try:
            print(f"DEBUG: torch.cuda.current_device() = {torch.cuda.current_device()}")
            print(f"DEBUG: torch.cuda.get_device_name(0) = {torch.cuda.get_device_name(0)}")
        except Exception as e:
            print(f"DEBUG: Could not get CUDA device details: {e}")
    # END DEBUG
    
    # Handle VLLM arguments
    if args.no_auto_vllm:
        # Explicitly disable VLLM
        model_kwargs['load_vllm'] = False
    elif args.load_vllm:
        # Explicitly enable VLLM
        model_kwargs['load_vllm'] = True
    # Otherwise, let auto-detection handle it (don't set load_vllm)
    
    # Ensure model is available
    if not ensure_model_available(args.model):
        print("Failed to download or find model. Exiting.")
        sys.exit(1)
    
    if not load_model(args.model, **model_kwargs):
        print("Failed to load model. Exiting.")
        sys.exit(1)
    
    # Create and run app
    app = create_app()
    
    print(f"\n🚀 CosyVoice OpenAI Compatible TTS API")
    print(f"📍 Server: http://{args.host}:{args.port}")
    print(f"📋 Health check: http://{args.host}:{args.port}/health")
    print(f"🎵 Supported formats: {SUPPORTED_FORMATS}")
    print(f"🎤 Supported voices: {supported_voices}")
    print(f"⚡ Model options: JIT={args.load_jit}, TRT={args.load_trt}, FP16={args.fp16},")
    print(f"🔊 Audio normalization: Enabled with default target LUFS: -16")
    
    # Show VLLM status
    vllm_status = model_kwargs.get('load_vllm', 'auto-detected')
    if vllm_status is True:
        print(f"🚀 VLLM: Enabled")
    elif vllm_status is False:
        print(f"❌ VLLM: Disabled")
    else:
        print(f"🔍 VLLM: Auto-detected for CosyVoice2 models")
    
    print("\n✅ Server ready!\n")
    
    try:
        from waitress import serve
        serve(app, host=args.host, port=args.port, threads=8)
    except ImportError:
        print("Waitress not found, using Flask dev server")
        app.run(host=args.host, port=args.port, threaded=True)

if __name__ == '__main__':
    main()

# Example usage:
"""
# Basic request
curl -X POST http://localhost:9996/v1/audio/speech \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "tts-1",
    "input": "Hello, this is a test of the OpenAI compatible TTS API.",
    "voice": "中文女",
    "response_format": "mp3",
    "speed": 1.0,
    "stream": true
  }' \\
  --output speech.mp3

# Non-streaming request (wait for full audio generation)
curl -X POST http://localhost:9996/v1/audio/speech \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "tts-1",
    "input": "Hello, this is a test of the OpenAI compatible TTS API.",
    "voice": "中文女",
    "response_format": "mp3",
    "speed": 1.0,
    "stream": false
  }' \\
  --output speech.mp3

# Python OpenAI client
from openai import OpenAI

client = OpenAI(
    api_key="dummy-key",
    base_url="http://localhost:9996/v1"
)

# Streaming response
with client.audio.speech.with_streaming_response.create(
    model="tts-1",
    voice="中文女", 
    input="Hello world! This is streaming audio.",
    response_format="mp3",
    stream=True
) as response:
    with open("speech.mp3", "wb") as f:
        for chunk in response.iter_bytes():
            f.write(chunk)

# Non-streaming response
response = client.audio.speech.create(
    model="tts-1",
    voice="中文女", 
    input="Hello world! This is non-streaming audio.",
    response_format="mp3",
    stream=False
)
with open("speech.mp3", "wb") as f:
    f.write(response.content)
"""