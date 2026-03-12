# Changelog: TechniqueMaker Improvements

## [2026-03-11] - Protocol-Aware Analysis & Interdiction

### 🦅 Predator Reactive Analysis Console
- **Adaptive Bandwidth Sculpting:** Integrated real-time -10dB occupied bandwidth measurement to automatically match the target signal's width.
- **Preamble Sabotage:** Implemented timing-gated interdiction that targets only the synchronization window of detected signals (Invisible Mode).
- **Clock-Pull Drift:** Added linear frequency ramping to disrupt receiver frequency tracking loops and PLLs.
- **Stability Frame Stutter:** Added periodic interdiction logic to force receiver stability counter resets.
- **Named Preset Manager:** Implemented a multi-preset system with persistent JSON storage for rapid scenario switching.
- **Professional Terminology:** Completely scrubbed all aggressive language, replacing it with technical terms (**Interdiction**, **Signal Template**, **Tracking**, **Gating**).

### 🚀 DSP & Signal Synthesis
- **Correlator Confusion:** Added a new Signal Template based on randomized Zadoff-Chu sequences to stress software-defined timing scanners.
- **Synchronized Core:** Unified `BaseWaveforms.py` across the root project and GNU Radio OOT module.
- **Stateful Integration:** Refined phase integration math to handle frequency ramps (Clock-Pull) without phase jumps.

### 🏗️ Tooling
- **Unified Launcher:** Enhanced `TechniqueMaker.py` with improved permission handling and executable flags.
- **Documentation Suite:** Refreshed `README.md`, `TECHNIQUES.md`, and `FUTURE_PLANS.md` to reflect the transition to a professional SIGINT suite.
