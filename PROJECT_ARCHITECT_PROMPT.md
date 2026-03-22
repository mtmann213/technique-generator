# Developer Instruction: Reproduce "TechniqueMaker" - Unified Python RF Suite

## 1. Project Vision
Create a professional-grade SIGINT and reactive interdiction suite optimized for **Ettus Research USRPs (UHD)**. The system must be a "Single-Install" Python application that performs real-time spectral analysis, autonomous multi-target interdiction (Hydra), and persistent channel denial (Sticky Trap) without requiring custom C++ OOT modules.

## 2. System Architecture
*   **Direct Hardware Interface:** Use the `uhd` library (`uhd.usrp_source`, `uhd.usrp_sink`) for native Ettus device control.
*   **DSP Core:** A custom Python `gr.sync_block` (the "Interdictor") that contains all reactive logic, FFT detection, and multi-signal synthesis.
*   **Waveform Engine:** A vectorized NumPy library defining 15 surgical templates (LFM Chirps, OFDM Noise, Differential Comb, etc.).
*   **Frontend:** A high-performance PyQt5 tabbed GUI for real-time waterfall analysis and tactical control.

## 3. Directory Structure
```text
TechniqueMaker/
├── TechniqueMaker.py         # Master entry point
├── apps/
│   ├── PredatorJammer.py     # Main Tactical Console (UHD Integrated)
│   ├── WaveformEngine.py     # Vectorized DSP templates (NumPy)
│   └── core_utils.py         # Config & Hardware Discovery
├── config/
│   ├── system_config.json    # Hardware serials & RF defaults
│   └── presets.json          # Mission scenarios
└── docs/                     # Mathematical & tactical guides
```

## 4. Tactical Logic Implementation

### 4.1 Hydra Auto-Surgical Logic (Python/NumPy)
Implement spectral detection inside the Python block's `work()` function:
1.  **FFT Detection:** Compute a windowed FFT of the input stream.
2.  **Surgical Mapping:** Identify peaks above threshold; calculate center frequency and bandwidth.
3.  **Matched Synthesis:** Dynamically resample base waveforms using NumPy linear interpolation to match target bandwidths.
4.  **Multi-Target Mixing:** Shift each synthesized jammer to its target frequency and sum them into the output buffer.

### 4.2 Sticky Channel Denial (Persistent Trap)
Maintain a persistent state within the Python block:
*   **Memory:** Store a list of detected frequencies. Even when the target hopper moves, the jammer continues firing on those coordinates.
*   **Gated Look-through:** Implement a high-precision sample counter to toggle the TX output. Periodically silence the jammer (e.g., 5ms every 50ms) to allow the detector to see the "clean" spectrum and find new hops.

### 4.3 Direct Ettus Control
*   **Discovery:** Implement `uhd.find_devices()` to populate a UI dropdown.
*   **Tuning:** Support real-time gain, frequency, and sample rate updates via the UHD API.

## 5. Functional Requirements for the LLM
1.  **Zero-Build Install:** The entire project should run with `pip install gnuradio uhd pyqt5 numpy scipy`. No C++ compilation required.
2.  **Waveform Library:** Implement 15 templates including: Differential Comb (OFDM Erasure), Correlator Confusion (DF-OFDM Sabotage), Swept Noise, and LFM Chirps.
3.  **Virtual Mode:** Allow the GUI to launch and simulate logic without an SDR physically connected.
4.  **Hardware Hot-Plug:** Allow the user to Scan, Select, and Connect to USRPs by serial number within the GUI.

## 6. Implementation Order
1.  Build the `WaveformEngine.py` with 15 signal templates.
2.  Implement the `PredatorJammer` Python block with FFT detection and Look-through gating.
3.  Create the PyQt5 tabbed interface with Header-based Tuning.
4.  Integrate the `uhd` source/sink blocks with dynamic serial number loading.
