#!/bin/bash
set -e

# Activate conda environment
source /opt/conda/etc/profile.d/conda.sh
conda activate ${VENV:-cosyvoice}

echo "=============================================="
echo "🚀 CosyVoice API Server with VLLM Support"
echo "=============================================="

# Print environment configuration
echo "📍 Configuration:"
echo "   Host: ${API_HOST:-0.0.0.0}"
echo "   Port: ${API_PORT:-9996}"
echo "   Model: ${MODEL_DIR:-pretrained_models/CosyVoice2-0.5B}"
echo "   JIT: ${LOAD_JIT:-false}"
echo "   TensorRT: ${LOAD_TRT:-false}"
echo "   FP16: ${FP16:-false}"
echo "   Flow Cache: ${USE_FLOW_CACHE:-false}"
echo "   VLLM: ${LOAD_VLLM:-auto}"
echo "   Auto VLLM: ${NO_AUTO_VLLM:-false}"

# Check if model directory exists
if [ ! -d "${MODEL_DIR:-pretrained_models/CosyVoice2-0.5B}" ]; then
    echo "⚠️  Warning: Model directory '${MODEL_DIR:-pretrained_models/CosyVoice2-0.5B}' not found!"
    echo "   Please ensure you have mounted the model directory correctly."
    echo "   Example: -v /path/to/your/pretrained_models:/workspace/CosyVoice/pretrained_models"
fi

# Build command line arguments
ARGS=""
ARGS="${ARGS} --host ${API_HOST:-0.0.0.0}"
ARGS="${ARGS} --port ${API_PORT:-9996}"
ARGS="${ARGS} --model ${MODEL_DIR:-pretrained_models/CosyVoice2-0.5B}"

# Add optional flags based on environment variables
if [ "${LOAD_JIT:-false}" = "true" ]; then
    ARGS="${ARGS} --load-jit"
fi

if [ "${LOAD_TRT:-false}" = "true" ]; then
    ARGS="${ARGS} --load-trt"  
fi

if [ "${FP16:-false}" = "true" ]; then
    ARGS="${ARGS} --fp16"
fi

if [ "${USE_FLOW_CACHE:-false}" = "true" ]; then
    ARGS="${ARGS} --use-flow-cache"
fi

if [ "${LOAD_VLLM:-auto}" = "true" ]; then
    ARGS="${ARGS} --load-vllm"
elif [ "${NO_AUTO_VLLM:-false}" = "true" ]; then
    ARGS="${ARGS} --no-auto-vllm"
fi

echo "=============================================="
echo "🎯 Starting API server with: python api/api.py${ARGS}"
echo "=============================================="

# Change to the CosyVoice directory
cd /workspace/CosyVoice

# Start the API server
exec python api/api.py ${ARGS}