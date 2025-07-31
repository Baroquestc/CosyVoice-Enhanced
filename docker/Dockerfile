FROM rapidsai/miniforge-cuda:cuda12.0.1-base-ubuntu22.04-py3.10

ARG VENV_NAME="cosyvoice"
ENV VENV=$VENV_NAME
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
SHELL ["/bin/bash", "--login", "-c"]

# Install system dependencies
RUN apt-get update -y --fix-missing && \
    apt-get install -y git build-essential curl wget ffmpeg unzip git git-lfs sox libsox-dev && \
    apt-get clean && \
    git lfs install

# Create cosyvoice environment
RUN conda create -y -n ${VENV} python=3.10
ENV CONDA_DEFAULT_ENV=${VENV}
ENV PATH /opt/conda/bin:/opt/conda/envs/${VENV}/bin:$PATH

WORKDIR /workspace

ENV PYTHONPATH="${PYTHONPATH}:/workspace/CosyVoice:/workspace/CosyVoice/third_party/Matcha-TTS"

# Clone CosyVoice repository
RUN git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git

# Install pynini first (required dependency)
RUN conda activate ${VENV} && conda install -y -c conda-forge pynini==2.1.5

# Install Python dependencies
RUN conda activate ${VENV} && cd CosyVoice && \
    pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com

# Copy local api files and utils to container
COPY api/ /workspace/CosyVoice/api/
COPY utils/ /workspace/CosyVoice/utils/

# Install API dependencies including VLLM
RUN conda activate ${VENV} && \
    pip install flask pyloudnorm waitress && \
    pip install vllm==0.9.0 -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com

WORKDIR /workspace/CosyVoice

# Expose API port
EXPOSE 9996

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9996/health || exit 1

# Default command to run API with conda environment
CMD ["conda", "run", "--no-capture-output", "-n", "cosyvoice", "python", "api/api.py", "--host", "0.0.0.0", "--port", "9996"]