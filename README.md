# TechniqueMaker: Advanced Reactive Interdiction Suite

TechniqueMaker is a high-performance SDR platform designed for protocol-aware RF interdiction. It provides a real-time C++/Python framework for detecting, tracking, and disrupting complex digital waveforms with sub-millisecond precision.

---

## 🦅 Tactical Capabilities

### 1. Multi-Hardware Interdiction
- **USRP (UHD):** Native support for B205-mini, B210, and N-series devices.
- **Signal Hound (Soapy):** Integrated support for the **VSG60A** vector signal generator with absolute dBm level control.
- **Sidekiq S4 (Epiq):** PCIe-based support for high-bandwidth, multi-channel operations.

### 2. Advanced Waveform Warheads
- **WiFi Preamble Sabotage:** Protocol-aware disruption of 802.11b/g/n preambles before payload delivery.
- **Distributed Bandwidth Expansion (+BW):** Synchronized dual-SDR tuning to "Spectral Stitch" a continuous 40 MHz tactical block.
- **Differential Comb:** High-density spectral dead-zones designed to defeat frequency-hopping targets.

### 3. Precision Safety Engine
- **Absolute Level Control:** Real-time dBm adjustments ( -120 to +10 dBm) to protect external power amplifiers.
- **Calibration Matrix:** Automatic Gain-to-dBm mapping via the integrated RF System Calibrator.

---

## 📦 Standalone Tactical Deployment (Offline)

The suite is designed for deployment on air-gapped, high-performance workstations using the **Universal Hardware Container (UHC)**.

### 1. Export the Environment (Online)
Build the image and package it for transfer:
```bash
docker build -t predator-jammer:latest .
docker save predator-jammer:latest | gzip > predator_image.tar.gz
```

### 2. Deploy (Offline)
Move `predator_image.tar.gz` and `run_standalone.sh` to the target machine via USB.
```bash
# Load the image
gunzip -c predator_image.tar.gz | docker load

# Launch with Hardware Passthrough (PCIe/USB)
chmod +x run_standalone.sh
./run_standalone.sh
```

---

## 🛠️ Project Structure
- **`apps/PredatorJammer.py`**: The primary tactical console for reactive operations.
- **`apps/SystemCalibrator.py`**: Automated RF power and frequency calibration.
- **`gr-techniquemaker/`**: C++ native DSP core for high-performance signal processing.
- **`config/predator_presets.json`**: Tactical profiles for DAPS, WiFi, and ISM targets.
- **`run_standalone.sh`**: Hardware-aware launcher with PCIe/USB driver injection.

---

## 📄 Documentation
- [Techniques Overview](docs/TECHNIQUES.md)
- [Docker & Deployment Guide](docs/DOCKER_INSTRUCTIONS.md)
- [Future Plans](docs/FUTURE_PLANS.md)

---

## 🛡️ License
This project is intended for authorized RF testing and electronic warfare research only. Ensure compliance with all local spectrum regulations before transmitting.
