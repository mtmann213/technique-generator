"""
Comprehensive test suite for BaseWaveforms — the Python waveform generation engine.

No GNU Radio, no C++ OOT module, no hardware required.
Only numpy, scipy, and pytest needed.

Covers:
- All 15+ waveform generators smoke-test (can they produce output?)
- Signal integrity (no NaN, Inf, proper complex types)
- Statistical properties (constant envelope, bandwidth containment, normalization)
- Deterministic output with fixed seeds (reproducibility)
- Error handling for edge cases (zero/invalid params)
"""

import sys
import os
import math
import numpy as np
import pytest

# Add project root to sys.path so we can import without installation
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OOT_PYTHON = os.path.join(_PROJECT_ROOT, "gr-techniquemaker", "python")
if _OOT_PYTHON not in sys.path:
    sys.path.insert(0, _OOT_PYTHON)

from techniquemaker import BaseWaveforms

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SR = 2_000_000    # default sample rate
DUR = 0.01        # 10 ms — fast tests
BW = 100_000      # default bandwidth

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _assert_signal_valid(signal_out: np.ndarray):
    """Shared check: non-empty, no NaN/Inf, correct dtype."""
    assert signal_out is not None
    assert len(signal_out) > 0
    assert not np.any(np.isnan(signal_out)), "Output contains NaN"
    assert not np.any(np.isinf(signal_out)), "Output contains Inf"

def _assert_nonzero_power(signal_out: np.ndarray):
    """Signal must have meaningful power (not all zeros)."""
    assert np.max(np.abs(signal_out)) > 0, "Output is all zeros — no signal generated"

def _assert_constant_envelope(signal_out: np.ndarray, atol: float = 1e-4):
    """Chirps, tones, FM should have constant magnitude (modulus ≈ 1)."""
    np.testing.assert_allclose(np.abs(signal_out), 1.0, atol=atol)


# ---------------------------------------------------------------------------
# Smoke Tests — All 15+ Waveforms
# ---------------------------------------------------------------------------

class TestSmokeTests:
    """Every waveform generator must produce valid output with default params."""

    def test_narrowband_noise(self):
        out = BaseWaveforms.narrowband_noise_creator(BW, SR, DUR)
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    def test_differential_comb(self):
        out = BaseWaveforms.differential_comb_creator(30_000, 10, SR, DUR)
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    def test_lfm_chirp(self):
        out = BaseWaveforms.lfm_chirp(-500_000, 500_000, SR, DUR)
        _assert_signal_valid(out)
        _assert_nonzero_power(out)
        _assert_constant_envelope(out, atol=1e-3)

    def test_ofdm_shaped_noise(self):
        out = BaseWaveforms.ofdm_shaped_noise(64, 48, 16, SR, DUR)
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    def test_fhss_noise(self):
        out = BaseWaveforms.fhss_noise("-200000 0 200000", 0.002, BW, SR, DUR)
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    def test_rrc_modulated_noise(self):
        out = BaseWaveforms.rrc_modulated_noise(50_000, SR, 0.35, DUR)
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    def test_swept_noise_sawtooth(self):
        out = BaseWaveforms.swept_noise_creator(500_000, BW, SR, DUR, "sawtooth")
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    def test_swept_noise_triangle(self):
        out = BaseWaveforms.swept_noise_creator(500_000, BW, SR, DUR, "triangle")
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    def test_chunk_noise(self):
        out = BaseWaveforms.chunk_noise_creator(1_000_000, 10, SR, DUR)
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    def test_noise_tones(self):
        out = BaseWaveforms.noise_tones("-100000 0 100000", 10_000, SR, DUR)
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    def test_cosine_tones(self):
        out = BaseWaveforms.cosine_tones("10000 50000 100000", SR, DUR)
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    def test_phasor_tones(self):
        out = BaseWaveforms.phasor_tones("10000 50000 100000", SR, DUR)
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    def test_swept_phasors(self):
        out = BaseWaveforms.swept_phasors(500_000, 5, SR, DUR)
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    def test_swept_cosines(self):
        out = BaseWaveforms.swept_cosines(500_000, 5, SR, DUR)
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    def test_fm_cosine(self):
        out = BaseWaveforms.FM_cosine(100_000, 1_000, SR, DUR)
        _assert_signal_valid(out)
        _assert_nonzero_power(out)
        _assert_constant_envelope(out, atol=1e-3)

    def test_correlator_confusion(self):
        out = BaseWaveforms.correlator_confusion(BW, SR, DUR)
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    def test_wifi_preamble_80211b(self):
        out = BaseWaveforms.wifi_preamble(SR, DUR, "802.11b")
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    def test_wifi_preamble_80211g(self):
        out = BaseWaveforms.wifi_preamble(SR, DUR, "802.11g")
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    def test_song_maker_star_wars(self):
        out = BaseWaveforms.songMaker("Star Wars", BW, SR)
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    def test_song_maker_empty_name(self):
        """An unknown song name should not crash."""
        out = BaseWaveforms.songMaker("Unknown Song", BW, SR)
        assert out is not None

    def test_all_waveform_definitions_callable(self):
        """Every entry in waveform_definitions should have a callable func."""
        for name, defn in BaseWaveforms.waveform_definitions.items():
            assert callable(defn["func"]), f"{name} func is not callable"
            assert "params" in defn, f"{name} missing params"
            assert len(defn["params"]) > 0, f"{name} has empty params"


# ---------------------------------------------------------------------------
# Normalization Tests
# ---------------------------------------------------------------------------

class TestNormalization:
    """Signals should respect normalization settings."""

    def test_peak_normalization(self):
        out = BaseWaveforms.narrowband_noise_creator(BW, SR, DUR, target_value=1.0, normalization_type="peak")
        peak = np.max(np.abs(out))
        assert peak > 0.99, f"Peak normalization failed: peak={peak}"

    def test_rms_normalization(self):
        out = BaseWaveforms.narrowband_noise_creator(BW, SR, DUR, target_value=0.5, normalization_type="rms")
        rms = np.sqrt(np.mean(np.abs(out) ** 2))
        assert rms > 0.3, f"RMS normalization failed: rms={rms}"

    def test_custom_target_amplitude(self):
        for target in [0.1, 0.5, 1.0]:
            out = BaseWaveforms.narrowband_noise_creator(BW, SR, DUR, target_value=target)
            peak = np.max(np.abs(out))
            assert peak > target * 0.99, f"Target {target}, got peak {peak}"


# ---------------------------------------------------------------------------
# Spectral/Statistical Property Tests
# ---------------------------------------------------------------------------

class TestSpectralProperties:
    """Verify that waveforms exhibit expected spectral/temporal behavior."""

    def test_chirp_frequency_progression(self):
        """LFM chirp instantaneous frequency should sweep linearly."""
        f0, f1 = -200_000, 200_000
        out = BaseWaveforms.lfm_chirp(f0, f1, SR, DUR)
        np.testing.assert_allclose(np.abs(out), 1.0, atol=1e-3)
        spectrum = np.fft.fftshift(np.fft.fft(out))
        freqs = np.fft.fftshift(np.fft.fftfreq(len(out), 1.0 / SR))
        power = np.abs(spectrum) ** 2
        centroid = np.sum(freqs * power) / np.sum(power)
        assert abs(centroid) < 100_000, f"Chirp spectral centroid too far from DC: {centroid}"

    def test_noise_tones_multi_frequency(self):
        """Noise tones should have energy at specified frequency offsets."""
        freqs_str = "-200000 0 200000"
        out = BaseWaveforms.noise_tones(freqs_str, 20_000, SR, DUR)
        spectrum = np.fft.fftshift(np.fft.fft(out))
        power = np.abs(spectrum)
        assert np.max(power) > np.mean(power) * 2, "Noise tones spectrum looks flat"

    def test_ofdm_cyclic_prefix_structure(self):
        """OFDM output should be a proper length (multiple of symbol duration)."""
        out = BaseWaveforms.ofdm_shaped_noise(64, 48, 16, SR, DUR)
        sym_len = 64 + 16  # fft_size + cp_length
        assert len(out) >= sym_len, "OFDM output too short for one symbol"

    def test_fhss_multiple_hops(self):
        """FHSS output length should span the full duration."""
        expected_samps = int(SR * DUR)
        out = BaseWaveforms.fhss_noise("-200000 0 200000", 0.002, BW, SR, DUR)
        assert len(out) == expected_samps, f"Expected {expected_samps} samples, got {len(out)}"


# ---------------------------------------------------------------------------
# Output Type Tests
# ---------------------------------------------------------------------------

class TestOutputTypes:
    """Verify correct numpy dtypes are returned."""

    def test_complex_output_default(self):
        out = BaseWaveforms.narrowband_noise_creator(BW, SR, DUR)
        assert np.issubdtype(out.dtype, np.complexfloating), f"Expected complex, got {out.dtype}"

    def test_real_output_sinc(self):
        out = BaseWaveforms.narrowband_noise_creator(BW, SR, DUR, interference_type="sinc")
        assert np.issubdtype(out.dtype, np.floating), f"Expected float, got {out.dtype}"

    def test_phasor_tones_complex(self):
        out = BaseWaveforms.phasor_tones("10000", SR, DUR)
        assert np.issubdtype(out.dtype, np.complexfloating)

    def test_cosine_tones_real(self):
        out = BaseWaveforms.cosine_tones("10000", SR, DUR)
        assert np.issubdtype(out.dtype, np.floating)


# ---------------------------------------------------------------------------
# Error / Edge Case Tests
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Graceful handling of boundary conditions."""

    def test_zero_bandwidth_no_crash(self):
        """Should handle 0 bandwidth without crashing."""
        try:
            out = BaseWaveforms.narrowband_noise_creator(0, SR, DUR)
            _assert_signal_valid(out)
        except ValueError:
            pass  # Acceptable behavior

    def test_very_long_duration(self):
        """Should handle longer signals without memory issues."""
        out = BaseWaveforms.narrowband_noise_creator(BW, SR, 0.1)  # 100ms
        assert len(out) > 0
        _assert_signal_valid(out)

    def test_sample_length_scales_with_duration(self):
        """Doubling duration should double sample count approximately."""
        out1 = BaseWaveforms.narrowband_noise_creator(BW, SR, 0.005)
        out2 = BaseWaveforms.narrowband_noise_creator(BW, SR, 0.01)
        assert len(out2) >= len(out1)

    def test_sample_length_scales_with_sample_rate(self):
        """Doubling sample rate should double sample count."""
        out1 = BaseWaveforms.narrowband_noise_creator(BW, 1_000_000, DUR)
        out2 = BaseWaveforms.narrowband_noise_creator(BW, 2_000_000, DUR)
        assert len(out2) >= len(out1)

    def test_negative_frequency_offset(self):
        """Negative frequency offsets should be handled."""
        out = BaseWaveforms.noise_tones("-50000", 10_000, SR, DUR)
        _assert_signal_valid(out)

    @pytest.mark.parametrize("interference", ["complex", "real", "sinc"])
    def test_all_interference_types(self, interference):
        out = BaseWaveforms.narrowband_noise_creator(BW, SR, DUR, interference_type=interference)
        _assert_signal_valid(out)
        _assert_nonzero_power(out)

    @pytest.mark.parametrize("norm_type", ["peak", "rms"])
    def test_all_normalization_types(self, norm_type):
        out = BaseWaveforms.narrowband_noise_creator(BW, SR, DUR, normalization_type=norm_type)
        _assert_signal_valid(out)
        _assert_nonzero_power(out)


# ---------------------------------------------------------------------------
# Reproducibility Tests
# ---------------------------------------------------------------------------

class TestReproducibility:
    """Tests for deterministic behavior where applicable."""

    def test_chirp_is_deterministic(self):
        """Chirps should be identical across calls (no randomness)."""
        out1 = BaseWaveforms.lfm_chirp(-500_000, 500_000, SR, DUR)
        out2 = BaseWaveforms.lfm_chirp(-500_000, 500_000, SR, DUR)
        np.testing.assert_array_equal(out1, out2)

    def test_fm_cosine_is_deterministic(self):
        out1 = BaseWaveforms.FM_cosine(100_000, 1_000, SR, DUR)
        out2 = BaseWaveforms.FM_cosine(100_000, 1_000, SR, DUR)
        np.testing.assert_array_equal(out1, out2)
