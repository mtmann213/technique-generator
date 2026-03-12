# TechniqueMaker: Docker & Offline Deployment Guide

This guide explains how to use Docker to run the TechniqueMaker suite on any Linux machine with zero manual dependency installation, including support for SDR hardware and PyQt5 GUIs.

---

## 🏗️ 1. Initial Setup
Ensure Docker is installed on your host machine.

### Build the Image
Run this once to create the environment:
```bash
docker build -t techniquemaker .
```

---

## 🚀 2. Running the Suite
The `run_docker.sh` helper handles USB hardware passthrough (for the USRP) and X11 GUI forwarding.

### Launch Predator Console
```bash
chmod +x run_docker.sh
./run_docker.sh predator
```

### Launch Standalone GUI
```bash
./run_docker.sh gui
```

### Run Batch Generator
```bash
./run_docker.sh batch --args --count 10
```

---

## 📡 3. Air-Gap / No-Internet Deployment
Use this method to bring the entire suite onto a secure, non-networked device.

### On a machine WITH internet:
1.  Run the bundle script:
    ```bash
    chmod +x bundle_offline.sh
    ./bundle_offline.sh
    ```
2.  Copy the resulting `techniquemaker_offline_bundle.tar` and the `run_docker.sh` script to a USB drive.

### On the target machine WITHOUT internet:
1.  Plug in the USB drive.
2.  Load the environment:
    ```bash
    docker load < techniquemaker_offline_bundle.tar
    ```
3.  Launch the Predator console:
    ```bash
    ./run_docker.sh predator
    ```

---

## 🛠️ Troubleshooting
*   **Permission Denied (USB):** If Docker cannot see your USRP, ensure your user is in the `plugdev` group on the host machine, or run the script with `sudo`.
*   **GUI Not Showing:** If you get an X11 error, ensure you are logged into a desktop session (X11/Wayland) and that `xhost` is installed.
