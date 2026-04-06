# TechniqueMaker: Advanced Reactive Interdiction Suite

TechniqueMaker is a high-performance SDR platform designed for protocol-aware RF interdiction. It provides a real-time C++/Python framework for detecting, tracking, and disrupting complex digital waveforms with sub-millisecond precision.

---

## 🦅 Tactical Capabilities

### 1. Multi-Hardware Interdiction
- **USRP (UHD):** Native support for B205-mini, B210, and N-series devices.
- **Signal Hound (Soapy):** Integrated support for the **VSG60A** vector signal generator with absolute dBm level control.
- **Sidekiq S4/X4 (Epiq):** PCIe-based support for high-bandwidth, multi-channel operations. Features strict MTU DMA alignment and explicit antenna port routing for robust 200+ MSPS stitching.

### 2. Advanced Waveform Warheads
- **WiFi Preamble Sabotage:** Protocol-aware disruption of 802.11b/g/n preambles before payload delivery.
- **Distributed Bandwidth Expansion (+BW):** Synchronized dual-SDR tuning to "Spectral Stitch" a continuous 40 MHz tactical block.
- **Differential Comb:** High-density spectral dead-zones designed to defeat frequency-hopping targets.

### 3. Precision Safety Engine
- **Absolute Level Control:** Real-time dBm adjustments ( -120 to +10 dBm) to protect external power amplifiers.
- **Calibration Matrix:** Automatic Gain-to-dBm mapping via the integrated RF System Calibrator.

### 4. 🤖 Air-Gapped Local AI Integration
- **Offline Coding Assistant:** Includes the `lcc` (Local Claude Code) script to route AI requests to a local `llama-server` running Qwen2.5-Coder.
- **Troubleshooting Pipeline:** Allows piping build and DMA stream errors directly to the local GPU-accelerated LLM for instant resolution on NVIDIA Orin/Jetson devices without internet access.
- Refer to `LLM_HANDOVER_DOCUMENT.md` for AI context passing and synchronization.

---

## 📦 Standalone Tactical Deployment (Offline)

### Target: x86_64 Ubuntu 22.04 (confirmed architecture)

For ARM64 (NVIDIA Orin), see `docs/AIRGAP_ARM64.md` instead.

### Quick Setup (Online Machine)
```bash
# Create the complete offline bundle
chmod +x bundle_offline.sh
./bundle_offline.sh
```

This produces:
- `techniquemaker_offline_v1.tar.gz` — Full source tree (excludes .git, build artifacts)
- `sidekiq_sng_v1.zip` — Sidekiq-SNG standalone (backwards compat)

Transfer both files + `predator_image.tar.gz` to the air-gapped target via USB.

### Deploy (Offline / Air-Gapped Target)
```bash
# 1. Extract the bundle
tar xzf techniquemaker_offline_v1.tar.gz
cd technique-generator/

# 2. Pre-flight hardware verification
./check_hardware.sh          # Full system check
./check_hardware.sh --sidekiq  # Sidekiq X4/S4 focused

# 3. Install GNU Radio OOT module
./install.sh

# 4. Build Sidekiq streaming engine (if using sng directly)
cd sidekiq-sng && ./build_on_target.sh && cd ..

# 5. Load Docker image
gunzip -c predator_image.tar.gz | docker load

# 6. Launch
python3 TechniqueMaker.py predator     # Predator Jammer Console
./run_standalone.sh                    # Docker with hardware passthrough
```

---

## 🔧 Sidekiq X4 Setup (Air-Gapped)

The Sidekiq X4 is a **PCIe x4** SDR with 4 TX/RX channels and 400+ MSPS aggregate bandwidth. It connects via the **Epiq SoapySDR plugin** -- no GNU Radio integration required (SNG uses it natively).

### Prerequisites (Install on Air-Gapped Target Before Transferring)

These must be installed from the Epiq SDK package (distributed separately):

1. **Sidekiq PCIe Driver** -- kernel module for the X4 hardware interface
2. **SoapySDR + Sidekiq Module** -- `SoapySidekiq` SoapySDR plugin
3. **Firmware** -- loaded automatically by the driver on module load

You can verify installation by running:
```bash
SoapySDRUtil --probe="driver=sidekiq"
```
This should report 4 TX and 4 RX channels with antenna labels (J1, J7, etc.).

### Hardware Verification
```bash
# Check PCIe enumeration
lspci | grep -i -e "epiq" -e "sidekiq"

# Check SoapySDR device
SoapySDRUtil --find

# Deep probe: software index -> physical port mapping
cd sidekiq-sng
./sng --probe
```

### Streaming with Sidekiq X4
```bash
# Single channel, 100MHz bandwidth, Port J1 (software index 0)
./sng --tech noise --bw 100e6 --rate 100e6 --chan 0 --freq 2400e6 --stream --gain 10

# Multi-channel spectral stitching: ports J1+J2 for 200MHz coverage
./sng --tech noise --bw 200e6 --rate 150e6 --chan 0,1 --freq 2400e6 --stream --gain 10

# Surgical: 3-tone disruption via Port J7 (TX1, index 1)
./sng --tech noise-tones --hops "-20M 0 20M" --bw 1M --rate 50M --chan 1 --freq 915M --stream --gain 5
```

### Antenna Port Mapping (X4)

The X4 has **4 physical antennas**. Always use `--probe` first, as port labels vary by firmware version:
```
Software Index [0]: Hardware Label: J1 (TRX1)
Software Index [1]: Hardware Label: J7 (TX1)
Software Index [2]: Hardware Label: J8 (TX2)
Software Index [3]: Hardware Label: J9 (TRX2)
```

**Critical:** Only power channels that have antennas connected. Powering an unused port can cause reflected power damage.

### Docker + Sidekiq X4

The `run_standalone.sh` script detects Sidekiq X4 via `lspci` and SoapySDR, then passes `--privileged` to Docker for PCIe device access. The Docker image includes SoapySDR -- just ensure the X4 driver is loaded on the host (the `--privileged` flag maps the device nodes through).

### Using Sidekiq Inside the Container

Inside the container, you may need to verify SoapySDR sees the device:
```bash
SoapySDRUtil --find
SoapySDRUtil --probe="driver=sidekiq"
```

If the device is not found, the PCIe device may not be mapped. The container must be launched with `--privileged` (handled by `run_standalone.sh`).

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
