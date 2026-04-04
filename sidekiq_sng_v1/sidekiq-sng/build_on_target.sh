#!/usr/bin/env bash
# build_on_target.sh - Helper for building Sidekiq-SNG on air-gapped systems

echo "--- Building Sidekiq-SNG with SoapySDR Support ---"
cd "$(dirname "$0")"

# Check for SoapySDR
if ldconfig -p | grep -q "libSoapySDR"; then
    echo "[PASS] Found libSoapySDR."
else
    echo "[WARN] libSoapySDR not found in ldconfig. If it is in a custom path, run: 'export LD_LIBRARY_PATH=/path/to/lib:$LD_LIBRARY_PATH'"
fi

# Attempt build
echo "Running: make soapy"
make soapy

if [ $? -eq 0 ]; then
    echo "[SUCCESS] sng built with SoapySDR streaming support."
    echo "Run with: ./sng --tech <tech> --stream"
else
    echo "[FAIL] Build failed. Ensure g++ and libsoapysdr-dev are installed."
    echo "Falling back to standard build (file output only)..."
    make
fi
