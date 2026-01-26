# Use an official Python runtime as a parent image
# Python 3.10 is a safe bet for most ML libraries
ARG PYTHON_VERSION=3.10
FROM python:${PYTHON_VERSION}-slim as base

# Prevent apt dialogs & set UTF-8 locale
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.cache/huggingface \
    TRANSFORMERS_CACHE=/app/.cache/huggingface/transformers \
    HF_ENABLE_PARALLEL_LOADING=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
# build-essential: for compiling python packages
# git: for cloning repos if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
# We'll create this file next
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
ARG USE_GPU="false"
# If GPU build requested, user will later mount nvidia runtime. Torch install differs.
RUN if [ "$USE_GPU" = "true" ]; then \
            pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cu121; \
        fi && \
        pip install --no-cache-dir -r requirements.txt && \
        pip install --no-cache-dir "huggingface_hub[hf_xet]" && \
        # bitsandbytes is required for 8/4-bit quantization support
        pip install --no-cache-dir --upgrade bitsandbytes

# Copy the current directory contents into the container at /app
COPY . /app

# Create cache directories with proper permissions
RUN mkdir -p /app/.cache/huggingface && chmod -R 755 /app/.cache

# Define environment variable
# This mimics the Kaggle environment variable for competition rerun
# Uncomment this line for actual submission simulation where Gateway is external
# ENV KAGGLE_IS_COMPETITION_RERUN=true

# Add entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["test"]

# Example build:
#   docker build -t aimo:cpu .
#   docker build --build-arg USE_GPU=true -t aimo:gpu .
