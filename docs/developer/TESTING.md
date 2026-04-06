# Testing Guide

## Running Tests

### Waveform Engine Tests (No Dependencies)

```bash
# Run all waveform tests (numpy + scipy only, no GNU Radio)
pytest tests/test_waveform_engine.py -v

# Run with coverage
pytest tests/test_waveform_engine.py --cov=techniquemaker --cov-report=term

# Run specific test classes
pytest tests/test_waveform_engine.py::TestSmokeTests -v
pytest tests/test_waveform_engine.py::TestNormalization -v
pytest tests/test_waveform_engine.py::TestSpectralProperties -v
pytest tests/test_waveform_engine.py::TestOutputTypes -v
pytest tests/test_waveform_engine.py::TestEdgeCases -v
pytest tests/test_waveform_engine.py::TestReproducibility -v

# Run a single test
pytest tests/test_waveform_engine.py -k "test_lfm_chirp" -v
```

### Parity Tests (Requires Compiled OOT Module)

```bash
# These test Python vs C++ output parity
pytest tests/test_waveform_parity.py -v
# Requires: gr-techniquemaker built and installed
```

### DSP / Visualization Tests

```bash
# These are matplotlib-based — generate plots for visual inspection
python tests/test_advanced_dsp.py
```

## Test Coverage

The waveform engine test suite covers:

| Category | Count | What |
|---|---|---|
| Smoke Tests | 21 | Every waveform produces valid output |
| Normalization | 3 | Peak/RMS normalization correctness |
| Spectral Properties | 4 | Frequency progression, energy distribution, structure |
| Output Types | 4 | Correct numpy dtypes (complex vs real) |
| Edge Cases | 9 | Boundary conditions, error handling, parameter combinations |
| Reproducibility | 2 | Deterministic outputs where expected |
| **Total** | **43** | |

## Adding New Tests

### For New Waveform Generators

Add a smoke test in `TestSmokeTests`:

```python
def test_new_technique(self):
    out = BaseWaveforms.new_technique(bandwidth_hz=BW, sample_rate_hz=SR, technique_length_seconds=DUR)
    _assert_signal_valid(out)
    _assert_nonzero_power(out)
```

### For Parity Checks (Python vs C++)

Add to `tests/test_waveform_parity.py` by following the existing pattern.

### For Property Tests

Add to the appropriate class in `TestSpectralProperties` or create a new test class.

## Virtual Mode Testing

The Predator Console supports a "Simulated Signal Generator" mode that doesn't require hardware:

1. Launch: `python apps/PredatorJammer.py`
2. Check "Enable Simulated Signal Generator" in the Hardware tab
3. The LCG (Linear Congruential Generator) simulates a frequency-hopping target
4. Test detection, tracking, and interdiction logic without SDR hardware
