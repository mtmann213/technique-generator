# Changelog: TechniqueMaker Improvements

This document tracks the significant changes, optimizations, and new features added to the TechniqueMaker project.

## [2026-03-10] - Initial Project Modernization & OOT Integration

### 🏗️ Architecture & Distribution
- **GNU Radio OOT Module:** Created the `gr-techniquemaker` Out-Of-Tree module to allow the signal generator to be used directly in GNU Radio flowgraphs.
- **`install.sh`:** Added a one-click installation script to handle the CMake build and system installation process for the OOT module.
- **`README.md`:** Created a comprehensive guide for installation, testing, and project structure.
- **Repository Preservation:** Renamed original files to `BaseGui_ORIG.py` and `BaseWaveforms_ORIG.py` to maintain a clean development history.
- **`.gitignore`:** Added a standard Git ignore file to prevent build artifacts and Python cache files from cluttering the repository.

### 🚀 Performance Optimizations
- **`songMaker` Optimization:** Refactored note generation to use list-based collection instead of repeated `np.concatenate` inside loops. This reduced the generation time for a 2-second song from **~10 seconds to 0.1 seconds**.
- **Vectorization Ready:** Prepared the DSP codebase for further vectorization by modularizing the time-array and normalization logic.

### ✨ New Advanced Signal Techniques
- **LFM Chirp:** Standard Linear Frequency Modulation technique added for radar and synchronization testing.
- **FHSS Noise:** Frequency Hopping Spread Spectrum technique using narrowband noise bursts.
- **OFDM-Shaped Noise:** Advanced technique that generates noise with the specific spectral signature of an OFDM signal (Rectangular subcarriers + Cyclic Prefix).

### ⚙️ Feature Enhancements
- **Technique PDU Generator Block:** A dynamic GNU Radio block that:
    - Outputs standard PDUs (metadata + complex64 samples).
    - Features a context-aware GUI in GRC (only shows parameters relevant to the selected technique).
    - Supports all 14 signal techniques from a single block.
- **Normalization Engine:** Implemented a centralized `_normalize_signal` helper across all techniques.
    - Added **Target Level** and **Norm Type** (Peak vs. RMS) parameters.
    - Ensures consistent power levels across different techniques, preventing clipping or quiet signals in SDR hardware.

### 🧪 Testing & Verification
- **Sandbox Test Script:** Created `test_advanced_dsp.py` using Matplotlib to allow rapid verification of DSP math without needing to launch GNU Radio.
- **Self-Terminating GRC Test:** Developed `test_techniquepdu.grc` with a Python snippet that automatically stops the flowgraph after 30 seconds, preventing infinite CPU consumption during tests.
