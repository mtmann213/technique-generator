#!/bin/bash

# 1. Enable X11 Forwarding (Allows Docker to show GUI windows)
xhost +local:docker > /dev/null

# 2. Identify the USRP USB path (Optional but helps visibility)
# Standard path is /dev/bus/usb

echo "--- Launching TechniqueMaker Container ---"
echo "--- Hardware: USRP Passthrough Enabled ---"
echo "--- GUI: X11 Forwarding Enabled ---"

# 3. Run the container
# --privileged: Required for direct hardware access
# -v /dev/bus/usb:/dev/bus/usb: Mounts the USB bus for UHD drivers
# -v /tmp/.X11-unix:/tmp/.X11-unix: For GUI forwarding
# -e DISPLAY=$DISPLAY: Tells Python where to draw windows
docker run -it --rm \
    --privileged \
    --net=host \
    -v /dev/bus/usb:/dev/bus/usb \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -e DISPLAY=$DISPLAY \
    -v "$(pwd)":/app \
    techniquemaker "$@"

# 4. Cleanup X11 permissions
xhost -local:docker > /dev/null
