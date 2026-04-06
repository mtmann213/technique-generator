# TechniqueMaker: Project Architecture & Development Guide

> **Updated:** 2026-04-05 — Phases 1-3 completed
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

- **Dual-interdictor design**: `interdictor` (TX1) and `interdictor2` (TX2) for dual-SDR spectral stitching. Both are created in `init_blocks()`; `interdictor2` is silenced by default.
- **Waterfall has 2 inputs**: Always. When single-SDR mode, interdictor2 outputs zeros to channel 1. Don't disconnect unless you change the waterfall ninputs to 1.
- **C++ interdictor `work()`** has two paths:
  - `"Auto-Surgical"` → spectral detection + multi-target waveform synthesis
  - `"Continuous (Stream)"` → plays `d_base_waveform` in a loop
- **Waveform loading**: `update_dynamic_params()` calls `generate_and_load_waveform()` which generates waveform via BaseWaveforms and pushes to interdictor via `set_base_waveform()`
- **Jamming output**: When `d_jamming_enabled=false`, the C++ `work()` fills output with zeros and returns early

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

1. **`generate_and_load_waveform()`** must be called AFTER `interdictor` is created. The call chain is: `on_connect_toggled(true)` → `init_blocks()` → `update_dynamic_params()` → `generate_and_load_waveform()`
2. **Waveform params** are defined in `BaseWaveforms.waveform_definitions` as `{"name", "title", "type", "default"}`. The `update_dynamic_params()` loop builds `current_template_kwargs` from these, skipping `sample_rate_hz` and `technique_length_seconds` (set separately).
3. **`bandwidth_hz`** is the first positional param for `narrowband_noise_creator` — it MUST be in kwargs or the call fails.
4. **`static double manual_phase_acc`** was fixed to use instance variable (commit: `Fix: narrowband noise always visible on waterfall when TX off`)
5. **Waterfall topology** requires both inputs connected — don't remove interdictor2→waterfall unless you also change waterfall ninputs

## 5. Roadmap

See `docs/FUTURE_PLANS.md` for the original roadmap. Current priorities:
1. **Fix remaining underflows** (Phase 4)
2. **Complete flowgraph extraction** (Phase 4)
3. **CI/CD pipeline** (Phase 4)
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
