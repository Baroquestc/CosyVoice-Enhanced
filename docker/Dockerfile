FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

ARG VENV_NAME="cosyvoice"
ENV VENV=$VENV_NAME
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
SHELL ["/bin/bash", "--login", "-c"]

RUN apt-get update -y --fix-missing && \
    apt-get install -y software-properties-common && \
    add-apt-repository universe && \
    apt-get update -y && \
    apt-get install -y git build-essential curl wget ffmpeg unzip git-lfs sox libsox-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    git lfs install

# ==================================================================
# conda install and conda forge channel as default
# ------------------------------------------------------------------
# Install miniforge
RUN wget --quiet https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O ~/miniforge.sh && \
    /bin/bash ~/miniforge.sh -b -p /opt/conda && \
    rm ~/miniforge.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo "source /opt/conda/etc/profile.d/conda.sh" >> /opt/nvidia/entrypoint.d/100.conda.sh && \
    echo "source /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate ${VENV}" >> /opt/nvidia/entrypoint.d/110.conda_default_env.sh && \
    echo "conda activate ${VENV}" >> $HOME/.bashrc

ENV PATH /opt/conda/bin:$PATH

RUN conda config --add channels conda-forge && \
    conda config --set channel_priority strict
# ------------------------------------------------------------------
# ~conda
# ==================================================================

RUN conda create -y -n ${VENV} python=3.10
ENV CONDA_DEFAULT_ENV=${VENV}
ENV PATH /opt/conda/bin:/opt/conda/envs/${VENV}/bin:$PATH

WORKDIR /workspace

ENV PYTHONPATH="${PYTHONPATH}:/workspace/CosyVoice:/workspace/CosyVoice/third_party/Matcha-TTS"

RUN git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git

RUN conda activate ${VENV} && conda install -y -c conda-forge pynini==2.1.5
RUN conda activate ${VENV} && cd CosyVoice && \
    pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com

# ==================================================================
# Install VLLM for acceleration (conditional based on environment)
# ------------------------------------------------------------------
# Install VLLM v0.9.0 for CosyVoice2 acceleration
RUN conda activate ${VENV} && \
    pip install vllm==0.9.0 -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com || \
    echo "VLLM installation failed, will fall back to standard mode"

# Install additional API dependencies
RUN conda activate ${VENV} && \
    pip install flask waitress pyloudnorm -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com
# ------------------------------------------------------------------
# ~VLLM
# ==================================================================

WORKDIR /workspace/CosyVoice

# Copy enhanced API and utilities
COPY api/ ./api/
COPY utils/ ./utils/

# Create necessary directories
RUN mkdir -p tmp logs pretrained_models

# Set up environment variables for API service
ENV API_HOST=0.0.0.0
ENV API_PORT=9997
ENV MODEL_DIR=pretrained_models/CosyVoice2-0.5B
ENV LOAD_JIT=false
ENV LOAD_TRT=false
ENV FP16=false
ENV USE_FLOW_CACHE=false
ENV LOAD_VLLM=auto
ENV NO_AUTO_VLLM=false

# Expose API port
EXPOSE 9997

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9997/health || exit 1

# Entry point script
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
