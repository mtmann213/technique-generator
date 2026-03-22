# Changelog: TechniqueMaker Improvements

## [2026-03-13] - Hydra Auto-Surgical & High-Speed Wideband Support

### 🦅 Predator Reactive Analysis Console
- **Professional UI Layout:** Overhauled the GUI with a header-based tuning bar and a tabbed sidebar (Hardware, Interdiction, Protocol) for intuitive tactical operation.
- **Status Badge System:** Added color-coded badges (OFFLINE, CONNECTED, TX SILENT, ACTIVE) for instant situational awareness.
- **Hardware Hot-Plug:** Predator can now launch in "Virtual Mode" without an SDR connected, allowing for real-time scanning and dynamic connection to discovered USRPs.
- **Sticky Channel Denial:** Implemented a persistent "trap" mode that discovery and locks onto hopper channels, maintaining interdiction even after the target moves.
- **Gated Look-through:** Added a configurable duty cycle (e.g., 90ms Jam / 10ms Silence) that silences the jammer periodically to allow for clean spectral scanning.
- **Hydra Auto-Surgical Mode:** Automatically identifies spectral peaks above a threshold and deploys matched-bandwidth "comb teeth" to disrupt them in real-time.

### 🚀 C++ Core (Hydra Engine)
- **Matched-Bandwidth Resampling:** Implemented a high-performance linear interpolator in the C++ work loop that dynamically scales the jamming signal's width to match the detected target's spectral footprint.
- **Multi-Target Surgical Synthesis:** Optimized C++ loop that sums multiple mixed/filtered jammers into a single high-performance output stream.
- **Persistent State Machine:** Added native C++ logic to track and maintain a growing list of discovered hopper channels.
- **Gating Counter:** High-precision sample counter implemented in the `work()` loop to manage Look-through duty cycles at the microsecond level.
- **Spectral Detection Pipeline:** Implemented windowed FFT island detection in native C++ for ultra-fast, gapless monitoring.

### 🏗️ Project Reorganization & Software Engineering
- **Directory Refactor:** Moved all core applications to `apps/`, persistent data to `config/`, documentation to `docs/`, and experiments to `tests/`.
- **Centralized Configuration:** All hardware serials and RF defaults are now managed via `config/system_config.json`.
- **Smart 2D Interpolation:** Row-wise linear extrapolation with monotonic filtering for characterization tables.
- **Standardized Logging:** Implemented Python's `logging` framework across all tools.
