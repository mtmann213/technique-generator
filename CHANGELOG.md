# Changelog: TechniqueMaker Improvements

## [2026-03-12] - UI Precision & Hardcore Protocol Interdiction

### 🦅 Predator Reactive Analysis Console
- **Refined Targeting UI:** Renamed "Freq Snipe" to **Manual** mode for improved technical clarity.
- **Clock-Pull Precision:** Replaced the frequency drift slider with a precise numeric entry field (Hz/s) for exact frequency ramping.
- **Hydra Telemetry:** Added a dynamic value label to the Hydra slider to show current simultaneous target count.
- **Advanced Stutter Gating:** 
    - Added **Burst Frames** control to specify the exact number of consecutive frames to destroy.
    - Implemented **Clean Count Randomization** toggle to defeat adaptive receiver state machines.
- **Protocol Parameter Validation:** Added protection against invalid inputs in all protocol-aware numeric fields.

### 🚀 DSP & GNU Radio Block
- **Adaptive Bandwidth Sculpting:** Integrated real-time -10dB occupied bandwidth measurement to automatically match interdiction signals to targets.
- **Preamble Sabotage (Invisible Mode):** Implemented timing-gated interdiction targeting only the synchronization window (default 20ms).
- **Stutter Logic V2:** Refactored the `techniquepdu` block to support multi-frame bursts and randomized clean-cycle lengths.
- **Synchronized Core:** Unified `BaseWaveforms.py` across the root project and GNU Radio OOT module for a single source of truth.

### 🏗️ Deployment & Portability
- **Tactical Dockerization:** Created a unified `Dockerfile` and `run_docker.sh` for hardware/GUI passthrough on any machine.
- **Air-Gap / Offline Bundle:** Implemented `bundle_offline.sh` to export the entire environment into a portable `.tar` file for non-networked field laptops.
- **Professional Terminology:** Finalized the transition to SIGINT/EW standards (**Interdiction**, **Signal Template**, **Tracking**, **Gating**).
- **Master Guide:** Updated `TECHNIQUES.md` with detailed mechanical explanations of advanced interdiction strategies.
