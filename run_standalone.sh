#!/bin/bash
# run_standalone.sh: Tactical Hardware Passthrough for Predator Jammer
#
# Supports: Ettus USRP (USB), Signal Hound (USB), Sidekiq S4 (PCIe /dev node),
#           Sidekiq X4 (PCIe, SoapySDR discovery)
#
# Docker requires --privileged for PCIe device passthrough.
set -e

# Ensure we are in the repo directory
cd "$(dirname "$0")"

echo "============================================"
echo "  Predator Universal Hardware Container"
echo "  Device Detection & Launch"
echo "============================================"

# 1. Setup GUI access (X11 forwarding)
xhost +local:docker > /dev/null

# 2. Hardware Detection
OPTS=""

# --- Sidekiq S4: /dev node ---
if [ -c /dev/sidekiq0 ]; then
    echo "[+] Sidekiq S4 detected (PCIe /dev node)."
    OPTS="$OPTS --device /dev/sidekiq0:/dev/sidekiq0"
fi

# --- Sidekiq X4: PCIe via lspci ---
# The X4 uses a PCIe x4 interface. Check for Epiq vendor ID or known device.
# Also check for SoapySDR device availability.
SIDEKIQ_PCI=0
if command -v lspci &> /dev/null; then
    SIDEKIQ_PCI=$(lspci | grep -i -c -e "epiq" -e "sidekiq" || true)
fi
if [ "$SIDEKIQ_PCI" -gt 0 ]; then
    echo "[+] Sidekiq X4 detected via PCIe ($SIDEKIQ_PCI device(s))."
    echo "    Using --privileged for full device passthrough."
    OPTS="$OPTS --privileged"
elif command -v lspci &> /dev/null && [ "$SIDEKIQ_PCI" -eq 0 ]; then
    # Also check if SoapySDR can find any Sidekiq devices
    if command -v SoapySDRUtil &> /dev/null; then
        SIDEKIQ_SOAPY=$(SoapySDRUtil --probe="driver=sidekiq" 2>&1 | grep -c "Found" || true)
        if [ "$SIDEKIQ_SOAPY" -gt 0 ]; then
            echo "[+] Sidekiq device detected via SoapySDR."
            echo "    Using --privileged for device passthrough."
            OPTS="$OPTS --privileged"
        fi
    fi
fi

# --- USRP/Signal Hound (USB) ---
USRPS_FOUND=false
if [ -d /dev/bus/usb ]; then
    # Check for Ettus USRP devices
    if [ -d /dev/bus/usb ]; then
        if command -v uhd_find_devices &> /dev/null; then
            UHD_COUNT=$(uhd_find_devices 2>/dev/null | grep -c "B-Series\|X-Series\|E-Series" || true)
            if [ "$UHD_COUNT" -gt 0 ]; then
                echo "[+] USRP detected ($UHD_COUNT device(s)). Mapping USB bus..."
                USRPS_FOUND=true
            fi
        fi
    fi

    # Check for Signal Hound devices
    if lsusb | grep -q -i "signal.hound\|1d52" 2>/dev/null; then
        echo "[+] Signal Hound device detected. Mapping USB bus..."
        USRPS_FOUND=true
    fi

    # Map the entire USB bus for SDR peripherals
    if [ "$USRPS_FOUND" = true ] && [ -d /dev/bus/usb ]; then
        OPTS="$OPTS -v /dev/bus/usb:/dev/bus/usb"
    fi
fi

# --- Fallback: If no devices detected but we still need hardware access ---
if [ -z "$OPTS" ]; then
    echo "[!] No SDR devices detected at startup."
    echo "    USB bus will still be mapped for hot-plug support."
    OPTS="-v /dev/bus/usb:/dev/bus/usb"
fi

# 3. Create Local Driver Staging if missing
mkdir -p local_drivers

# 4. Check for Docker image
IMAGE="predator-jammer:latest"
if ! docker image inspect "$IMAGE" &> /dev/null; then
    echo "[!] Docker image '$IMAGE' not found."
    echo "    Load the air-gapped image with:"
    echo "      gunzip -c predator_image.tar.gz | docker load"
    echo ""
    echo "    Or build locally with:"
    echo "      docker build -t predator-jammer:latest ."
    exit 1
fi

# 5. Launch Container
echo ""
echo "[*] Launching Predator Container..."
echo "    Image: $IMAGE"
echo "    Devices: $OPTS"
echo ""
docker run -it --rm \
    --privileged \
    --net=host \
    --env="DISPLAY=$DISPLAY" \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    --volume="$(pwd)/config:/app/config" \
    --volume="$(pwd)/local_drivers:/usr/local/lib/predator_drivers" \
    --volume="$(pwd)/recordings:/app/recordings" \
    $OPTS \
    "$IMAGE" \
    predator

# 6. Cleanup X11 permissions
echo ""
echo "[*] Container exited. Cleaning up X11 permissions..."
xhost -local:docker > /dev/null
echo "[*] Done."
