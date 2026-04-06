# TechniqueMaker: Project Architecture & Development Guide

> **Updated:** 2026-04-05 — Phases 1-4 complete
> **Author:** MTT + Hermes Agent (Nous Research)

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TechniqueMaker Suite                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  apps/PredatorJammer.py  ── Main GUI (PyQt5 + GNU Radio)    │
│  apps/engine/            ── Flowgraph builder, headless (P3)│
│  apps/gui/               ── Theme system, dashboard (P2)     │
│  apps/hardware/          ── USRP discovery (P2)              │
│  apps/session/           ── Presets, calibration (P2)        │
│                                                               │
│  gr-techniquemaker/      ── C++ OOT DSP module              │
│    lib/interdictor_cpp_impl.cc  ─ Reactive interdictor       │
│    python/techniquemaker/BaseWaveforms.py ─ 17 waveforms     │
│                                                               │
│  sidekiq-sng/            ── Standalone C++ engine           │
│    WaveformEngine.cpp/hpp  ─ Core math + SoapySDR stream    │
│    main.cpp              ─ CLI entry point                  │
│                                                               │
│  tests/                  ── pytest (43 waveform tests)      │
└─────────────────────────────────────────────────────────────┘
         │              │                │
         ▼              ▼                ▼
    Ettus USRP     Signal Hound    Sidekiq S4/X4
    (UHD driver)   (SoapySDR)      (SoapySDR, DMA)
```

## 2. Key Design Decisions

- **Single-interdictor mode (default)**: Only `interdictor` is created. Waterfall has 1 input. Half the DSP load.
- **Dual-interdictor mode**: Toggling "ENABLE SECONDARY SDR" rebuilds entire flowgraph — waterfall (ninputs=2), interdictor2, all connections.
- **Conditional flowgraph**: interdictor2, sink2, waterfall channel 1, and source→interdictor2 are ALL gated on `self.dual_tx_enabled`.
- **C++ interdictor `work()`** has two paths:
  - `"Auto-Surgical"` → spectral detection + multi-target waveform synthesis
  - `"Continuous (Stream)"` → plays `d_base_waveform` in a loop
- **Waveform loading**: `update_dynamic_params()` → `generate_and_load_waveform()` → `set_base_waveform()`. Now defensive against missing params (Phase 3).
- **Jamming disabled**: C++ `work()` outputs zeros when `d_jamming_enabled=false`.

## 3. Module Structure (Post-Refactoring)

```
apps/
├── PredatorJammer.py          # Main GUI orchestrator (~1200 lines)
├── SystemCalibrator.py        # RF calibration
├── BatchGenerator.py          # Dataset generation
├── core_utils.py              # ConfigManager (singleton), logger
├── gui/
│   ├── theme.py               # Tactical theme engine, style helpers
│   └── validation_dashboard.py # Tab 4: test runner, waveform analysis
├── engine/
│   ├── flowgraph.py           # GNU Radio flowgraph builder (Phase 3)
│   └── headless.py            # CLI: generate, analyze, test waveforms
├── hardware/
│   └── usrp_discovery.py      # UHD device scanning
└── session/
    ├── presets.py             # PresetManager (save/load/apply JSON)
    └── calibration.py         # CalibrationManager (dBm estimation)
```

## 4. Known Gotchas

1. **`generate_and_load_waveform()`** is defensive: uses `setdefault` for `bandwidth_hz` and `sample_rate_hz`, scans `sig.parameters` for missing required args
2. **Waterfall ninputs**: `2 if self.dual_tx_enabled else 1`. Don't change without updating toggle/flowgraph rebuild logic
3. **`on_dual_tx_toggle` rebuilds everything**: waterfall widget, all blocks, all connections, waterfall, then restarts top_block
4. **C++ `work()`** returns zeros when `d_jamming_enabled=false` — no output but the block still processes
5. **Waveform params** defined in `BaseWaveforms.waveform_definitions` as `{"name", "title", "type", "default"}`
6. **`self.bw`** is the instance bandwidth default (usually 100e3) — used as fallback in kwargs builder

## 5. Roadmap

See `docs/FUTURE_PLANS.md` for the original roadmap. Remaining priorities:
1. **CI/CD pipeline** (GitHub Actions)
2. **Complete flowgraph extraction** (Phase 4 partial)
3. **Replace QTimer polling with Qt signals/events**
4. **4x4 MIMO support** (original roadmap)
5. **Automated PRNG cracker** (original roadmap)
6. **SigMF data replay** (original roadmap)
7. **Remote headless node** (original roadmap)

## 6. Testing Strategy

| Test | Location | Requires |
|---|---|---|
| Waveform smoke tests | `tests/test_waveform_engine.py` | numpy + scipy |
| Python/C++ parity | `tests/test_waveform_parity.py` | Compiled OOT module |
| Advanced DSP | `tests/test_advanced_dsp.py` | GNU Radio + matplotlib |
| Headless CLI | `python -m apps.engine.headless --all` | numpy + scipy |
| Validation Dashboard | GUI Tab 4 | PyQt5 + BaseWaveforms |
