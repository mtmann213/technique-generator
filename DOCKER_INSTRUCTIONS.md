# TechniqueMaker: Docker & Tactical Offline Deployment Guide

This guide provides the complete procedure for deploying the TechniqueMaker suite on secure, non-networked (air-gapped) devices.

---

## 🏗️ 1. Prepare the Portable Environment
*Perform these steps on a machine WITH internet access.*

1.  **Clone the Repo:** Ensure you have the latest code.
2.  **Build the Image:**
    ```bash
    docker build -t techniquemaker .
    ```
3.  **Generate the Offline Bundle:**
    This script exports the 2GB+ environment into a single `.tar` file.
    ```bash
    chmod +x bundle_offline.sh
    ./bundle_offline.sh
    ```
4.  **Transfer to USB:**
    Copy the following files to your USB drive:
    *   `techniquemaker_offline_bundle.tar` (The Environment)
    *   `run_docker.sh` (The Launcher)
    *   The entire `TechniqueMaker/` source folder (For live code updates)

---

## 🚀 2. Deploy on the Offline Device
*Perform these steps on the target machine WITHOUT internet access.*

### Prerequisites
The target machine must have the Docker Engine installed. If it does not, you must side-load the Docker `.deb` or `.rpm` packages for your specific OS first.

### Step A: Load the Environment
1.  Plug in the USB drive and navigate to its folder.
2.  Import the image:
    ```bash
    docker load < techniquemaker_offline_bundle.tar
    ```
3.  Verify the image is present:
    ```bash
    docker images
    # You should see 'techniquemaker' in the list.
    ```

### Step B: Launch the Console
The `run_docker.sh` script automatically detects your USRP and sets up GUI forwarding.
```bash
chmod +x run_docker.sh
./run_docker.sh predator
```

---

## 🔄 3. Updating Code (The "Surgical" Method)
One major advantage of this setup is that the **code is separate from the environment**.

*   The Docker image contains GNU Radio, UHD drivers, and dependencies.
*   The `run_docker.sh` script "mounts" your local folder into the container.
*   **To update the app:** You do NOT need to re-transfer the 2GB `.tar` file. Simply copy the updated `.py` files from the repo to your USB stick and overwrite the ones on the offline machine. The container will use the new code instantly the next time you run it.

---

## 🛠️ Troubleshooting
*   **USB/USRP Not Found:**
    1. Run `lsusb` on the host to ensure the USRP is visible.
    2. Run the script with `sudo ./run_docker.sh predator` to bypass permission locks.
*   **X11 / Display Errors:**
    Docker needs permission to draw on your screen. On the host machine, run:
    ```bash
    xhost +local:docker
    ```
*   **Performance:**
    Ensure the host machine has at least 4GB of RAM, as GNU Radio and the Predator FFT processing are memory-intensive.
