# TechniqueMaker: Advanced RF Analysis & Signal Synthesis Suite

**TechniqueMaker** is a professional-grade signal generation and electronic stress-testing toolkit. It provides a modular framework for generating complex interference patterns, automated signal tracking/interdiction using SDRs, and mass-producing labeled datasets for Machine Learning (ML) signal classification.

---

## 🚀 The Unified Launcher
The easiest way to use the suite is through the unified launcher. It automatically handles your `PYTHONPATH` and environment setup.

```bash
chmod +x TechniqueMaker.py
./TechniqueMaker.py --help
```

### Modes:
*   **`gui`**: Launches the standalone signal generator with visual PSD previews.
*   **`predator`**: Launches the **Reactive Analysis Console** (High-performance signal tracking & interdiction).
*   **`batch`**: Runs the **AI Dataset Factory** to generate SigMF training data.
*   **`install`**: Builds and installs the GNU Radio OOT module.

---

## 🦅 Predator Reactive Analysis Console
The flagship tool of the suite. Designed for real-time RF analysis and automated interdiction using USRP hardware (e.g., B205-mini).

*   **Auto-Track (FFT):** Scans the spectrum and automatically locks onto signals above a threshold.
*   **Hydra Mode:** Track and interdict up to 8 targets simultaneously with prioritized signal templates.
*   **Manual Override:** Precisely target a specific frequency offset using a real-time slider.
*   **Template Config:** On-the-fly reconfiguration of interdiction signals (Noise, Chirps, Zadoff-Chu, etc.).
*   **SigMF Logging:** Record entire RF sessions to disk with full metadata for forensic playback.

---

## 🤖 AI Dataset Factory
Mass-produce SigMF-compliant datasets for training signal classification models.

```bash
./TechniqueMaker.py batch --args --count 100 --fs 1000000 --duration 0.02
```
Generates randomized, labeled captures for all 15 signal techniques, organized into a clean folder structure for deep learning pipelines.

---

## 📻 GNU Radio Integration
TechniqueMaker includes a high-performance **OOT Module** (`gr-techniquemaker`).

1.  **Install:** `./TechniqueMaker.py install`
2.  **Use:** Search for **Technique PDU Generator** in GRC.
3.  **Features:** Supports both Burst (PDU) and Continuous (Stream) modes with real-time frequency sliding and vectorized DSP.

---

## 🏗️ Project Structure
*   `TechniqueMaker.py`: The master launcher.
*   `PredatorJammer.py`: Reactive analysis and interdiction console.
*   `BaseGui.py`: Standalone signal generator with real-time PSD preview.
*   `BatchGenerator.py`: Labeled dataset production tool.
*   `BaseWaveforms.py`: The core DSP engine (Optimized & Vectorized).
*   `gr-techniquemaker/`: Full GNU Radio OOT module source.
*   `TECHNIQUES.md`: Detailed technical reference for all signal synthesis algorithms.

## 🛠️ Requirements
*   **OS:** Linux (Ubuntu 22.04+ recommended)
*   **Hardware:** UHD-compatible SDRs (for Predator mode)
*   **Software:** Python 3.10+, GNU Radio 3.10+, NumPy, SciPy, PyQt5
