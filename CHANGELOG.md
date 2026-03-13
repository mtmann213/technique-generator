# Changelog: TechniqueMaker Improvements

## [2026-03-13] - Precision Calibration & Smart Interpolation

### 🛠️ RF System Calibrator (Precision Engine)
- **Smart 2D Interpolation:** Implemented row-wise linear extrapolation with `scipy.interpolate` to fill gaps in frequency and power ranges.
- **Monotonic Filtering:** Added logic to ignore measurement noise and saturation points, ensuring a clean Gain-to-Power mapping.
- **Stability Averaging:** Integrated 5-snapshot averaging and increased settling times (0.5s) for rock-solid USRP-to-USRP loopback measurements.
- **Multi-Hardware Support:** Added native support for USRP (UHD) closed-loop receivers, Signal Hound (Soapy) auto-mode, and Spike (Manual) high-accuracy mode.
- **Operational Analytics:** Added an "Operational View" that displays the required USRP Gain for a target dBm output across the frequency spectrum.
- **Data Explorer:** Added a spreadsheet-style table window and CSV export for easy calibration data review.
- **Calibrator Presets:** Persistent save/load system for hardware sweep configurations.

### 🦅 Predator Reactive Analysis Console
- **Integrated Calibration Display:** Added real-time "Estimated Output (dBm)" telemetry mapped from the `calibration_matrix.json`.
- **UI Refinements:** Fixed syntax errors in plotting logic and ensured proper widget scaling for the calibrated power display.

### 🏗️ Architecture & Infrastructure
- **Dependency Update:** Updated `Dockerfile` and `TechniqueMaker.py` to support `scipy` interpolation and `SoapySDR` requirements.
- **Documentation Sync:** Refreshed `TECHNIQUES.md` and `README.md` with detailed calibration and characterization workflows.
