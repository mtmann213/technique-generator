r"""Headless mode runner — run the full engine without GUI for CI/testing.

Usage:
    # Basic: just run with default config and print metrics
    python -m apps.engine.headless

    # Custom config (JSON from stdin)
    python -m apps.engine.headless --config config/system_config.json

    # Run a waveform and save to file for inspection
    python -m apps.engine.headless --tech "LFM Chirp" --out chirp.bin

    # Run as server (accept commands over stdio)
    python -m apps.engine.headless --server
"""

import sys
import os
import json
import argparse
import numpy as np
from datetime import datetime

# -- Add project paths --
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_oot = os.path.join(_ROOT, "gr-techniquemaker", "python")
if _oot not in sys.path:
    sys.path.insert(0, _oot)

try:
    from techniquemaker import BaseWaveforms
except ImportError:
    from gnuradio.techniquemaker import BaseWaveforms

AVAILABLE_TECHNIQUES = list(BaseWaveforms.waveform_definitions.keys())


def generate_waveform(
    tech_name: str, sr: float = 2e6, dur: float = 0.01, **overrides
) -> np.ndarray:
    """Generate a waveform by name with optional parameter overrides."""
    defn = BaseWaveforms.waveform_definitions.get(tech_name)
    if not defn:
        raise ValueError(f"Unknown technique: {tech_name}")

    kwargs = {
        "sample_rate_hz": sr,
        "technique_length_seconds": dur,
    }
    for p in defn["params"]:
        if p["name"] in kwargs:
            continue
        try:
            kwargs[p["name"]] = float(p["default"])
        except (ValueError, TypeError):
            kwargs[p["name"]] = p["default"]

    kwargs.update(overrides)

    import inspect

    sig = inspect.signature(defn["func"])
    valid = {k: v for k, v in kwargs.items() if k in sig.parameters}
    return defn["func"](**valid)


def analyze_waveform(wf: np.ndarray, sr: float = 2e6) -> dict:
    """Compute signal integrity metrics."""
    n = len(wf)
    peak = float(np.max(np.abs(wf)))
    rms = float(np.sqrt(np.mean(np.abs(wf) ** 2)))
    crest = peak / rms if rms > 0 else float("inf")
    mean_pwr = float(np.mean(np.abs(wf) ** 2))
    peak_to_avg = 10 * np.log10(peak**2 / mean_pwr) if mean_pwr > 0 else float("inf")

    # Spectral analysis
    spec = np.fft.fftshift(np.fft.fft(wf))
    freqs = np.fft.fftshift(np.fft.fftfreq(n, 1.0 / sr))
    pwr = np.abs(spec) ** 2
    total_pwr = np.sum(pwr)
    peak_idx = np.argmax(pwr)
    peak_freq = float(freqs[peak_idx])

    # Bandwidth estimate (3-dB points from peak)
    threshold = pwr[peak_idx] * 0.5
    above_threshold = pwr >= threshold
    edges = np.where(np.diff(above_threshold.astype(int)))[0]
    bw_estimate = 0.0
    if len(edges) >= 2:
        bw_estimate = float(np.abs(freqs[edges[-1]] - freqs[edges[0]]))

    # Constellation spread (for complex signals)
    if np.iscomplexobj(wf):
        phase = np.angle(wf)
        phase_var = float(np.var(phase))
    else:
        phase_var = 0.0

    return {
        "samples": n,
        "duration_seconds": n / sr,
        "sample_rate_hz": sr,
        "peak_amplitude": peak,
        "rms": rms,
        "crest_factor": crest,
        "mean_power_w": mean_pwr,
        "peak_to_avg_db": float(peak_to_avg),
        "peak_frequency_hz": peak_freq,
        "peak_frequency_khz": peak_freq / 1e3,
        "estimated_bandwidth_hz": bw_estimate,
        "has_nan": bool(np.any(np.isnan(wf))),
        "has_inf": bool(np.any(np.isinf(wf))),
        "dtype": str(wf.dtype),
        "is_complex": bool(np.iscomplexobj(wf)),
        "phase_variance": phase_var,
    }


def print_report(report: dict, tech_name: str):
    """Pretty-print analysis report to stdout."""
    sep = "=" * 60
    print(sep)
    print(f"  Waveform Report: {tech_name}")
    print(f"  Generated: {datetime.now().isoformat()}")
    print(sep)
    print(f"  Samples:           {report['samples']:,}")
    print(f"  Duration:          {report['duration_seconds']:.6f}s")
    print(f"  Sample Rate:       {report['sample_rate_hz']/1e6:.2f} MS/s")
    print(f"  Dtype:             {report['dtype']}")
    print(f"  Is Complex:        {report['is_complex']}")
    print(sep)
    print(f"  Peak Amplitude:    {report['peak_amplitude']:.6f}")
    print(f"  RMS:               {report['rms']:.6f}")
    print(f"  Crest Factor:      {report['crest_factor']:.3f}")
    print(f"  Mean Power (W):    {report['mean_power_w']:.6f}")
    print(f"  Peak-to-Avg (dB):  {report['peak_to_avg_db']:.3f}")
    print(sep)
    print(f"  Peak Frequency:    {report['peak_frequency_khz']:.2f} kHz")
    print(f"  Est. Bandwidth:    {report['estimated_bandwidth_hz']/1e3:.2f} kHz")
    print(f"  Phase Variance:    {report['phase_variance']:.6f}")
    print(sep)
    print(f"  NaN:   {report['has_nan']}")
    print(f"  Inf:   {report['has_inf']}")

    # Verdict
    verdict = "PASS"
    if report["has_nan"] or report["has_inf"]:
        verdict = "FAIL"
    if report["peak_amplitude"] == 0:
        verdict = "FAIL"
    print(f"  VERDICT: {verdict}")
    print(sep)


def main():
    parser = argparse.ArgumentParser(description="TechniqueMaker Headless Engine")
    parser.add_argument(
        "--tech",
        type=str,
        default="Narrowband Noise",
        choices=AVAILABLE_TECHNIQUES,
        help="Technique to generate",
    )
    parser.add_argument("--out", type=str, default=None, help="Output binary file (.bin / .cf32)")
    parser.add_argument("--sr", type=float, default=2e6, help="Sample rate Hz")
    parser.add_argument("--dur", type=float, default=0.01, help="Duration (seconds)")
    parser.add_argument("--json", action="store_true", help="Output report as JSON")
    parser.add_argument("--all", action="store_true", help="Generate and test ALL techniques")
    parser.add_argument("--list", action="store_true", help="List available techniques")

    args = parser.parse_args()

    if args.list:
        print("Available techniques:")
        for name in AVAILABLE_TECHNIQUES:
            print(f"  - {name}")
        return

    if args.all:
        passed = 0
        failed = 0
        for tech in AVAILABLE_TECHNIQUES:
            try:
                wf = generate_waveform(tech, sr=args.sr, dur=args.dur)
                report = analyze_waveform(wf, args.sr)
                if report["has_nan"] or report["has_inf"] or report["peak_amplitude"] == 0:
                    print(f"  FAIL: {tech}")
                    failed += 1
                else:
                    print(f"  PASS: {tech} ({report['samples']} samples)")
                    passed += 1
            except Exception as e:
                print(f"  ERR:  {tech} - {e}")
                failed += 1
        print(f"\nResult: {passed}/{passed+failed} passed")
        return

    wf = generate_waveform(args.tech, sr=args.sr, dur=args.dur)
    report = analyze_waveform(wf, args.sr)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report, args.tech)

    if args.out:
        wf.astype(np.complex64).tofile(args.out)
        print(f"\nSaved to: {args.out}")


if __name__ == "__main__":
    main()
