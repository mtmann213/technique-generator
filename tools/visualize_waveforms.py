#!/usr/bin/env python3
"""Waveform visualization tool for TechniqueMaker.

Generate visualizations of all waveform techniques without requiring SDR hardware.
Requires matplotlib and numpy.

Usage:
    python tools/visualize_waveforms.py                    # Interactive mode
    python tools/visualize_waveforms.py --tech "LFM Chirp" # Single technique
    python tools/visualize_waveforms.py --all              # All techniques (saves PNGs)
    python tools/visualize_waveforms.py --spectrogram      # Add spectrogram to output
    python tools/visualize_waveforms.py --constellation    # Add constellation plot
    python tools/visualize_waveforms.py --list             # List available techniques
"""

import argparse
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Add project paths
_ROOT = Path(__file__).parent.parent
_oot = _ROOT / "gr-techniquemaker" / "python"
if str(_oot) not in sys.path:
    sys.path.insert(0, str(_oot))

try:
    from techniquemaker import BaseWaveforms
except ImportError:
    from gnuradio.techniquemaker import BaseWaveforms


def generate_waveform(tech_name: str, sample_rate: float = 2e6, duration: float = 0.05):
    """Generate a waveform by technique name."""
    defn = BaseWaveforms.waveform_definitions.get(tech_name)
    if not defn:
        raise ValueError(f"Unknown technique: {tech_name}")

    kwargs = {
        "sample_rate_hz": sample_rate,
        "technique_length_seconds": duration,
    }

    # Add default params
    for p in defn.get("params", []):
        if p["name"] in kwargs:
            continue
        try:
            kwargs[p["name"]] = float(p["default"])
        except (ValueError, TypeError):
            kwargs[p["name"]] = p["default"]

    # Handle techniques with special params
    if tech_name == "Differential Comb":
        kwargs["spike_count"] = 20
    if tech_name == "Chunked Noise":
        kwargs["chunks"] = 10
    if tech_name == "OFDM-Shaped Noise":
        kwargs["fft_size"] = 64
        kwargs["num_subcarriers"] = 48
    if tech_name == "Song Maker":
        kwargs["bandwidth_hz"] = 100000
    if tech_name == "GPS Spoof":
        kwargs["satellite_prn"] = 1
    if tech_name == "Repeat Jammer":
        # Provide a default dummy capture (will generate noise)
        kwargs["capture_file"] = "/dev/null"
    if tech_name == "Bluetooth Hop":
        kwargs["sample_rate_hz"] = 2e6
    if tech_name == "LoRa Disruption":
        kwargs["center_freq_hz"] = 915e6
        kwargs["bandwidth_hz"] = 125000

    import inspect

    sig = inspect.signature(defn["func"])
    valid = {k: v for k, v in kwargs.items() if k in sig.parameters}

    return defn["func"](**valid)


def plot_time_domain(ax, samples, title: str):
    """Plot time domain (real part)."""
    n = len(samples)
    time_ms = np.arange(n) / n * 1000  # arbitrary time axis
    ax.plot(time_ms, np.real(samples), linewidth=0.5, color="blue", alpha=0.8)
    ax.set_title(title)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Amplitude")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, time_ms[-1])


def plot_psd(ax, samples, sample_rate: float, title: str):
    """Plot Power Spectral Density."""
    ax.psd(samples, NFFT=1024, Fs=sample_rate / 1e6, color="red")
    ax.set_title(title)
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel("Power Spectral Density (dB/Hz)")
    ax.grid(True, alpha=0.3)


def plot_spectrogram(ax, samples, sample_rate: float, title: str):
    """Plot spectrogram (frequency over time)."""
    # Use matplotlib's specgram
    spec, freqs, t, im = ax.specgram(
        samples,
        NFFT=512,
        Fs=sample_rate / 1e6,
        cmap="viridis",
        noverlap=128,
        mode="psd",
    )
    ax.set_title(title)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Frequency (MHz)")
    # Add colorbar
    cbar = ax.figure.colorbar(im, ax=ax, label="Power (dB)")


def plot_constellation(ax, samples, title: str):
    """Plot I/Q constellation diagram."""
    if not np.iscomplexobj(samples):
        # Convert to complex if real
        samples = samples + 0j

    # Downsample for clarity if too many points
    step = max(1, len(samples) // 5000)
    i_vals = np.real(samples[::step])
    q_vals = np.imag(samples[::step])

    ax.scatter(i_vals, q_vals, s=0.5, alpha=0.5, c="blue")
    ax.set_title(title)
    ax.set_xlabel("In-Phase (I)")
    ax.set_ylabel("Quadrature (Q)")
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(-1.2, 1.2)
    ax.set_ylim(-1.2, 1.2)

    # Add unit circle reference
    theta = np.linspace(0, 2 * np.pi, 100)
    ax.plot(np.cos(theta), np.sin(theta), "k--", alpha=0.3, linewidth=0.5)


def plot_phase_portrait(ax, samples, title: str):
    """Plot phase portrait (phase trajectory)."""
    if not np.iscomplexobj(samples):
        return  # Phase only makes sense for complex signals

    # Unwrap phase
    phase = np.unwrap(np.angle(samples))
    n = len(phase)
    time_ms = np.arange(n) / n * 1000

    # Plot phase vs time
    ax.plot(time_ms, phase, linewidth=0.5, color="green", alpha=0.8)
    ax.set_title(title)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Phase (radians)")
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, time_ms[-1])


def plot_waterfall(ax, samples, sample_rate: float, title: str):
    """Plot waterfall (pseudo-3D frequency display)."""
    # Create multiple overlapping PSDs
    n_samples = len(samples)
    n_segments = 20
    segment_size = n_samples // n_segments

    # Offset each segment vertically
    for i in range(n_segments):
        start = i * segment_size
        end = start + segment_size
        segment = samples[start:end]

        # Compute PSD
        spec, freqs = (
            np.fft.fftshift(np.fft.fft(segment)),
            np.fft.fftshift(np.fft.fftfreq(segment_size, 1 / sample_rate)),
        )
        psd = 10 * np.log10(np.abs(spec) ** 2 + 1e-10)

        # Downsample freq axis for display
        step = max(1, len(freqs) // 100)
        ax.plot(freqs[::step] / 1e6, psd[::step] - i * 10, linewidth=0.3, alpha=0.7)

    ax.set_title(title)
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel("Time →")
    ax.grid(True, alpha=0.3)


def visualize_technique(
    tech_name: str,
    sample_rate: float = 2e6,
    duration: float = 0.05,
    output_dir: str = None,
    show_spectrogram: bool = False,
    show_constellation: bool = False,
    show_phase: bool = False,
    show_waterfall: bool = False,
    verbose: bool = True,
):
    """Generate and visualize a single technique."""
    if verbose:
        print(f"Generating {tech_name}...")

    try:
        samples = generate_waveform(tech_name, sample_rate, duration)
    except Exception as e:
        print(f"  ERROR generating {tech_name}: {e}")
        return None

    if samples is None or len(samples) == 0:
        print(f"  ERROR: Empty waveform for {tech_name}")
        return None

    if verbose:
        print(f"  Generated {len(samples)} samples, dtype={samples.dtype}")

    # Determine layout
    n_plots = 2  # time domain + PSD
    if show_spectrogram:
        n_plots += 1
    if show_constellation:
        n_plots += 1
    if show_phase:
        n_plots += 1

    # Create figure
    rows = (n_plots + 1) // 2
    fig, axes = plt.subplots(rows, 2, figsize=(14, 4 * rows))
    if n_plots == 1:
        axes = [axes]
    else:
        axes = axes.flatten() if hasattr(axes, "flatten") else [axes]

    idx = 0

    # Time domain
    plot_time_domain(axes[idx], samples, f"{tech_name} - Time Domain")
    idx += 1

    # PSD
    plot_psd(axes[idx], samples, sample_rate, f"{tech_name} - Power Spectral Density")
    idx += 1

    # Spectrogram
    if show_spectrogram and idx < len(axes):
        plot_spectrogram(axes[idx], samples, sample_rate, f"{tech_name} - Spectrogram")
        idx += 1

    # Constellation
    if show_constellation and idx < len(axes):
        plot_constellation(axes[idx], samples, f"{tech_name} - I/Q Constellation")
        idx += 1

    # Phase portrait
    if show_phase and idx < len(axes):
        plot_phase_portrait(axes[idx], samples, f"{tech_name} - Phase Portrait")
        idx += 1

    # Turn off unused subplots
    for ax in axes[idx:]:
        ax.set_visible(False)

    plt.tight_layout()

    # Save if output directory specified
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        safe_name = tech_name.replace(" ", "_").replace("/", "_")
        filename = os.path.join(output_dir, f"{safe_name}.png")
        plt.savefig(filename, dpi=150, bbox_inches="tight")
        if verbose:
            print(f"  Saved: {filename}")

    return fig


def visualize_all_techniques(
    sample_rate: float = 2e6,
    duration: float = 0.05,
    output_dir: str = "output/waveforms",
    show_spectrogram: bool = False,
    show_constellation: bool = False,
    show_phase: bool = False,
    show_waterfall: bool = False,
    verbose: bool = True,
):
    """Generate visualizations for all available techniques."""
    techniques = list(BaseWaveforms.waveform_definitions.keys())

    if verbose:
        print(f"\nVisualizing {len(techniques)} techniques...")
        print(f"Output directory: {output_dir}\n")

    os.makedirs(output_dir, exist_ok=True)

    passed = 0
    failed = 0

    for tech in techniques:
        try:
            fig = visualize_technique(
                tech,
                sample_rate,
                duration,
                output_dir,
                show_spectrogram,
                show_constellation,
                show_phase,
                show_waterfall,
                verbose,
            )
            if fig is not None:
                plt.close(fig)
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  FAILED {tech}: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"Output: {output_dir}/")
    print(f"{'=' * 60}\n")

    return passed, failed


def main():
    parser = argparse.ArgumentParser(
        description="Visualize TechniqueMaker waveforms without SDR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--tech",
        type=str,
        default=None,
        help="Technique to visualize (default: interactive selection)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Visualize ALL techniques and save to output/waveforms/",
    )
    parser.add_argument(
        "--list", action="store_true", help="List available techniques and exit"
    )
    parser.add_argument(
        "--sr",
        "--sample-rate",
        type=float,
        default=2e6,
        help="Sample rate in Hz (default: 2e6)",
    )
    parser.add_argument(
        "--dur",
        "--duration",
        type=float,
        default=0.05,
        help="Waveform duration in seconds (default: 0.05)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="output/waveforms",
        help="Output directory for PNGs (default: output/waveforms)",
    )
    parser.add_argument(
        "--spectrogram", action="store_true", help="Add spectrogram to visualizations"
    )
    parser.add_argument(
        "--constellation", action="store_true", help="Add I/Q constellation diagram"
    )
    parser.add_argument("--phase", action="store_true", help="Add phase portrait")
    parser.add_argument("--waterfall", action="store_true", help="Add waterfall plot")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Don't display plots (for batch processing)",
    )

    args = parser.parse_args()

    # Handle --list
    if args.list:
        techniques = list(BaseWaveforms.waveform_definitions.keys())
        print("Available techniques:")
        for i, tech in enumerate(techniques, 1):
            print(f"  {i:2d}. {tech}")
        return

    # Handle --all
    if args.all:
        visualize_all_techniques(
            sample_rate=args.sr,
            duration=args.dur,
            output_dir=args.output,
            show_spectrogram=args.spectrogram,
            show_constellation=args.constellation,
            show_phase=args.phase,
            show_waterfall=args.waterfall,
            verbose=args.verbose or True,
        )
        return

    # Single technique
    if args.tech:
        fig = visualize_technique(
            args.tech,
            sample_rate=args.sr,
            duration=args.dur,
            output_dir=args.output if args.output != "output/waveforms" else None,
            show_spectrogram=args.spectrogram,
            show_constellation=args.constellation,
            show_phase=args.phase,
            show_waterfall=args.waterfall,
            verbose=args.verbose,
        )
        if fig is not None and not args.no_show:
            plt.show()
        return

    # Interactive mode - show menu
    techniques = list(BaseWaveforms.waveform_definitions.keys())

    print("\n" + "=" * 50)
    print("  TechniqueMaker Waveform Visualizer")
    print("=" * 50)
    print("\nAvailable techniques:")
    for i, tech in enumerate(techniques, 1):
        print(f"  {i:2d}. {tech}")
    print(f"\n  {len(techniques) + 1:2d}. All techniques (save to {args.output}/)")
    print("  q.   Quit\n")

    while True:
        choice = input("Select technique number: ").strip()

        if choice.lower() == "q":
            print("Goodbye!")
            break

        try:
            idx = int(choice) - 1
            if idx == len(techniques):
                # All techniques
                visualize_all_techniques(
                    sample_rate=args.sr,
                    duration=args.dur,
                    output_dir=args.output,
                    show_spectrogram=args.spectrogram,
                    show_constellation=args.constellation,
                    show_phase=args.phase,
                    show_waterfall=args.waterfall,
                    verbose=True,
                )
            elif 0 <= idx < len(techniques):
                tech = techniques[idx]
                fig = visualize_technique(
                    tech,
                    sample_rate=args.sr,
                    duration=args.dur,
                    show_spectrogram=args.spectrogram,
                    show_constellation=args.constellation,
                    show_phase=args.phase,
                    show_waterfall=args.waterfall,
                    verbose=True,
                )
                if fig is not None:
                    plt.show()
            else:
                print("Invalid selection. Try again.")
        except ValueError:
            print("Invalid input. Enter a number or 'q'.")


if __name__ == "__main__":
    main()
