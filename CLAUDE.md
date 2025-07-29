# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CosyVoice is a multilingual text-to-speech (TTS) system with multiple model versions:
- **CosyVoice 1.0**: Base 300M parameter model with SFT and Instruct variants
- **CosyVoice 2.0**: 0.5B parameter streaming model with improved accuracy and stability

The system supports Chinese, English, Japanese, Korean, and Chinese dialects with zero-shot voice cloning, cross-lingual synthesis, and streaming inference capabilities.

## Core Architecture

### Main Components
- **`cosyvoice/cli/`**: High-level API classes (`CosyVoice`, `CosyVoice2`) for inference
- **`cosyvoice/llm/`**: Large language model components for text processing
- **`cosyvoice/flow/`**: Flow matching models for acoustic feature generation
- **`cosyvoice/hifigan/`**: Neural vocoder for audio synthesis
- **`cosyvoice/transformer/`**: Transformer-based encoder/decoder implementations
- **`cosyvoice/tokenizer/`**: Text and speech tokenization utilities
- **`cosyvoice/dataset/`**: Data loading and preprocessing pipeline
- **`cosyvoice/utils/`**: Common utilities, file operations, and training helpers

### Model Loading Pattern
Models are loaded via the CLI classes which automatically handle:
- Model type detection (CosyVoice vs CosyVoice2)
- Configuration loading from `cosyvoice.yaml`
- Frontend initialization (tokenizer, feature extractor, speaker embedding)
- Device placement and optimization (JIT, TensorRT, FP16)

## Development Commands

### Environment Setup
```bash
conda create -n cosyvoice -y python=3.10
conda activate cosyvoice
pip install -r requirements.txt
```

### Model Download
Models must be downloaded before use:
```python
from modelscope import snapshot_download
snapshot_download('iic/CosyVoice2-0.5B', local_dir='pretrained_models/CosyVoice2-0.5B')
snapshot_download('iic/CosyVoice-300M', local_dir='pretrained_models/CosyVoice-300M')
```

### Running Inference
- **Web UI**: `python api/webui.py --port 50000 --model_dir pretrained_models/CosyVoice-300M`
- **CLI Inference**: `python cosyvoice/bin/inference.py`
- **API Server**: 
  - Main API: `python api/api.py`
  - FastAPI: `cd runtime/python/fastapi && python server.py`
  - gRPC: `cd runtime/python/grpc && python server.py`

### Training Pipeline
Training follows a multi-stage process defined in `examples/libritts/cosyvoice/run.sh`:
1. Data preparation and preprocessing
2. Speaker embedding extraction (campplus)
3. Speech token extraction
4. Parquet format conversion
5. Multi-component training (llm, flow, hifigan)
6. Model averaging and export

Training command:
```bash
cd examples/libritts/cosyvoice
bash run.sh
```

### Model Export
- **JIT Export**: `python cosyvoice/bin/export_jit.py --model_dir <model_dir>`
- **ONNX Export**: `python cosyvoice/bin/export_onnx.py --model_dir <model_dir>`

## Key Usage Patterns

### Model Initialization
```python
from cosyvoice.cli.cosyvoice import CosyVoice, CosyVoice2

# CosyVoice2 (recommended)
cosyvoice = CosyVoice2('pretrained_models/CosyVoice2-0.5B')

# CosyVoice 1.0
cosyvoice = CosyVoice('pretrained_models/CosyVoice-300M')
```

### Inference Modes
- **Zero-shot**: Clone voice from prompt audio
- **SFT**: Use predefined speaker voices
- **Cross-lingual**: Synthesize in different language than prompt
- **Instruct**: Control synthesis with natural language instructions
- **Streaming**: Real-time synthesis with low latency

### Configuration Files
- Model configs: `<model_dir>/cosyvoice.yaml`
- Training configs: `examples/*/conf/cosyvoice*.yaml`
- DeepSpeed configs: `examples/*/conf/ds_stage2.json`

## File Organization Conventions

- **Bin scripts** (`cosyvoice/bin/`): Executable training and inference scripts
- **CLI modules** (`cosyvoice/cli/`): High-level user-facing APIs
- **Core modules**: Organized by model component (llm, flow, hifigan, transformer)
- **Examples**: Complete training recipes in `examples/<dataset>/<model>/`
- **Runtime**: Deployment configurations in `runtime/python/`
- **Tools**: Utility scripts in `tools/` for data processing

## Model Compatibility

Always check model type before initialization:
- Use `get_model_type()` from `cosyvoice.utils.class_utils`
- CosyVoice2 models require `CosyVoice2` class
- CosyVoice 1.0 models require `CosyVoice` class
- Model directories contain identifying `cosyvoice.yaml` configuration

## Dependencies and Hardware

- **CUDA**: Required for GPU acceleration, training, and TensorRT
- **sox**: Audio processing dependency (install via package manager)
- **ffmpeg**: Audio codec support (included in project structure)
- **vllm**: Optional for CosyVoice2 high-performance inference (v0.9.0)
- **deepspeed**: Linux-only training acceleration
- **tensorrt**: Linux-only inference optimization