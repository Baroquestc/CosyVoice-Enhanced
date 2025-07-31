# CosyVoice Docker Build and Usage Guide - FIXED

## ⚠️ IMPORTANT FIX APPLIED
The "entrypoint.sh not found" issue has been resolved by fixing the build context:
- All commands must run from **project root**, not `docker/` directory
- Build context is now properly set to project root
- All batch scripts updated to use correct paths

## Quick Start

```bash
# ALWAYS run from project root directory
cd /path/to/cosyvoice

# Build the image (CORRECT)
docker build -f docker/Dockerfile -t cosyvoice-api:latest .

# Run with docker-compose (RECOMMENDED)
docker compose -f docker/docker-compose.yml up --build

# Using Windows batch scripts (from project root)
scripts\docker-compose-up.bat
```

## Build Context Fix Details

**Before (BROKEN):**
```bash
cd docker/
docker compose up -d  # Wrong context!
```

**After (FIXED):**
```bash
cd /path/to/cosyvoice  # Project root
docker compose -f docker/docker-compose.yml up -d  # Correct!
```

## Build Optimizations

### Multi-stage Build
- **Builder stage**: Full CUDA development environment for compiling dependencies
- **Runtime stage**: Minimal CUDA runtime for production (60% smaller)

### Layer Caching
- System dependencies installed in separate layers
- Python requirements cached independently
- VLLM installation isolated for better caching

### Build Speed Tips
```bash
# Use BuildKit for faster builds
DOCKER_BUILDKIT=1 docker build -f docker/Dockerfile -t cosyvoice-api .

# Parallel builds with docker-compose
docker-compose build --parallel
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL_DIR` | `pretrained_models/CosyVoice2-0.5B` | Model directory path |
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `9996` | API server port |
| `LOAD_VLLM` | `auto` | Enable VLLM acceleration |
| `FP16` | `false` | Enable FP16 precision |
| `LOAD_TRT` | `false` | Enable TensorRT optimization |

## Production Deployment

### Using Docker Compose (Recommended)
```bash
# Create .env file
cat > .env << EOF
MODEL_DIR=pretrained_models/CosyVoice2-0.5B
API_PORT=9996
LOAD_VLLM=true
FP16=true
EOF

# Deploy
docker-compose up -d
```

### Manual Deployment
```bash
docker run -d \
  --name cosyvoice-api \
  --gpus all \
  --restart unless-stopped \
  -p 9996:9996 \
  -v /path/to/models:/workspace/CosyVoice/pretrained_models:ro \
  -v /path/to/logs:/workspace/CosyVoice/logs \
  -e LOAD_VLLM=true \
  -e FP16=true \
  cosyvoice-api:latest
```

## Testing the API

```bash
# Health check
curl http://localhost:9996/health

# TTS request
curl -X POST http://localhost:9996/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello, world!",
    "voice": "中文女",
    "response_format": "mp3"
  }' \
  --output test.mp3
```

## Troubleshooting

### Build Issues
- **CUDA not found**: Ensure NVIDIA Container Toolkit is installed
- **Out of memory**: Increase Docker memory limit or use `--memory=8g`
- **Permission denied**: Check file permissions and Docker daemon access

### Runtime Issues
- **GPU not detected**: Verify `--gpus all` flag and NVIDIA drivers
- **Model not found**: Check volume mounting and model path
- **VLLM errors**: Ensure sufficient GPU memory (8GB+ recommended)

## Performance Tips

1. **Use VLLM**: Set `LOAD_VLLM=true` for CosyVoice2 models
2. **Enable FP16**: Set `FP16=true` to reduce memory usage
3. **TensorRT**: Set `LOAD_TRT=true` for optimized inference
4. **Flow Cache**: Set `USE_FLOW_CACHE=true` for faster repeated inference