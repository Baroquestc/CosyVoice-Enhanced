# --- Base Image ---
FROM nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04

# --- Environment Setup ---
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
SHELL ["/bin/bash", "--login", "-c"]

# --- System Dependencies ---
# Install essential packages for building Python libraries and handling files.
RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get update -o Acquire::Check-Valid-Until=false -y --fix-missing && \
    apt-get install -y git build-essential curl wget ffmpeg unzip git-lfs sox libsox-dev && \
    apt-get clean && \
    git lfs install

# --- Conda Installation ---
# Install Miniforge for a minimal conda environment.
RUN wget --quiet https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O ~/miniforge.sh && \
    /bin/bash ~/miniforge.sh -b -p /opt/conda && \
    rm ~/miniforge.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo "source /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc

ENV PATH /opt/conda/bin:$PATH

# Configure conda channels for strict priority.
RUN conda config --add channels conda-forge && \
    conda config --set channel_priority strict

# --- Python Environment Setup ---
# Create a single, clean environment for the application.
ARG VLLM_ENV_NAME="cosyvoice_vllm"
RUN conda create -y -n ${VLLM_ENV_NAME} python=3.10
ENV PATH /opt/conda/envs/${VLLM_ENV_NAME}/bin:$PATH

# --- Project Checkout ---
WORKDIR /workspace
ENV PYTHONPATH="${PYTHONPATH}:/workspace/CosyVoice:/workspace/CosyVoice/third_party/Matcha-TTS"
RUN git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git

# --- Python Dependencies Installation ---
# This is the definitive fix for the numpy version conflict.
# 1. Install numpy<2.0 via conda.
# 2. Create a pip `constraints.txt` file to enforce this version.
# 3. Use the `-c constraints.txt` flag during all pip installs to ensure the rule is followed.
# 4. Install waitress for production deployment.
RUN conda run -n ${VLLM_ENV_NAME} bash -c "\
    conda install -y -c conda-forge pynini==2.1.5 'numpy<2.0' && \
    cd /workspace/CosyVoice && \
    echo 'numpy<2.0' > constraints.txt && \
    grep -v '^numpy' requirements.txt | grep -v '^transformers' | grep -v '^vllm' > requirements_filtered.txt && \
    pip install -r requirements_filtered.txt -c constraints.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com && \
    pip install pyloudnorm flask waitress transformers==4.53.3 vllm==0.9.0 -c constraints.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host=mirrors.aliyun.com \
    "

# --- Application Setup ---
WORKDIR /workspace/CosyVoice

# Copy local API and utility files into the container.
COPY api/ /workspace/CosyVoice/api/
COPY utils/ /workspace/CosyVoice/utils/

# Expose the API port.
EXPOSE 9996

# Health check to ensure the server starts correctly.
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9996/health || exit 1

# --- Run Command ---
# Default command to start the API server using the correct conda environment.
CMD ["sh", "-c", "conda run --no-capture-output -n cosyvoice_vllm python api/api.py --host 0.0.0.0 --port 9996 --model ${MODEL_DIR:-pretrained_models/CosyVoice2-0.5B} ${LOAD_JIT:+--load-jit} ${LOAD_TRT:+--load-trt} ${FP16:+--fp16} ${USE_FLOW_CACHE:+--use-flow-cache} ${LOAD_VLLM:+--load-vllm} ${NO_AUTO_VLLM:+--no-auto-vllm}"]
