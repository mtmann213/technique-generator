"""Tests for headless CLI engine."""

import numpy as np
from apps.engine.headless import (
    generate_waveform,
    analyze_waveform,
    AVAILABLE_TECHNIQUES,
)


def test_available_techniques():
    """Test that techniques are available."""
    assert len(AVAILABLE_TECHNIQUES) > 0
    assert "Narrowband Noise" in AVAILABLE_TECHNIQUES


def test_generate_narrowband_noise():
    """Test generating narrowband noise."""
    wf = generate_waveform("Narrowband Noise", sr=2e6, dur=0.01)
    assert wf is not None
    assert len(wf) > 0
    assert wf.dtype in [np.complex64, np.complex128]


def test_generate_lfm_chirp():
    """Test generating LFM chirp."""
    wf = generate_waveform(
        "LFM Chirp", sr=2e6, dur=0.01, start_freq_hz=900e6, end_freq_hz=910e6
    )
    assert wf is not None
    assert len(wf) > 0


def test_generate_basic_techniques():
    """Test generating basic techniques that don't require extra params."""
    basic_techniques = [
        "Narrowband Noise",
        "LFM Chirp",
        "Differential Comb",
        "RRC Modulated Noise",
    ]
    for tech in basic_techniques:
        kwargs = {}
        if tech == "Differential Comb":
            kwargs = {"spike_count": 10}
        wf = generate_waveform(tech, sr=2e6, dur=0.01, **kwargs)
        assert wf is not None, f"Failed to generate {tech}"
        assert len(wf) > 0, f"Empty waveform for {tech}"


def test_generate_with_overrides():
    """Test waveform generation with parameter overrides."""
    wf = generate_waveform(
        "Narrowband Noise",
        sr=2e6,
        dur=0.01,
        bandwidth_hz=100000,
        interference_type="complex",
    )
    assert wf is not None


def test_generate_unknown_technique():
    """Test that unknown technique raises ValueError."""
    try:
        generate_waveform("Unknown Technique", sr=2e6, dur=0.01)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unknown technique" in str(e)


def test_analyze_waveform():
    """Test waveform analysis."""
    wf = generate_waveform("Narrowband Noise", sr=2e6, dur=0.01)
    metrics = analyze_waveform(wf, sr=2e6)

    # Check for expected keys (function returns these keys)
    assert "samples" in metrics
    assert "duration_seconds" in metrics
    assert "peak_frequency_hz" in metrics
    assert "crest_factor" in metrics


def test_analyze_zero_signal():
    """Test analyzing near-zero signal."""
    wf = np.zeros(1000, dtype=np.complex128)
    wf[0] = 1e-10  # Near-zero but not exactly zero
    metrics = analyze_waveform(wf, sr=2e6)

    assert "samples" in metrics


def test_short_waveform():
    """Test analyzing very short waveform."""
    wf = np.array([1.0 + 0j, 0.5 + 0.5j], dtype=np.complex128)
    metrics = analyze_waveform(wf, sr=2e6)

    assert metrics["samples"] == 2


def test_crest_factor_real_waveform():
    """Test crest factor for real-valued waveform."""
    wf = np.random.randn(1000).astype(np.float64)
    metrics = analyze_waveform(wf, sr=2e6)

    assert "crest_factor" in metrics
    # Crest factor should be >= 1 for real signals
    assert metrics["crest_factor"] >= 1.0
