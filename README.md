# TechniqueMaker: Advanced RF Analysis & Signal Synthesis Suite

**TechniqueMaker** is a professional-grade signal generation and electronic stress-testing toolkit. It provides a modular framework for generating complex interference patterns, automated signal tracking/interdiction using SDRs, and mass-producing labeled datasets for Machine Learning (ML) signal classification.

---

## 🦅 Predator-Native (C++ Version)
The high-performance, native implementation of the Reactive Analysis Console. Built for tactical deployment where deterministic latency and low jitter are required.

### Key Capabilities:
*   **Zero-GIL Control:** Bypasses Python entirely for real-time parameter updates.
*   **Predictive Pattern Engine:** Integrated PRNG sequence cracking for hoppers.
*   **Hydra V2:** Supports up to 50 simultaneous surgical targets.

### Compilation & Launch:
```bash
cd predator-cpp/build
cmake ..
make -j$(nproc)
./PredatorNative
```

---

## 🚀 The Unified Launcher
The easiest way to use the suite is through the unified launcher. It automatically handles your environment and Docker setup.

```bash
chmod +x TechniqueMaker.py
./TechniqueMaker.py predator
```

---

## 🦅 Predator Reactive Analysis Console
The flagship tool of the suite. Designed for real-time RF analysis and protocol-aware interdiction using USRP hardware.

### Key Tactical Features:
*   **Protocol-Aware Gating:** Targets specific phases of a digital link (Preamble Sabotage, Stability Stutter).
*   **Tracking Loop Attacks:** Disrupts PLLs and frequency correction using Clock-Pull frequency ramping.
*   **Adaptive BW Sculpting:** Automatically measures and matches the target signal's occupied bandwidth.
*   **Hydra Multi-Tracking:** Track and interdict up to 8 simultaneous targets using peak suppression.
*   **SigMF Logging:** Record entire RF sessions with compliant metadata for forensic playback.

---

## 🤖 AI Dataset Factory
Mass-produce SigMF-compliant datasets for training signal classification models. Organized, labeled, and randomized for high-quality deep learning pipelines.

---

## 📻 GNU Radio Integration
TechniqueMaker includes a high-performance **OOT Module** (`gr-techniquemaker`).
*   Vectorized DSP for 2 MHz+ real-time operation.
*   Supports both Burst (PDU) and Continuous (Stream) modes.
*   Fully programmable via Message Ports.

---

## 🏗️ Project Structure
*   `TechniqueMaker.py`: Master launcher.
*   `apps/`: Core applications (`PredatorJammer.py`, `SystemCalibrator.py`, `BaseGui.py`).
*   `docs/`: Documentation (`TECHNIQUES.md`, `DOCKER_INSTRUCTIONS.md`, etc.).
*   `gr-techniquemaker/`: High-performance GNU Radio OOT Module.
*   `config/`: User presets and calibration matrices.

## 🛠️ Requirements
*   **OS:** Linux (Ubuntu 22.04 recommended)
*   **Hardware:** UHD-compatible SDRs (e.g., B205-mini)
*   **Software:** Docker (optional), GNU Radio 3.10+, NumPy, SciPy, PyQt5
