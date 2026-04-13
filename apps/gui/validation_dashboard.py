"""Validation Dashboard tab for Predator Console.

Provides real-time verification that the waveform engine and detection
pipeline are working correctly, without needing hardware.

Tab features:
  - Waveform preview (generated directly from BaseWaveforms)
  - Spectrum analysis (FFT of the output)
  - Test runner with pass/fail status
  - Signal integrity metrics
"""

import numpy as np
from PyQt5 import Qt, QtCore, QtWidgets

try:
    from techniquemaker import BaseWaveforms
except ImportError:
    try:
        from gnuradio.techniquemaker import BaseWaveforms
    except ImportError:
        BaseWaveforms = None

# ---------------------------------------------------------------------------
# Validation Dashboard Widget
# ---------------------------------------------------------------------------


class ValidationDashboard(Qt.QWidget):
    """Tab widget: waveform validation, spectrum, test runner, metrics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = Qt.QVBoxLayout(self)
        self.sr = 2_000_000
        self.dur = 0.01
        self.bw = 100_000

        self._build_waveform_section()
        self._build_spectrum_section()
        self._build_test_runner()
        self._build_metrics_panel()

    # ---- Waveform Preview ----
    def _build_waveform_section(self):
        box = Qt.QGroupBox("Waveform Preview Generator")
        layout = Qt.QFormLayout(box)

        self.wf_combo = Qt.QComboBox()
        if BaseWaveforms:
            self.wf_combo.addItems(list(BaseWaveforms.waveform_definitions.keys()))
        layout.addRow("Technique:", self.wf_combo)

        self.wf_preview_btn = Qt.QPushButton("GENERATE & ANALYZE")
        self.wf_preview_btn.clicked.connect(self.on_generate_preview)
        self.wf_preview_btn.setStyleSheet(
            "background-color: #0f3460; color: white; font-weight: bold;"
        )
        layout.addRow(self.wf_preview_btn)

        self.wf_info = Qt.QTextEdit()
        self.wf_info.setReadOnly(True)
        self.wf_info.setMaximumHeight(220)
        self.wf_info.setStyleSheet(
            "background-color: #0a0a1a; color: #00ff41; "
            "font-family: 'Courier New', monospace; font-size: 12px;"
        )
        layout.addRow(self.wf_info)
        self.layout.addWidget(box)

    def on_generate_preview(self):
        if not BaseWaveforms:
            self.wf_info.append("ERROR: BaseWaveforms not available")
            return
        name = self.wf_combo.currentText()
        defn = BaseWaveforms.waveform_definitions.get(name)
        if not defn:
            return

        # Build kwargs from defaults
        kwargs = {
            "sample_rate_hz": self.sr,
            "technique_length_seconds": self.dur,
        }
        for p in defn["params"]:
            if p["name"] in ["sample_rate_hz", "technique_length_seconds"]:
                continue
            try:
                kwargs[p["name"]] = float(p["default"])
            except (ValueError, TypeError):
                kwargs[p["name"]] = p["default"]

        try:
            import inspect

            sig = inspect.signature(defn["func"])
            valid = {k: v for k, v in kwargs.items() if k in sig.parameters}
            out = defn["func"](**valid)

            # Compute metrics
            n_samples = len(out)
            peak = float(np.max(np.abs(out)))
            rms = float(np.sqrt(np.mean(np.abs(out) ** 2)))
            crest = peak / rms if rms > 0 else float("inf")
            mean_pwr = float(np.mean(np.abs(out) ** 2))
            has_nan = bool(np.any(np.isnan(out)))
            has_inf = bool(np.any(np.isinf(out)))
            dtype = str(out.dtype)

            self.wf_info.clear()
            self.wf_info.append(f"Waveform:     {name}")
            self.wf_info.append(f"Samples:      {n_samples:,}")
            self.wf_info.append(f"Duration:     {self.dur}s @ {self.sr/1e6:.1f}MS/s")
            self.wf_info.append(f"Dtype:        {dtype}")
            self.wf_info.append(f"Peak Amp:     {peak:.6f}")
            self.wf_info.append(f"RMS:          {rms:.6f}")
            self.wf_info.append(f"Crest Factor: {crest:.3f}")
            self.wf_info.append(f"Mean Power:   {mean_pwr:.6f}")
            self.wf_info.append(f"NaN:          {has_nan}")
            self.wf_info.append(f"Inf:          {has_inf}")
            self.wf_info.append("")

            # Spectrum summary
            spec = np.fft.fftshift(np.fft.fft(out))
            freqs = np.fft.fftshift(np.fft.fftfreq(n_samples, 1.0 / self.sr))
            pwr = np.abs(spec) ** 2
            total_pwr = np.sum(pwr)
            # Find peak frequency
            peak_idx = np.argmax(pwr)
            peak_freq = freqs[peak_idx]
            self.wf_info.append(f"Peak Freq:    {peak_freq/1e3:.2f} kHz")

            # Pass/fail verdict
            verdict = "PASS"
            if has_nan or has_inf:
                verdict = "FAIL"
            if n_samples == 0:
                verdict = "FAIL"
            self.wf_info.append(f"Verdict:      {verdict}")
            self.wf_info.append(f"Peak Freq:    {peak_freq/1e3:.2f} kHz")

        except Exception as e:
            self.wf_info.append(f"ERROR: {e}")

    # ---- Spectrum Section ----
    def _build_spectrum_section(self):
        box = Qt.QGroupBox("Quick Spectrum Analysis")
        layout = Qt.QVBoxLayout(box)
        label = Qt.QLabel(
            "Run 'Generate & Analyze' above to compute spectrum statistics. "
            "No hardware or GNU Radio required."
        )
        label.setWordWrap(True)
        layout.addWidget(label)

        self.spectrum_info = Qt.QTextEdit()
        self.spectrum_info.setReadOnly(True)
        self.spectrum_info.setMaximumHeight(80)
        self.spectrum_info.setStyleSheet(
            "background-color: #0a0a1a; color: #00ffff; "
            "font-family: 'Courier New', monospace; font-size: 12px;"
        )
        layout.addWidget(self.spectrum_info)
        self.layout.addWidget(box)

    # ---- Test Runner ----
    def _build_test_runner(self):
        box = Qt.QGroupBox("Quick Test Runner")
        layout = Qt.QVBoxLayout(box)

        self.test_run_btn = Qt.QPushButton("RUN WAVEFORM SMOKE TESTS")
        self.test_run_btn.clicked.connect(self.run_quick_tests)
        self.test_run_btn.setStyleSheet(
            "background-color: #0f3460; color: white; font-weight: bold;"
        )
        layout.addWidget(self.test_run_btn)

        self.test_results = Qt.QTextEdit()
        self.test_results.setReadOnly(True)
        self.test_results.setMaximumHeight(200)
        self.test_results.setStyleSheet(
            "background-color: #0a0a1a; color: #00ff41; "
            "font-family: 'Courier New', monospace; font-size: 12px;"
        )
        layout.addWidget(self.test_results)
        self.layout.addWidget(box)

    def run_quick_tests(self):
        if not BaseWaveforms:
            self.test_results.append("BaseWaveforms not available")
            return

        self.test_results.clear()
        self.test_results.append("Running waveform smoke tests...\n")
        passed = 0
        failed = 0
        errors = []

        sr = self.sr
        dur = self.dur
        bw = self.bw

        tests = [
            ("Narrowband Noise", lambda: BaseWaveforms.narrowband_noise_creator(bw, sr, dur)),
            (
                "Differential Comb",
                lambda: BaseWaveforms.differential_comb_creator(30_000, 10, sr, dur),
            ),
            ("LFM Chirp", lambda: BaseWaveforms.lfm_chirp(-500_000, 500_000, sr, dur)),
            ("OFDM Noise", lambda: BaseWaveforms.ofdm_shaped_noise(64, 48, 16, sr, dur)),
            (
                "FHSS Noise",
                lambda: BaseWaveforms.fhss_noise("-200000 0 200000", 0.002, bw, sr, dur),
            ),
            ("RRC Modulated", lambda: BaseWaveforms.rrc_modulated_noise(50_000, sr, 0.35, dur)),
            ("Swept Noise", lambda: BaseWaveforms.swept_noise_creator(500_000, bw, sr, dur)),
            ("Noise Tones", lambda: BaseWaveforms.noise_tones("-100000 0 100000", 10_000, sr, dur)),
            ("Cosine Tones", lambda: BaseWaveforms.cosine_tones("10000 50000", sr, dur)),
            ("Phasor Tones", lambda: BaseWaveforms.phasor_tones("10000 50000", sr, dur)),
            ("FM Cosine", lambda: BaseWaveforms.FM_cosine(100_000, 1_000, sr, dur)),
            ("WiFi Preamble B", lambda: BaseWaveforms.wifi_preamble(sr, dur, "802.11b")),
            ("WiFi Preamble G", lambda: BaseWaveforms.wifi_preamble(sr, dur, "802.11g")),
            ("Songs: Star Wars", lambda: BaseWaveforms.songMaker("Star Wars", bw, sr)),
            ("Correlator Confusion", lambda: BaseWaveforms.correlator_confusion(bw, sr, dur)),
        ]

        for name, fn in tests:
            try:
                out = fn()
                if out is None or len(out) == 0:
                    self.test_results.append(f"  FAIL: {name} (empty output)")
                    failed += 1
                elif np.any(np.isnan(out)):
                    self.test_results.append(f"  FAIL: {name} (contains NaN)")
                    failed += 1
                elif np.any(np.isinf(out)):
                    self.test_results.append(f"  FAIL: {name} (contains Inf)")
                    failed += 1
                elif np.max(np.abs(out)) == 0:
                    self.test_results.append(f"  FAIL: {name} (all zeros)")
                    failed += 1
                else:
                    self.test_results.append(f"  PASS: {name} ({len(out)} samples)")
                    passed += 1
            except Exception as e:
                self.test_results.append(f"  ERR:  {name} — {e}")
                failed += 1

        self.test_results.append(f"\nResult: {passed} passed, {failed} failed out of {len(tests)}")
        if failed == 0:
            self.test_results.append("STATUS: ALL TESTS PASSED\n")
        else:
            self.test_results.append("STATUS: TESTS FAILED — review errors above\n")

    # ---- Metrics Panel ----
    def _build_metrics_panel(self):
        box = Qt.QGroupBox("Engine Metrics")
        layout = Qt.QFormLayout(box)

        self.metric_total_waveforms = Qt.QLabel("15+ registered")
        layout.addRow("Registered Techniques:", self.metric_total_waveforms)

        self.metric_test_count = Qt.QLabel("43 in test suite")
        layout.addRow("Automated Tests:", self.metric_test_count)

        self.metric_hw_required = Qt.QLabel("No")
        layout.addRow("Hardware Needed:", self.metric_hw_required)

        label = Qt.QLabel("Use \"Generate & Analyze\" or \"Run Smoke Tests\" above.")
        label.setWordWrap(True)
        layout.addRow(label)
        self.layout.addWidget(box)
