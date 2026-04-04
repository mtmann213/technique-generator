#!/usr/bin/env bash
# build_on_target.sh - Helper for building Sidekiq-SNG on air-gapped systems

echo "--- Building Sidekiq-SNG [DIRECT LINK MODE] ---"
cd "$(dirname "$0")"

# 1. Find the EXACT path to the library file (e.g., /lib/x86_64-linux-gnu/libSoapySDR.so.0.8)
FULL_SOAPY_PATH=$(ldconfig -p | grep libSoapySDR | head -n 1 | awk '{print $NF}')

if [ -n "$FULL_SOAPY_PATH" ]; then
    echo "[PASS] Found library file: $FULL_SOAPY_PATH"
    
    # 2. Compile by passing the full path to the .so file instead of -lSoapySDR
    # This avoids the "cannot find -lSoapySDR" error when the .so symlink is missing.
    echo "Running: g++ -O3 -march=native -std=c++17 -I./include -DUSE_SOAPY -o sng main.cpp WaveformEngine.cpp $FULL_SOAPY_PATH"
    
    g++ -O3 -march=native -std=c++17 -I./include -DUSE_SOAPY -o sng main.cpp WaveformEngine.cpp "$FULL_SOAPY_PATH"
    
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] sng built with SoapySDR streaming support."
        echo "Run with: ./sng --tech <tech> --stream"
    else
        echo "[FAIL] Compilation failed."
    fi
else
    echo "[ERROR] libSoapySDR not found in ldconfig. Cannot build with streaming support."
    echo "Attempting standard file-only build..."
    make
fi
