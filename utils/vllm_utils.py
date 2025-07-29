"""
VLLM utilities for automatic detection and integration with CosyVoice2
"""
import sys
import os
import importlib.util
import logging
from typing import Optional, Tuple


def check_vllm_availability() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Check if vllm is available and compatible for CosyVoice2 usage.
    
    Returns:
        Tuple of (is_available, version, error_message)
    """
    try:
        # Try to import vllm
        import vllm
        
        # Check version compatibility (v0.9.0 is required according to README)
        version = getattr(vllm, '__version__', 'unknown')
        
        # Parse version to check compatibility
        if version != 'unknown':
            try:
                # Extract major.minor version
                version_parts = version.split('.')
                major = int(version_parts[0])
                minor = int(version_parts[1]) if len(version_parts) > 1 else 0
                
                # vllm v0.9.0+ is required
                if major == 0 and minor >= 9:
                    return True, version, None
                else:
                    return False, version, f"vllm version {version} is not compatible. v0.9.0+ required."
            except (ValueError, IndexError):
                # If we can't parse version, assume it might work
                return True, version, None
        
        return True, version, None
        
    except ImportError as e:
        return False, None, f"vllm not installed: {str(e)}"
    except Exception as e:
        return False, None, f"Error checking vllm: {str(e)}"


def register_cosyvoice2_vllm() -> bool:
    """
    Register CosyVoice2 model with VLLM if available.
    
    Returns:
        True if successfully registered, False otherwise
    """
    try:
        is_available, version, error = check_vllm_availability()
        if not is_available:
            return False
            
        # Import and register CosyVoice2 for VLLM
        from vllm import ModelRegistry
        from cosyvoice.vllm.cosyvoice2 import CosyVoice2ForCausalLM
        
        # Register the model
        ModelRegistry.register_model("CosyVoice2ForCausalLM", CosyVoice2ForCausalLM)
        
        return True
        
    except ImportError:
        # cosyvoice.vllm module not available
        return False
    except Exception as e:
        logging.warning(f"Failed to register CosyVoice2 with VLLM: {e}")
        return False


def should_enable_vllm_for_model(model_dir: str) -> bool:
    """
    Determine if VLLM should be enabled for a given model directory.
    
    Args:
        model_dir: Path to the model directory
        
    Returns:
        True if VLLM should be enabled, False otherwise
    """
    # Check if vllm is available
    is_available, _, _ = check_vllm_availability()
    if not is_available:
        return False
    
    # Check if it's a CosyVoice2 model
    if 'CosyVoice2' in model_dir or os.path.exists(os.path.join(model_dir, 'cosyvoice2.yaml')):
        return True
    
    return False


def get_vllm_status() -> dict:
    """
    Get comprehensive VLLM status information.
    
    Returns:
        Dictionary with VLLM status information
    """
    is_available, version, error = check_vllm_availability()
    
    status = {
        'available': is_available,
        'version': version,
        'error': error,
        'registered': False
    }
    
    if is_available:
        # Check if CosyVoice2 can be registered
        status['registered'] = register_cosyvoice2_vllm()
    
    return status


def log_vllm_status():
    """Log VLLM availability status."""
    status = get_vllm_status()
    
    if status['available']:
        if status['registered']:
            print(f"✅ VLLM v{status['version']} available and CosyVoice2 registered for acceleration")
        else:
            print(f"⚠️  VLLM v{status['version']} available but CosyVoice2 registration failed")
    else:
        print(f"❌ VLLM not available: {status['error']}")
        print("💡 To enable VLLM acceleration for CosyVoice2:")
        print("   conda create -n cosyvoice_vllm --clone cosyvoice")
        print("   conda activate cosyvoice_vllm") 
        print("   pip install vllm==v0.9.0")