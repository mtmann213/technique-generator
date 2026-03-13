# TechniqueMaker: Tactical RF Suite Dockerfile
FROM ubuntu:22.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install System Dependencies (GNU Radio 3.10, UHD, Python, PyQt5)
RUN apt-get update && apt-get install -y \
    gnuradio \
    uhd-host \
    python3-numpy \
    python3-scipy \
    python3-pyqt5 \
    python3-sip-dev \
    python3-pmt \
    python3-pip \
    python3-soapysdr \
    soapysdr-tools \
    cmake \
    git \
    liborc-0.4-dev \
    libgmp-dev \
    libboost-all-dev \
    xterm \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# 2. Setup Workspace
WORKDIR /app
COPY . /app

# 3. Build and Install the OOT Module
RUN mkdir -p gr-techniquemaker/build && \
    cd gr-techniquemaker/build && \
    cmake .. && \
    make -j$(nproc) && \
    make install && \
    ldconfig

# 4. Set Environment Variables
ENV PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3/dist-packages:/usr/local/lib/python3.10/dist-packages
ENV DISPLAY=:0

# 5. Default command launches the help menu
ENTRYPOINT ["python3", "/app/TechniqueMaker.py"]
CMD ["--help"]
