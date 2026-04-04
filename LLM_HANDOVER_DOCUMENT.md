# TechniqueMaker / Sidekiq-SNG: LLM Handover Document

## 1. Project Overview
**TechniqueMaker** is a professional-grade SIGINT and reactive RF interdiction suite. It operates in a dual-environment setup: a host machine for development and an **air-gapped target machine** for deployment, specifically interacting with **Epiq Solutions Sidekiq hardware (S4/X4)** via SoapySDR.

The project features a **dual-engine DSP architecture**:
1.  **Python/NumPy "Golden Set"**: Used for mathematical validation, rapid prototyping, and baseline technique generation (`BaseWaveforms.py`).
2.  **High-Performance C++ Engine (`sidekiq-sng`)**: A native C++ implementation (`WaveformEngine.cpp` & `main.cpp`) designed for direct DMA memory access to the Sidekiq hardware, bypassing GNU Radio overhead for extreme bandwidths (up to 200+ MSPS via spectral stitching).

## 2. Core Capabilities & Techniques
The suite supports 11 distinct RF interdiction techniques, all mathematically parity-tested between Python and C++:
*   `noise` (Narrowband Noise)
*   `phase-noise` (Phase-Shifted Noise)
*   `comb` (Differential Comb)
*   `chirp` (Linear FM Chirp)
*   `ofdm` (OFDM-Shaped Noise)
*   `fhss` (Frequency Hopping Spread Spectrum Noise)
*   `confusion` (Correlator Confusion via Zadoff-Chu sequences)
*   `noise-tones` (Multiple narrowband noise pillars)
*   `cosine-tones` (Multiple pure sine wave pillars)
*   `phasor-tones` (Complex phasor tones)
*   `chunked-noise` (Swept chunked noise)
*   `rrc` (Root-Raised-Cosine Modulated Noise)
*   `fm-cosine` (Frequency Modulated Cosine)

## 3. The Air-Gapped Deployment Strategy
Because the target machine lacks internet access, development relies on a strict bundling process.
*   **`bundle_offline.sh`**: Zips the `sidekiq-sng` directory into `sidekiq_sng_v1.zip` for USB transfer.
*   **`build_on_target.sh`**: A smart compilation script executed on the air-gapped machine. It dynamically locates the runtime `libSoapySDR.so` using `ldconfig` and links against it directly, bypassing the need for missing `-dev` packages (`libsoapysdr-dev`).
*   **Vendored Headers**: To satisfy the C++ compiler without `-dev` packages, we manually reconstructed and vendored `SoapySDR/Device.hpp` and `SoapySDR/Types.hpp` directly into the project's `include/` directory.

## 4. Local AI Integration (LCC & Llama.cpp)
To reduce the "USB Sneakernet" turnaround time, we established a local AI coding assistant directly on the air-gapped machine (which features an NVIDIA Orin `nv194` or similar high-end GPU).
*   **Engine**: `llama.cpp` (`llama-server`) running locally on port `8000`.
*   **Model**: `Qwen2.5-Coder-7B-Instruct-GGUF` (Highly recommended for C++).
*   **Interface**: A local script named `lcc` (Local Claude Code) or a fallback Python chat script acts as the terminal frontend, piping `make soapy` errors directly into the local LLM for instant resolution.

## 5. Recent Technical Hurdles & Architectural Solutions

Any LLM taking over this project must understand the strict hardware constraints we recently solved:

### A. Sidekiq DMA Alignment (The "numElems" Error)
*   **Problem**: Sidekiq DMA engines will violently reject streams (or loop endlessly causing center-frequency spikes) if `device->writeStream` requests are not exact multiples of the hardware MTU (16,380 samples).
*   **Solution**: Implemented **v2.3 [STRICT DMA MODE]**. The C++ engine now pre-pads all generated waveforms to be a perfect multiple of the queried hardware MTU. The `writeStream` loop is locked to send exactly 1 MTU chunk per iteration, perfectly advancing the data pointer.

### B. VTable Segfaults (ABI Mismatch)
*   **Problem**: Vendoring a "minimal" `SoapySDR/Device.hpp` caused a Segmentation Fault. The C++ virtual function table (vtable) shifted, causing calls like `getNumChannels()` to execute random memory addresses in the pre-compiled `.so` library.
*   **Solution**: Fully reconstructed the **exact SoapySDR 0.8.0 vtable layout**, including all dummy/unused virtual functions, ensuring perfect ABI alignment with the Ubuntu 22.04 runtime libraries.

### C. Antenna Routing / Silent Ports
*   **Problem**: Channels > 0 were "silent" despite software reporting successful transmission. Sidekiq shares synthesizers and requires explicit physical port mapping.
*   **Solution**: Implemented **v2.4 [DEEP PROBE]** and **v2.5 [MASTER ENABLE]**.
    1.  The code now dynamically queries `listAntennas()` for every channel and explicitly calls `setAntenna()` using the *last* item in the list (which maps to the physical SMA, e.g., J1/J7).
    2.  The code issues `device->writeSetting(SOAPY_SDR_TX, c, "TX_EN", "true")` for every channel to forcibly wake up internal power amplifiers before streaming.

### D. FM-Cosine Bandwidth Expansion
*   **Problem**: An `fm-cosine` technique requested at 100MHz bandwidth was appearing 250MHz wide on the spectrum analyzer.
*   **Solution**: The math was flawed (calculating phase directly from the sine of time). It was rewritten to use an **Instantaneous Frequency Accumulator** (`phase_acc += 2.0 * M_PI * dev / sample_rate_hz`), ensuring the peak-to-peak frequency deviation strictly adheres to the requested `--bw`.

## 6. User Interfaces
The `sidekiq-sng` directory includes two portable Python wrappers for the C++ binary:
1.  **`sng_gui.py`**: A `tkinter` based graphical interface.
2.  **`sng_console.py`**: A robust, standard-library-only Text User Interface (TUI). This is the primary control mechanism on the air-gapped machine (which lacks `tkinter`). It features dynamic parameter prompting, rapid RF reconfiguration, and dedicated "Blink Test" buttons for ports 0-3.

## 7. Current State
*   The C++ engine successfully builds on the air-gapped target.
*   The MTU DMA logic is stable.
*   The math engines (specifically FM Cosine) are calibrated to strict spectral boundaries.
*   The user is currently validating the multi-port transmission capabilities and spectral cleanliness on an external spectrum analyzer.
