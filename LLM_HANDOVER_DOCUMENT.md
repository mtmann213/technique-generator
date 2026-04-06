# TechniqueMaker: Developer Handover Document

> **Last updated:** 2026-04-05 — Phase 4 complete
> **All changes pushed to origin/main**

---

## Quick Start

1. Clone: `git clone https://github.com/mtmann213/technique-generator.git`
2. Read this file + `PROJECT_ARCHITECT_PROMPT.md` for full context
3. See `docs/developer/SETUP.md` for build/run instructions

---

## What This Project Is

**TechniqueMaker** — professional-grade SIGINT / reactive RF interdiction suite for SDR hardware (Ettus USRP, Signal Hound, Epiq Sidekiq S4/X4).

**Key directories:**
```
apps/PredatorJammer.py            # Main GUI orchestrator (~1200 lines)
apps/gui/                         # Theme engine, validation dashboard
apps/engine/                      # Flowgraph builder, headless CLI
apps/hardware/                    # USRP discovery
apps/session/                     # Presets, calibration managers
gr-techniquemaker/                # GNU Radio C++ OOT module
  lib/interdictor_cpp_impl.cc     # Reactive interdictor block
  python/techniquemaker/BaseWaveforms.py  # 17 waveform definitions
sidekiq-sng/                      # Standalone C++ engine
tests/                            # pytest suite (43 waveform tests)
```

---

## Known Bugs — All Fixed

| # | Bug | Fix | Phase |
|---|---|---|---|
| 1 | Dead code in TechniqueMaker.py | Removed 12 unreachable lines | 1 |
| 2 | `bandwidth_hz` missing in generate_and_load_waveform() | Defensive `setdefault` + `sig.parameters` scan for missing required args | 3 |
| 3 | `waterfall_sink_c(1)` topology failed | Waterfall ninputs: `2 if dual_tx_enabled else 1` | 4 |
| 4 | Narrowband noise visible when TX off | `on_fire_toggle()` now sets jamming_enabled on BOTH interdictors | 2 |
| 5 | `static double manual_phase_acc` leaked across instances | Replaced with instance member | 2 |
| 6 | `tx2_interdiction_enabled=True` caused always-on jamming | Changed to `False`, enabled via `on_dual_tx_toggle()` | 2 |
| 7 | Double interdictor load → underflows | interdictor2 ONLY created/connected when `dual_tx_enabled`; `on_dual_tx_toggle` rebuilds entire flowgraph | 4 |

---

## Architecture Decisions

- **Single-interdictor mode (default)**: Only `interdictor` is created. Waterfall has 1 input. Half the DSP load of before.
- **Dual-interdictor mode**: Toggling "ENABLE SECONDARY SDR" rebuilds the waterfall (ninputs=2), creates interdictor2, and rebuilds all connections.
- **Waveform generation**: `update_dynamic_params()` → `generate_and_load_waveform()` → `set_base_waveform()`. Now defensive against missing params.
- **C++ interdictor `work()`**: Two output modes — `"Auto-Surgical"` (detection-driven) and `"Continuous (Stream)"` (waveform loop).
- **Jamming disabled**: C++ block fills output with zeros and returns early when `d_jamming_enabled=false`.

---

## Hardware Lessons

### Sidekiq S4/X4
- DMA alignment: exact multiples of 16,380 samples
- Antenna routing: must use `setAntenna()` with last item from `listAntennas()`
- Must write `TX_EN=true` to wake up power amps
- Vendored headers must match exact SoapySDR 0.8.0 vtable

### Ettus USRP (UHD)
- B205-mini runs at 20MHz clock rate
- USB 3.0 required for high sample rates
- `find_usrps()` for device discovery

### Signal Hound (SoapySDR)
- VSG60A via SoapySDR, absolute dBm control
- BW limit: 40 MSPS (vs 20 MSPS on UHD)

---

## Build & Run

```bash
# Build OOT module
cd gr-techniquemaker && mkdir -p build && cd build
cmake .. && make -j$(nproc) && sudo make install && sudo ldconfig

# Tests (no hardware needed)
pytest tests/test_waveform_engine.py -v

# Headless waveform analysis
python -m apps.engine.headless --tech "LFM Chirp" --dur 0.1
python -m apps.engine.headless --all

# Launch GUI
python apps/PredatorJammer.py
```

---

## Git Status

All changes pushed to origin/main. Full commit history:

```
Phase 4: Eliminate double DSP load to fix underflows
Update LLM handover docs for future sessions
Fix: narrowband noise always visible on waterfall when TX off
Phase 3: Flowgraph extraction, headless engine runner, unified config
Phase 2: GUI overhaul with dark theme, modular architecture, and Validation Dashboard
Phase 1: Consolidate documentation structure
Phase 1: Add pyproject.toml and comprehensive test harness
Phase 1: Fix dead code and expand .gitignore
```
