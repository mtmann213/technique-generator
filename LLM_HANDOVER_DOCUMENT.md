# TechniqueMaker: Developer Handover Document

> **Last updated:** 2026-04-05
> **Version in repo:** v2.5+ with Phase 1-3 refactoring applied

---

## Quick Start for Next LLM

1. Clone the repo and check `git log` for recent commits
2. Read this file for project context and known bugs
3. Read `docs/developer/ARCHITECTURE.md` for system design
4. Read `docs/developer/TESTING.md` for test setup

The repo has been partially refactored through **Phase 3** (see Recent Changes below). The code is committed locally but may not be pushed to origin.

---

## What This Project Is

**TechniqueMaker** is a professional-grade SIGINT / reactive RF interdiction suite for SDR hardware (Ettus USRP, Signal Hound, Epiq Sidekiq S4/X4). It detects signals in the spectrum and generates counter-waveforms to disrupt them with sub-millisecond latency.

**Dual-engine DSP architecture:**
- **Python/NumPy "Golden Set"** — `BaseWaveforms.py` for validation and prototyping
- **C++ Interdictor** — GNU Radio OOT block for real-time processing
- **C++ SNG (Sidekiq Native Generator)** — Standalone C++ engine for ultra-high bandwidth (bypasses GNU Radio)

**Key directories:**
```
apps/                          # Python GUI applications
  gui/         (Phase 2)       # Extracted theme engine + validation dashboard
  engine/      (Phase 3)       # Flowgraph builder + headless runner
  hardware/    (Phase 2)       # USRP device discovery
  session/     (Phase 2)       # Presets + calibration managers
  PredatorJammer.py            # Main tactical console (partially refactored)
  SystemCalibrator.py          # RF calibration tool
  core_utils.py                # Config management
config/                        # System configs, presets, calibration data
docs/                          # Organized documentation (Phase 1)
gr-techniquemaker/             # GNU Radio C++ OOT module
  lib/interdictor_cpp_impl.cc  # Real-time interdictor block
  python/techniquemaker/BaseWaveforms.py  # Waveform definitions
predator-cpp/                  # Native C++ Qt console
sidekiq-sng/                   # Sidekiq SNG (standalone C++ engine)
sidekiq_ai_bundle/             # Local llama.cpp (not tracked in .gitignore)
tests/                         # pytest test suite
```

---

## 15+ Waveform Techniques

| Technique | Description |
|---|---|
| Narrowband Noise | Frequency-domain noise generation |
| Differential Comb | Phase-inverted multi-tone spectral dead zones |
| LFM Chirp | Linear frequency-modulated sweep |
| OFDM-Shaped Noise | Simulated OFDM signal with cyclic prefix |
| FHSS Noise | Frequency-hopping noise |
| RRC Modulated Noise | Root-raised cosine pulse-shaped noise |
| Swept Noise | Frequency-swept noise (sawtooth/triangle) |
| Swept Phasors | Swept complex exponential tones |
| Swept Cosines | Swept real cosine tones |
| Phasor Tones | Complex exponential pillars |
| Cosine Tones | Real cosine pillars |
| Noise Tones | Narrowband noise pillars at specific frequencies |
| Chunked Noise | Shuffled frequency-chunk noise |
| Correlator Confusion | Zadoff-Chu sequences with random phase/timing |
| WiFi Preamble | 802.11b/g preamble patterns for preamble sabotage |
| FM Cosine | Instantaneous frequency-accumulator FM |
| Song Maker | Musical sequences (Star Wars, Marine Hymn, etc.) |

Each is defined in `BaseWaveforms.waveform_definitions` with parameter metadata.

---

## Known Bugs — Already Fixed

These bugs were found and fixed during the refactoring session. **Verify the fixes are in the code before continuing:**

| # | Bug | Status | Fix Details |
|---|---|---|---|
| 1 | Dead code in `TechniqueMaker.py` (unreachable lines after `return`) | **Fixed** | Removed 12 lines after `return env` |
| 2 | `narrowband_noise_creator() missing bandwidth_hz` error in `generate_and_load_waveform()` | **Needs verification** | The kwargs builder in `update_dynamic_params()` should include all params from `waveform_definitions`. Verify params are not being skipped. |
| 3 | `waterfall_sink_c(1)` topology failed | **Needs verification** | Removing `interdictor2→waterfall` connection causes GNU Radio topology failure because waterfall was created with `ninputs=2`. If you disable interdictor2, also reduce waterfall ninputs to 1. |
| 4 | Narrowband noise visible on waterfall when TX is off | **Fixed** | `on_fire_toggle()` now calls `set_jamming_enabled(False)` on both `interdictor` and `interdictor2` |
| 5 | `static double manual_phase_acc = 0` in C++ interdictor `work()` leaked phase state across ALL instances | **Fixed** | Replaced with instance member `d_manual_phase_acc` + `d_manual_phase_initialized` |
| 6 | `tx2_interdiction_enabled = True` default caused interdictor2 to always jam, even when dual_tx is off | **Fixed** | Changed to `False`, enabled via `on_dual_tx_toggle()` |
| 7 | Interdictor2 always connected to waterfall causing unnecessary DSP load → underflows | **Partially fixed** | `tx2_interdiction_enabled=False` silences output, but interdictor2 is still connected to the graph (required for waterfall 2-input topology). The C++ block outputs zeros when jamming is disabled. |

---

## Unresolved Issues / Next Steps

### High Priority
- **Underflows** — Still occurring when connecting to hardware. Root cause: running two interdictor blocks when only one is needed. Consider making interdictor2 fully optional (conditional flowgraph wiring + adaptive waterfall ninputs)
- **`generate_and_load_waveform()` kwargs** — Verify the kwargs builder properly handles all technique parameter types and that `self.current_template_kwargs` is always populated before waveform generation

### Medium Priority (Phase 4+)
- Extract `PredatorJammer.py` fully into modular components (still ~1200 lines)
- Replace `QTimer` polling (100ms) with proper Qt signals/events from the C++ block
- Implement "headless mode" in the GUI for testing without hardware (use `apps/engine/headless.py`)
- CI/CD pipeline (GitHub Actions) for automated testing
- Docker multi-stage build for smaller images
- Full parity test suite running in CI

### Low Priority
- Cleaner documentation generation (MkDocs or Sphinx from source)
- Code style enforcement (black/flake8 enforcement in CI)
- Performance profiling and optimization of the Python interdictor fallback

---

## Hardware-Specific Lessons

### Sidekiq S4/X4
- DMA alignment must be exact multiples of hardware MTU (16,380 samples)
- Must explicitly route antenna ports via `setAntenna()` using last item from `listAntennas()`
- Must write `TX_EN=true` setting to wake up power amplifiers on each channel
- Vendored headers must match exact SoapySDR 0.8.0 vtable layout (ABI mismatch → segfaults)
- Shared synthesizers require explicit port mapping

### Ettus USRP (UHD)
- B205-mini detected and configured at 20MHz clock rate (see logs)
- USB 3.0 required for high sample rates
- Register loopback test confirms device health

### Signal Hound (SoapySDR)
- VSG60A vector signal generator supported via SoapySDR
- Uses absolute dBm level control (TX level, not gain)
- `--bw` limit: 40 MSPS on Signal Hound (vs 20 MSPS on UHD)

---

## Air-Gapped Deployment

Target machine has no internet. Development cycle:
1. Build/bundle on host machine
2. Transfer via USB to air-gapped target
3. Compile on target with `build_on_target.sh` (auto-links `libSoapySDR.so`)
4. Use local llama.cpp (`llama-server` + `lcc` script) for local AI assistance
5. Target machine: NVIDIA Orin with GPU

---

## Local Build Commands

```bash
# Build GNU Radio OOT module
cd gr-techniquemaker && mkdir -p build && cd build
cmake .. && make -j$(nproc) && sudo make install && sudo ldconfig

# Or use the installer
./install.sh

# Run tests (no GNU Radio needed)
pytest tests/test_waveform_engine.py -v

# Run tests (requires OOT module)
pytest tests/test_waveform_parity.py -v

# Headless waveform generation/analysis (NEW: Phase 3)
python -m apps.engine.headless --tech "LFM Chirp" --dur 0.1
python -m apps.engine.headless --all

# Launch GUI
python apps/PredatorJammer.py
```

---

## Git Status

All changes are committed locally. Check `git log --oneline` for the full history. Recent commit subjects:
- `Fix: narrowband noise always visible on waterfall when TX off`
- `Phase 3: Flowgraph extraction, headless engine runner, unified config`
- `Phase 2: GUI overhaul with dark theme, modular architecture, and Validation Dashboard`
- `Phase 1: ...` (3 commits: dead code fix, pyproject.toml + tests, docs)

Push to origin when ready: `git push origin main`
