# TechniqueMaker: Universal Tactical RF Suite (Standalone)
FROM ubuntu:22.04

# Prevent interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install System Dependencies (GNU Radio 3.10, UHD, SoapySDR, Python, PyQt5)
RUN apt-get update && apt-get install -y \
    gnuradio \
    uhd-host \
    soapysdr-tools \
    libsoapysdr-dev \
    python3-soapysdr \
    python3-numpy \
    python3-scipy \
    python3-pyqt5 \
    python3-pyqt5.sip \
    python3-pip \
    cmake \
    git \
    swig \
    liborc-0.4-dev \
    libgmp-dev \
    libboost-all-dev \
    xterm \
    sudo \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Local Driver Staging (For proprietary SDKs)
# Place libvsg60.so, libbb60.so, or sidekiq_sdk.deb in local_drivers/ before building
RUN mkdir -p /usr/local/lib/predator_drivers
COPY local_drivers/ /usr/local/lib/predator_drivers/
RUN ldconfig

# 3. Setup Workspace
WORKDIR /app
COPY . /app

# 4. Build and Install the OOT Module
RUN mkdir -p gr-techniquemaker/build && \
    cd gr-techniquemaker/build && \
    cmake .. && \
    make -j$(nproc) && \
    make install && \
    ldconfig

# 5. Pre-cache Python Dependencies for Offline Use
RUN pip3 install mako six

# 6. Set Environment Variables
ENV PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3/dist-packages:/usr/local/lib/python3.10/dist-packages
ENV DISPLAY=:0
ENV LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/predator_drivers

# 7. Default command launches the help menu
ENTRYPOINT ["python3", "/app/TechniqueMaker.py"]
CMD ["--help"]
