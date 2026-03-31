#!/bin/bash
# run_standalone.sh: Tactical Hardware Passthrough for Predator Jammer

# 1. Setup GUI access
xhost +local:docker > /dev/null

# 2. Identify Hardware Passthroughs
OPTS=""

# Check for Sidekiq S4 (PCIe /dev nodes)
if [ -c /dev/sidekiq0 ]; then
    echo "[+] Sidekiq S4 detected. Mapping PCIe interface..."
    OPTS="$OPTS --device /dev/sidekiq0:/dev/sidekiq0"
fi

# Check for USRP/Signal Hound (USB)
# We map the entire USB bus to ensure seamless hot-plugging
if [ -d /dev/bus/usb ]; then
    echo "[+] USB Bus detected. Mapping SDR peripherals..."
    OPTS="$OPTS -v /dev/bus/usb:/dev/bus/usb"
fi

# 3. Create Local Driver Staging if missing
mkdir -p local_drivers

# 4. Launch Container
echo "[*] Launching Predator Universal Hardware Container..."
docker run -it --rm \
    --privileged \
    --net=host \
    --env="DISPLAY=$DISPLAY" \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    --volume="$(pwd)/config:/app/config" \
    --volume="$(pwd)/local_drivers:/usr/local/lib/predator_drivers" \
    --volume="$(pwd)/recordings:/app/recordings" \
    $OPTS \
    predator-jammer:latest predator
