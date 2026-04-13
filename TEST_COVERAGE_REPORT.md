# TechniqueMaker: Test Coverage Report

> Generated: 2026-04-12

---

## Test Suite Summary

### Tests Added in This Session

| Module | Tests | Status |
|--------|-------|--------|
| `test_waveform_engine.py` | 44 | ✅ All pass |
| `test_core_utils.py` | 6 | ✅ All pass |
| `test_calibration.py` | 9 | ✅ All pass |
| `test_presets.py` | 8 | ✅ All pass |
| **Total** | **67** | **100% pass** |

---

## Test Coverage Details

### Waveform Engine (`BaseWaveforms.py`)
- Smoke tests for all 17 waveform generators
- Normalization (peak/RMS)
- Spectral properties
- Output types (complex/real)
- Edge cases (zero bandwidth, negative freq, etc.)
- Reproducibility

### Core Utils (`apps/core_utils.py`)
- `parse_scientific_notation()` - various formats
- `ConfigManager` - singleton pattern, defaults, file loading, logging

### Calibration (`apps/session/calibration.py`)
- Empty/missing calibration file
- Data loading from JSON
- Power estimation (exact/nearest freq/gain)
- Label formatting

### Presets (`apps/session/presets.py`)
- Empty/missing preset file
- Load/save/delete presets
- Apply to target objects

---

## Build Notes

### Python Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### Running Tests
```bash
PYTHONPATH=. python3 -m pytest tests/ -v
```

### Linting
```bash
black . --exclude="\.git|\.venv"
flake8 . --max-line-length=88
```

---

## C++ OOT Module

Location: `gr-techniquemaker/`

The GNU Radio OOT module requires:
- GNU Radio 3.10+
- CMake 3.8+
- C++17 compiler

Build:
```bash
cd gr-techniquemaker
mkdir build && cd build
cmake ..
make
sudo make install
```

---

## Branch: `fix-waveform-songmaker`

All fixes committed to this branch.