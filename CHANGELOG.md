# Changelog: TechniqueMaker Improvements

## [2026-04-06] - Air-Gap Deployment Hardening & Sidekiq X4 Support

### 📦 Air-Gap Transfer Pipeline
- **Complete Source Bundle:** Rewrote `bundle_offline.sh` to create `techniquemaker_offline_v1.tar.gz` -- full source tree with smart exclusions (.git, build artifacts, caches)
- **Backwards Compat:** Still produces `sidekiq_sng_v1.zip` for SNG-only deployments
- **Pre-Flight Hardware Check:** Added `check_hardware.sh` -- automated verification of 12 system dependencies (OS, arch, GNU Radio, SoapySDR, SDR hardware, Python deps, Docker, OOT module)
  - Supports `--sidekiq` flag for X4/S4 focused checks
  - Supports `--usrp` flag for USRP focused checks

### 🔧 Sidekiq X4 Support
- **run_standalone.sh rewritten:** Auto-detects Sidekiq X4 via `lspci` and SoapySDR (not just `/dev/sidekiq0` S4 detection)
  - Maps `--privileged` for Docker PCIe passthrough when X4 detected
  - Also auto-detects USRP via `uhd_find_devices` and Signal Hound via `lsusb`
  - Verifies Docker image exists before launching
  - Cleans up X11 permissions on container exit
- **X4 PCIe Passthrough:** `run_standalone.sh` no longer relies on `/dev` nodes for X4 -- uses lspci + SoapySDR discovery
- **Documentation:** New Sidekiq X4 setup section in README.md with driver prerequisites, port mapping, and streaming examples

### 📝 Documentation Overhaul
- **README.md:** Expanded deployment instructions with full pipeline (bundle → check → install → build → load → launch)
- **README.md:** New Sidekiq X4 setup section (prerequisites, probe, streaming, antenna mapping, Docker notes)
- **docs/README.md:** Added links to X4 setup guide and hardware pre-flight check
- **docs/developer/SETUP.md:** Added hardware verification section before Docker deployment
- **docs/developer/ARCHITECTURE.md:** Added hardware layer table, Sidekiq X4 architecture notes, air-gap deployment architecture
- **docs/developer/TESTING.md:** Added hardware pre-flight checks section with X4 verification sequence
- **sidekiq-sng/USAGE_GUIDE.md:** Added hardware support matrix, X4 compilation notes, architecture warnings
- **LLM_HANDOVER_DOCUMENT.md:** Updated hardware lessons, new Air-Gap Deployment section
- **PROJECT_ARCHITECT_PROMPT.md:** Added air-gap deployment flow diagram, scripts reference table, X4 requirements

## [2026-04-03] - Sidekiq SNG v2.5 & Air-Gapped Local AI

### 🦅 Sidekiq-SNG Enhancements
- **Strict DMA Mode (v2.3):** Resolved Sidekiq DMA alignment errors by enforcing exact MTU chunking and padding for hardware streaming.
- **Master Enable & Antenna Routing (v2.5):** Implemented explicit `setAntenna` and `TX_EN=true` calls to reliably wake up and route signals to secondary physical SMA ports.
- **Vendored SoapySDR Headers:** Reconstructed the exact SoapySDR 0.8.0 vtable layout to fix ABI segfaults on air-gapped target machines without `-dev` packages.
- **Removed Gain Caps & Added DMA Diagnostics:** Removed artificial 30dB gain limits and added streaming heartbeat diagnostics to the terminal.
- **Corrected FM-Cosine Math:** Rewrote the FM-Cosine modulation to use an Instantaneous Frequency Accumulator, preventing bandwidth expansion/aliasing.

### 🤖 Local AI LLM Integration
- **Air-Gapped LLM Handover:** Created `LLM_HANDOVER_DOCUMENT.md` and integrated local `llama-server` (Llama.cpp) running Qwen2.5-Coder.
- **LCC (Local Claude Code):** Configured `lcc` script to pipe build errors to the local GPU-accelerated LLM for offline coding assistance.

### 🖥️ New User Interfaces
- **TUI Tactical Console:** Added `sng_console.py` for terminal-based configuration, including quick "Blink Test" buttons for all 4 ports.
- **GUI Controller:** Added `sng_gui.py` (Tkinter-based) for graphical control.
- **Smart Build Script:** Added `build_on_target.sh` to automatically locate and link `libSoapySDR.so` on air-gapped systems.

## [2026-03-30] - Automated DSP Validation & Simulation Hardening

### 🧪 Automated Testing (Task 1)
- **Math Parity Suite:** Created `tests/test_waveform_parity.py` to mathematically verify the native C++ `WaveformEngine` against the Python/NumPy "Golden Set."
- **Exposed C++ Math Core:** Updated `pybind11` bindings to allow direct Python access to the C++ waveform generation algorithms for automated validation.

### 🦅 Predator Console (Python & C++)
- **Enhanced Sweeping:** Added `Sweep Rate (Hz/s)` support to `Swept Phasors` and `Swept Cosines` in both the UI and the math engine.
- **LCG Simulation Engine:** Upgraded the "Virtual" frequency hopper to use a Linear Congruential Generator (LCG) pattern, providing a predictable (but complex) sequence for testing the PRNG Cracker.

### 🚀 Performance & Stability
- **Zero-Copy Waveforms:** Removed the slow `.tolist()` conversion in the Python UI; NumPy buffers are now passed directly to C++ memory.
- **Predictive Parity:** Ported the `predictive_tracking` PRNG cracker logic to the Python fallback block.

## [2026-03-25] - Predator-Native: High-Performance C++ Implementation
...
### 🦅 Predator-Native (C++ Application)
- **Native Qt C++ UI:** Fully implemented a standalone C++ version of the Predator console using Qt Widgets, eliminating Python GIL bottlenecks and reducing control latency.
- **Dynamic Waveform Metadata:** Implemented a C++ metadata engine that automatically generates UI controls for all 14+ jamming techniques.
- **JSON Preset System:** Added a native persistence layer to save and recall tactical configurations from `config/predator_presets_cpp.json`.
- **Integrated Hardware Discovery:** Built native UHD device scanning directly into the C++ UI for seamless hot-plugging.
- **Simulated Frequency Hopper:** Added a "Virtual" mode that spawns a realistic frequency hopping target for offline training and algorithm testing.

### 🚀 C++ Core Enhancements (Hydra Engine V2)
- **Predictive Pattern Engine:** Implemented the first stage of a PRNG sequence cracker that analyzes hop deltas and predicts future target frequencies.
- **Preamble Sabotage (Timing Attack):** Added specialized logic to the `work()` loop to interdict only the first few milliseconds of a detected burst, effectively breaking link synchronization.
- **Extended Hydra Capacity:** Optimized the multi-target synthesis loop to support up to 50 simultaneous surgical jammers.
- **Native Waveform Engine:** Ported all mathematical synthesis algorithms (LFM, FHSS, RRC Noise, Correlator Confusion) from Python/NumPy to native C++/STL.

## [2026-03-13] - Hydra Auto-Surgical & High-Speed Wideband Support
...
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
