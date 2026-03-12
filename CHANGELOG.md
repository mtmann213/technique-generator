# Changelog: TechniqueMaker Improvements

## [2026-03-11] - UI Refinement & Advanced Protocol Gating

### 🦅 Predator Reactive Analysis Console
- **Refined Targeting UI:** Renamed "Freq Snipe" to **Manual** mode for improved technical clarity.
- **Clock-Pull Precision:** Replaced the frequency drift slider with a precise numeric entry field (Hz/s).
- **Hydra Telemetry:** Added a dynamic label to the Hydra slider to show current simultaneous target count.
- **Advanced Stutter Gating:** 
    - Added **Burst Frames** control to specify the number of consecutive frames to interdict.
    - Implemented **Clean Count Randomization** to defeat adaptive receiver algorithms.
- **UI Bugfixes:** Resolved layout issues and ensured proper widget scaling for the waterfall display.

### 🚀 DSP & Logic
- **Stutter Logic V2:** Refactored the `techniquepdu` block to support multi-frame bursts and randomized cycle lengths.
- **Parameter Validation:** Added protection against invalid inputs in the console's numeric fields.

### 🏗️ Architecture & Deployment
- **Dockerization:** Implemented a unified `Dockerfile` and helper scripts (`run_docker.sh`, `bundle_offline.sh`) for portable and air-gapped deployment.
- **Terminology Finalization:** Completed the transition from aggressive to professional SIGINT/EW terminology across all documentation and UI components.
- **Master Guide:** Updated `TECHNIQUES.md` with detailed mechanical explanations of advanced interdiction strategies.
