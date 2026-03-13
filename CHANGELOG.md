# Changelog: TechniqueMaker Improvements

## [2026-03-12] - RF Calibration & Precision Interdiction

### 🦅 Predator Reactive Analysis Console
- **Calibrated Power Display:** Now shows real-time "Est. Output: XX.X dBm" mapped from calibration data.
- **Refined Targeting UI:** Renamed "Freq Snipe" to **Manual** mode for improved technical clarity.
- **Clock-Pull Precision:** Replaced the frequency drift slider with a precise numeric entry field (Hz/s) for exact frequency ramping.
- **Hydra Telemetry:** Added a dynamic value label to the Hydra slider to show current simultaneous target count.
- **Advanced Stutter Gating:** 
    - Added **Burst Frames** control to specify the exact number of consecutive frames to destroy.
    - Implemented **Clean Count Randomization** toggle to defeat adaptive receiver state machines.

### 🛠️ RF System Calibrator (New Tool)
- **Manual Entry (Spike) Mode:** Automated USRP sweep logic paired with manual power entry from Spike software for maximum accuracy.
- **SoapySDR (Auto) Mode:** Integration with Signal Hound BB60D for fully autonomous characterization.
- **Technique Comparison:** New analysis mode to measure PAPR and power offsets for all 15 synthesis templates relative to a CW tone.
- **Analytics:** Generates real-time heatmaps of PA flatness and compression points.

### 🚀 DSP & GNU Radio Block
- **Adaptive Bandwidth Sculpting:** Integrated real-time -10dB occupied bandwidth measurement to automatically match interdiction signals to targets.
- **Preamble Sabotage (Invisible Mode):** Implemented timing-gated interdiction targeting only the synchronization window (default 20ms).
- **Stutter Logic V2:** Refactored the `techniquepdu` block to support multi-frame bursts and randomized clean-cycle lengths.
- **Synthesis-Integrated Transmitter:** The calibration engine now uses the real interdiction block for 1:1 waveform accuracy.

### 🏗️ Deployment & Portability
- **Tactical Dockerization:** Fully updated `Dockerfile` including `SoapySDR` and all protocol analysis dependencies.
- **Air-Gap Support:** Enhanced `DOCKER_INSTRUCTIONS.md` with "Surgical Update" guides for disconnected field laptops.
- **Professional Terminology:** Finalized transition to SIGINT/EW standards across all modules.
