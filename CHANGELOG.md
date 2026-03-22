# Changelog: TechniqueMaker Improvements

## [2026-03-13] - Hydra Auto-Surgical & High-Speed Wideband Support

### 🦅 Predator Reactive Analysis Console
- **Sticky Channel Denial:** Implemented a persistent "trap" mode that discovery and locks onto hopper channels, maintaining interdiction even after the target moves.
- **Gated Look-through:** Added a configurable duty cycle (e.g., 90ms Jam / 10ms Silence) that silences the jammer periodically to allow for clean spectral scanning.
- **Hydra Auto-Surgical Mode:** New feature that automatically identifies spectral peaks above a threshold and deploys matched-bandwidth "comb teeth" to disrupt them in real-time.
- **Wideband Sample Rate Control:** Added dynamic sample rate selection (up to 50MHz+) directly in the "Radio Tuning" panel.
- **Hardware Hot-Plug:** Predator can now launch in "Virtual Mode" without an SDR connected, allowing for real-time scanning and dynamic connection to discovered USRPs.
- **Flowgraph Lifecycle Management:** Added "Restart Flowgraph" button to apply hardware-level changes (like sample rate) without restarting the entire app.
- **Integrated Calibration Display:** Added real-time "Estimated Output (dBm)" telemetry mapped from the `config/calibration_matrix.json`.

### 🚀 C++ Core (Hydra Engine)
- **Persistent State Machine:** Added native C++ logic to track and maintain a growing list of discovered hopper channels.
- **Gating Counter:** High-precision sample counter implemented in the `work()` loop to manage Look-through duty cycles at the microsecond level.
- **Spectral Detection Pipeline:** Implemented windowed FFT island detection in native C++ for ultra-fast, gapless monitoring.
- **Multi-Target Surgical Synthesis:** Optimized C++ loop that sums multiple mixed/filtered jammers into a single high-performance output stream.
- **FFT-Matched Bandwidth:** The interdiction signal automatically scales its width to match the detected target's -10dB bandwidth.

### 🏗️ Project Reorganization & Software Engineering
- **Directory Refactor:** Moved all core applications to `apps/`, persistent data to `config/`, documentation to `docs/`, and experiments to `tests/`.
- **Centralized Configuration:** All hardware serials and RF defaults are now managed via `config/system_config.json`.
- **Smart 2D Interpolation:** Row-wise linear extrapolation with monotonic filtering for characterization tables.
- **Standardized Logging:** Implemented Python's `logging` framework across all tools.
