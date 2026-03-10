# TechniqueMaker: Future Development Roadmap

This document outlines the planned enhancements and feature requests for the TechniqueMaker project, categorized by functional area.

## 1. GNU Radio OOT Block (gr-techniquemaker)
- [ ] **Dynamic Reconfiguration:** Add a "command" message port to `techniquepdu` to allow real-time parameter updates (BW, technique, etc.) via PMT dictionaries.
- [ ] **Streaming Mode Toggle:** Implement a "Loop" parameter to allow the block to output a continuous stream of the generated technique instead of just one-shot PDUs.
- [ ] **Tag-Based Triggering:** Add the ability to trigger a PDU burst based on Stream Tags (e.g., `tx_sob`) for precise timing synchronization.
- [ ] **Hardware Abstraction Layer:** Create a helper block to map metadata from PDUs directly to USRP UHD sink commands (frequency, gain, etc.).

## 2. DSP & Waveform Generation (`BaseWaveforms.py`)
- [ ] **Advanced Techniques:**
    - **LFM Chirp:** Standard Linear Frequency Modulation for radar/sync testing.
    - **OFDM-Shaped Noise:** Noise masked to match specific subcarrier and cyclic prefix structures.
    - **Frequency Hopping (FHSS):** A technique that generates a sequence of hops based on a seed or list.
- [ ] **Normalization Engine:** Implement a global "Target RMS" or "Peak Amplitude" parameter across all techniques to ensure consistent power levels.
- [ ] **Spectral Shaping:** Add a post-generation pulse-shaping or LPF stage to all techniques to minimize spectral regrowth.
- [ ] **Optimization:** Refactor `songMaker` and `swept_phasors` to use list-based collection instead of `np.concatenate` in loops to eliminate memory copy bottlenecks.

## 3. GUI & Tooling (`BaseGui.py`)
- [ ] **Visual Preview:** Integrate a `matplotlib` or `pyqtgraph` window to show the FFT and Time Domain plot before saving.
- [ ] **SigMF Metadata Expansion:** Automatically include all generation parameters (technique name, BW, symbol rate) in the `.sigmf-meta` "annotations" or "global" fields.
- [ ] **Batch Generator:** Create a CLI tool to generate large datasets of signals with randomized parameters for machine learning training.
- [ ] **Validation Layer:** Improve `infer_type_from_string` with explicit bounds checking for numeric fields (e.g., BW > 0).

## 4. Documentation & Testing
- [ ] **QA Test Suite:** Expand `qa_techniquepdu.py` to include automated signal integrity checks (e.g., verifying the generated BW matches the requested BW).
- [ ] **Installation Script:** Create a simple `install.sh` to handle the `cmake`, `make install`, and `ldconfig` steps for the OOT module.
- [ ] **Technique Reference Guide:** A markdown file explaining the math and use cases for each available signal technique.
