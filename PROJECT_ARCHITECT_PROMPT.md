# Developer Instruction: Reproduce "TechniqueMaker" Tactical RF Suite

## 1. Project Vision
Create a professional-grade SIGINT and reactive interdiction suite capable of real-time spectral analysis, multi-target tracking (Hydra), and surgical channel denial. The suite must be high-performance (C++ core) with a responsive PyQt5 GUI and support air-gapped deployment via Docker.

## 2. System Architecture
The project uses a **Bilingual OOT (Out-Of-Tree) Module Architecture**:
*   **Core Engine:** A C++ GNU Radio block (`interdictor_cpp`) for high-bandwidth DSP.
*   **Fallback/Experimentation:** A Python `sync_block` (`techniquepdu`) mirroring the C++ logic.
*   **Frontend:** PyQt5-based applications (`PredatorJammer`, `SystemCalibrator`) that dynamically load the C++ core or fall back to Python.
*   **Configuration:** Centralized `system_config.json` for hardware abstraction.

## 3. Directory Structure
```text
TechniqueMaker/
├── TechniqueMaker.py         # Master CLI launcher & Path injector
├── apps/                     # Professional PyQt5 Applications
│   ├── PredatorJammer.py     # Main Reactive Console
│   ├── SystemCalibrator.py   # RF Chain Characterization tool
│   └── core_utils.py         # ConfigManager & safe parsing
├── config/                   # Persistent JSON/CSV data
├── gr-techniquemaker/        # GNU Radio OOT Module (C++ & Python)
│   ├── lib/                  # Native C++ work() loops & detectors
│   ├── python/               # DSP Template Library (BaseWaveforms.py)
│   └── grc/                  # Block YAML bindings
└── scripts/                  # Install & Docker infrastructure
```

## 4. Key Mathematical Implementations

### 4.1 Hydra Auto-Surgical Detector (C++)
Implement a windowed FFT pipeline in the `work()` loop:
1.  Fill circular buffer -> Windowed FFT -> Magnitude to dB.
2.  **Island Detection:** Group contiguous bins above `threshold_db`.
3.  **Estimation:** Calculate `center_freq` and `-10dB bandwidth`.
4.  **Resampled Synthesis:** For each target, use **Linear Interpolation** to resample the base "Warhead" waveform:
    $$s(t) = s[n] \cdot (1 - frac) + s[n+1] \cdot frac$$
5.  **Multi-Target Summation:** Sum all resampled/mixed targets into the output stream.

### 4.2 Sticky Channel Denial
Implement a state machine that appends newly discovered target frequencies to a `std::vector<Target>`. 
1.  **Look-through Gating:** Implement a sample counter to toggle between `JAM` and `LOOK` states (e.g., 90% duty cycle).
2.  Silence the output during `LOOK` to prevent self-interference during spectral discovery.

### 4.3 RF Calibration (Python)
Implement **2D Smart Interpolation**:
*   Perform Frequency vs. Gain sweeps.
*   Enforce **Monotonic Filtering** (discard points where Pwr drops as Gain increases).
*   Use `scipy.interpolate.interp1d` with `fill_value="extrapolate"` to generate an inverse lookup table (Target Pwr -> Required Gain).

## 5. Functional Requirements for the LLM
1.  **DSP Templates:** Implement 15 vectorized waveforms (LFM Chirps, FHSS Noise, Differential Comb, Correlator Confusion).
2.  **Hardware Hot-Plug:** Use `uhd.find_devices()` to populate a UI dropdown; allow dynamic Connect/Disconnect without restarting the flowgraph.
3.  **High-Performance Mixing:** All mixing must happen in C++ using optimized phasor multiplication.
4.  **Logging:** Use standard `logging` module with file and console handlers.

## 6. Implementation Order
1.  Scaffold the `gr-techniquemaker` GNU Radio module (C++ template).
2.  Implement the `BaseWaveforms.py` DSP math.
3.  Build the C++ `work()` loop with FFT detection and multi-target summation.
4.  Create the `ConfigManager` and centralized JSON structure.
5.  Build the `PredatorJammer` Tabbed UI.
6.  Implement the `SystemCalibrator` with CSV export and table views.
