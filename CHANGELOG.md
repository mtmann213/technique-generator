# Changelog: TechniqueMaker Improvements

## [2026-03-13] - Hydra Auto-Surgical & High-Speed Wideband Support

### 🦅 Predator Reactive Analysis Console
- **Hydra Auto-Surgical Mode:** New feature that automatically identifies spectral peaks above a threshold and deploys matched-bandwidth "comb teeth" to disrupt them in real-time.
- **Wideband Sample Rate Control:** Added dynamic sample rate selection (up to 50MHz+) directly in the "Radio Tuning" panel.
- **Flowgraph Lifecycle Management:** Added "Restart Flowgraph" button to apply hardware-level changes (like sample rate) without restarting the entire app.
- **Integrated Calibration Display:** Added real-time "Estimated Output (dBm)" telemetry mapped from the `config/calibration_matrix.json`.

### 🚀 C++ Core (Hydra Engine)
- **Spectral Detection Pipeline:** Implemented windowed FFT island detection in native C++ for ultra-fast, gapless monitoring.
- **Multi-Target Surgical Synthesis:** Optimized C++ loop that sums multiple mixed/filtered jammers into a single high-performance output stream.
- **FFT-Matched Bandwidth:** The interdiction signal automatically scales its width to match the detected target's -10dB bandwidth.

### 🏗️ Project Reorganization & Software Engineering
- **Directory Refactor:** Moved all core applications to `apps/`, persistent data to `config/`, documentation to `docs/`, and experiments to `tests/`.
- **Centralized Configuration:** All hardware serials and RF defaults are now managed via `config/system_config.json`.
- **Smart 2D Interpolation:** Row-wise linear extrapolation with monotonic filtering for characterization tables.
- **Standardized Logging:** Implemented Python's `logging` framework across all tools.
