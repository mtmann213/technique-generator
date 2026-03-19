# Changelog: TechniqueMaker Improvements

## [2026-03-13] - Project Reorganization & Precision Engine Finalization

### 🏗️ Directory Refactor (New Professional Structure)
- **Organizational Sweep:** Moved all core applications to `apps/`, persistent data to `config/`, documentation to `docs/`, and experiments to `tests/`.
- **Single Source of Truth:** Removed duplicated `BaseWaveforms.py` from the root. All tools now import the core DSP logic directly from the installed OOT module.
- **Unified Launcher:** Updated `TechniqueMaker.py` to support the new directory structure while maintaining "one-command" usability.
- **Improved Version Control:** Updated `.gitignore` to keep the root clean of generated datasets and binary session logs.

### 🛠️ RF System Calibrator (Precision Engine)
- **Smart 2D Interpolation:** Implemented row-wise linear extrapolation with `scipy.interpolate` to fill gaps in frequency and power ranges.
- **Monotonic Filtering:** Added logic to ignore measurement noise and saturation points, ensuring a clean Gain-to-Power mapping.
- **Stability Averaging:** Integrated 5-snapshot averaging and increased settling times (0.5s) for rock-solid loopback measurements.
- **Multi-Hardware Support:** Native support for USRP (UHD) loopback and Signal Hound (Soapy) auto-mode.
- **Operational Analytics:** Added an "Operational View" plot and a spreadsheet-style table view for required USRP Gains.
- **Data Export:** Added CSV export for characterization tables.

### 🦅 Predator Reactive Analysis Console
- **Integrated Calibration Display:** Added real-time "Estimated Output (dBm)" telemetry mapped from the `config/calibration_matrix.json`.
- **Refined Targeting UI:** Updated "Manual" mode and numeric Clock-Pull entry for high-precision interdiction.
