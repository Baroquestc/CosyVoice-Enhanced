# CosyVoice API Docker Deployment Guide

This guide provides comprehensive instructions for deploying the CosyVoice API service with VLLM acceleration support using Docker.

## 🚀 Quick Start

### Prerequisites

1. **Docker & Docker Compose**: Install Docker and Docker Compose
2. **NVIDIA Docker Runtime**: For GPU support
   ```bash
   # Install nvidia-container-toolkit
   curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
   curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
     sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
     sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
   sudo apt-get update
   sudo apt-get install -y nvidia-container-toolkit
   sudo systemctl restart docker
   ```
3. **GPU**: NVIDIA GPU with CUDA support (recommended for optimal performance)

### Step 1: Download Models

Download the required models to your local `pretrained_models` directory:

```python
# Run this script to download models
from modelscope import snapshot_download

# Download CosyVoice2 (recommended for VLLM acceleration)
snapshot_download('iic/CosyVoice2-0.5B', local_dir='pretrained_models/CosyVoice2-0.5B')

# Optional: Download other models
snapshot_download('iic/CosyVoice-300M', local_dir='pretrained_models/CosyVoice-300M')
snapshot_download('iic/CosyVoice-300M-SFT', local_dir='pretrained_models/CosyVoice-300M-SFT')
snapshot_download('iic/CosyVoice-300M-Instruct', local_dir='pretrained_models/CosyVoice-300M-Instruct')
```

### Step 2: Configure Environment

1. Copy the environment template:
   ```bash
   cd docker
   cp .env.example .env
   ```

2. Edit `.env` file with your configuration:
   ```bash
   # Update the models path to your actual directory
   MODELS_PATH=../pretrained_models
   
   # Choose your model
   MODEL_DIR=pretrained_models/CosyVoice2-0.5B
   
   # Enable performance options if needed
   FP16=true
   USE_FLOW_CACHE=true
   ```

### Step 3: Deploy

1. **Build and start the service:**
   ```bash
   cd docker
   docker-compose up -d --build
   ```

2. **Check service status:**
   ```bash
   docker-compose ps
   docker-compose logs -f cosyvoice-api
   ```

3. **Test the API:**
   ```bash
   curl http://localhost:9997/health
   ```

## 📋 Configuration Reference

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `9997` | API server port |
| `MODEL_DIR` | `pretrained_models/CosyVoice2-0.5B` | Model directory path |
| `MODELS_PATH` | `../pretrained_models` | Host path to models |
| `LOAD_JIT` | `false` | Enable JIT compilation |
| `LOAD_TRT` | `false` | Enable TensorRT (Linux only) |
| `FP16` | `false` | Enable FP16 precision |
| `USE_FLOW_CACHE` | `false` | Enable flow cache (CosyVoice2) |
| `LOAD_VLLM` | `auto` | VLLM mode: auto/true/false |
| `NO_AUTO_VLLM` | `false` | Disable auto VLLM detection |

### Volume Mappings

| Host Path | Container Path | Description |
|-----------|----------------|-------------|
| `../pretrained_models` | `/workspace/CosyVoice/pretrained_models` | Model files (read-only) |
| `../logs` | `/workspace/CosyVoice/logs` | Log files |
| `../tmp` | `/workspace/CosyVoice/tmp` | Temporary files |

## 🎯 Usage Examples

### Basic API Call

```bash
curl -X POST http://localhost:9997/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "tts-1",
    "input": "Hello, this is a test of the CosyVoice API with VLLM acceleration.",
    "voice": "中文女",
    "response_format": "mp3",
    "speed": 1.0
  }' \
  --output speech.mp3
```

### Python OpenAI Client

```python
from openai import OpenAI

client = OpenAI(
    api_key="dummy-key",
    base_url="http://localhost:9997/v1"
)

response = client.audio.speech.create(
    model="tts-1",
    voice="中文女",
    input="你好，这是CosyVoice API的测试。",
    response_format="mp3"
)

with open("speech.mp3", "wb") as f:
    f.write(response.content)
```

## 🔧 Performance Optimization

### For High-Performance Deployment

```bash
# In .env file
FP16=true
USE_FLOW_CACHE=true
LOAD_VLLM=true
LOAD_JIT=true
```

### For Memory-Constrained Environments

```bash
# In .env file
FP16=true
LOAD_VLLM=false
USE_FLOW_CACHE=false
```

### Multi-GPU Setup

```bash
# Use specific GPUs
CUDA_VISIBLE_DEVICES=0,1
```

## 🐛 Troubleshooting

### Common Issues

1. **VLLM Installation Failed**
   - Check GPU compatibility
   - Ensure CUDA version matches requirements
   - Set `LOAD_VLLM=false` to disable

2. **Model Not Found**
   - Verify `MODELS_PATH` points to correct directory
   - Ensure models are downloaded correctly
   - Check file permissions

3. **GPU Not Detected**
   - Install nvidia-container-toolkit
   - Restart Docker daemon
   - Check `nvidia-smi` works

4. **Out of Memory**
   - Enable FP16: `FP16=true`
   - Use smaller model
   - Reduce batch size

### Checking Logs

```bash
# View container logs
docker-compose logs -f cosyvoice-api

# Check container status
docker-compose ps

# Access container shell
docker-compose exec cosyvoice-api bash
```

### Health Check

```bash
# Check API health
curl http://localhost:9997/health

# Expected response:
# {"status": "healthy", "model_loaded": true}
```

## 🔄 Maintenance

### Update Models

1. Download new models to `pretrained_models/`
2. Update `MODEL_DIR` in `.env`
3. Restart service: `docker-compose restart`

### Update Service

```bash
# Pull latest changes
git pull

# Rebuild and restart
cd docker
docker-compose down
docker-compose up -d --build
```

### Backup Configuration

```bash
# Backup your configuration
cd docker
cp .env .env.backup
cp docker-compose.yml docker-compose.yml.backup
```

## 📊 Monitoring

### View Resource Usage

```bash
# Container stats
docker stats cosyvoice-api-server

# GPU usage
nvidia-smi
```

### Log Management

Logs are automatically rotated (max 10MB, 3 files). To view:

```bash
# Real-time logs (from docker directory)
cd docker
docker-compose logs -f

# Specific time range
docker-compose logs --since="1h" --until="30m"
```

## 🚀 Production Deployment

For production environments, consider:

1. **Use external volumes for persistence**
2. **Set up proper monitoring (Prometheus/Grafana)**
3. **Configure log aggregation (ELK stack)**
4. **Set up load balancing for multiple instances**
5. **Use secrets management for sensitive data**
6. **Regular backup of models and configurations**

Example production docker-compose:

```yaml
# Use external networks
networks:
  cosyvoice-network:
    external: true

# Use named volumes
volumes:
  cosyvoice-models:
    external: true
  cosyvoice-logs:
    external: true
```