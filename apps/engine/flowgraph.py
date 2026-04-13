"""GNU Radio flowgraph builder — extracted from PredatorJammer.init_blocks().

This module builds the complete GNURadio flowgraph:
  source → interdictor → sink
          ↘ display_mixer → waterfall
          ↘ file_sink (optional)

Separates DSP/wiring concerns from GUI/Hardware concerns.
"""

import time
import logging
import numpy as np

try:
    from gnuradio import gr, uhd, blocks, analog, soapy
except ImportError:
    gr = uhd = blocks = analog = soapy = None

logger = logging.getLogger("TechniqueMaker.engine")


class FlowgraphConfig:
    """Immutable config for flowgraph construction."""

    def __init__(self, **kwargs):
        self.serial = kwargs.get("serial", None)
        self.secondary_serial = kwargs.get("secondary_serial", None)
        self.samp_rate = kwargs.get("samp_rate", 2e6)
        self.center_freq = kwargs.get("center_freq", 915e6)
        self.tx2_freq = kwargs.get("tx2_freq", 935e6)
        self.rx_gain = kwargs.get("rx_gain", 40)
        self.tx_gain = kwargs.get("tx_gain", 50)
        self.tx_level = kwargs.get("tx_level", -10.0)
        self.tx_sink_type = kwargs.get("tx_sink_type", "UHD")
        self.sh_serial = kwargs.get("sh_serial", "")
        self.dual_tx_enabled = kwargs.get("dual_tx_enabled", False)
        self.sim_mode = kwargs.get("sim_mode", False)
        self.template = kwargs.get("template", "Narrowband Noise")
        self.tx2_template = kwargs.get("tx2_template", "Narrowband Noise")
        self.bw = kwargs.get("bw", 100e3)
        self.threshold = kwargs.get("threshold", -45)
        self.dwell = kwargs.get("dwell", 400)
        self.num_targets = kwargs.get("num_targets", 1)
        self.tx2_targets = kwargs.get("tx2_targets", 1)
        self.tx2_threshold = kwargs.get("tx2_threshold", -45)
        self.manual_mode = kwargs.get("manual_mode", False)
        self.manual_freq = kwargs.get("manual_freq", 0.0)
        self.interdiction_enabled = kwargs.get("interdiction_enabled", True)
        self.tx2_interdiction_enabled = kwargs.get("tx2_interdiction_enabled", True)
        self.adaptive_bw = kwargs.get("adaptive_bw", False)
        self.preamble_sabotage = kwargs.get("preamble_sabotage", False)
        self.sabotage_duration = kwargs.get("sabotage_duration", 20.0)
        self.clock_pull = kwargs.get("clock_pull", 0.0)
        self.stutter_enabled = kwargs.get("stutter_enabled", False)
        self.stutter_clean = kwargs.get("stutter_clean", 3)
        self.stutter_burst = kwargs.get("stutter_burst", 1)
        self.stutter_randomize = kwargs.get("stutter_randomize", False)
        self.frame_dur = kwargs.get("frame_dur", 40.0)
        self.hydra_auto_surgical = kwargs.get("hydra_auto_surgical", False)
        self.sticky_denial = kwargs.get("sticky_denial", False)
        self.look_through_ms = kwargs.get("look_through_ms", 10.0)
        self.jam_cycle_ms = kwargs.get("jam_cycle_ms", 90.0)


class Flowgraph:
    """Builds and manages the GNURadio top_block flowgraph.

    Usage:
        fg = Flowgraph(config)
        fg.build()        # creates blocks and connects them
        flowgraph = fg.top_block  # a gr.top_block instance
        flowgraph.start()
        # later:
        flowgraph.stop()
        flowgraph.wait()
    """

    def __init__(self, config: FlowgraphConfig):
        self.config = config
        self.top_block = None
        self.source = None
        self.interdictor = None
        self.interdictor2 = None
        self.sink = None
        self.sink2 = None
        self.file_sink = None
        self.sim_src = None
        self.mixer = None
        self.display_mixer = None
        self.waterfall_sink = None

    def build(self, top_block: "gr.top_block"):
        """Build all blocks and connect them into the given top_block."""
        self.top_block = top_block
        tb = top_block

        # 1. Source
        self._build_source(tb)

        # 2. Interdictor blocks (C++ with Python fallback)
        self._build_interdictors()

        # 3. Sinks
        self._build_sinks(tb)

        # 4. Display mixing
        self._build_display(tb)

        # 5. Apply sticky/look-through settings
        self._apply_advanced_settings()

    def _build_source(self, tb):
        """Build the RX source (hardware or noise source for offline)."""
        cfg = self.config

        if cfg.sim_mode:
            # Hardware + simulation tone
            self.source = uhd.usrp_source(
                device_addr=f"serial={cfg.serial}",
                stream_args=uhd.stream_args(cpu_format="fc32", args="", channels=[0]),
            )
            self.source.set_samp_rate(cfg.samp_rate)
            self.source.set_center_freq(cfg.center_freq, 0)
            self.source.set_gain(cfg.rx_gain, 0)

            self.sim_src = analog.sig_source_c(cfg.samp_rate, analog.GR_COS_WAVE, 0, 0.5, 0)
            self.mixer = blocks.add_cc()
            tb.connect(self.source, (self.mixer, 0))
            tb.connect(self.sim_src, (self.mixer, 1))
        elif cfg.serial:
            # Real hardware
            self.source = uhd.usrp_source(
                device_addr=f"serial={cfg.serial}",
                stream_args=uhd.stream_args(cpu_format="fc32", args="", channels=[0]),
            )
            self.source.set_samp_rate(cfg.samp_rate)
            self.source.set_center_freq(cfg.center_freq, 0)
            self.source.set_gain(cfg.rx_gain, 0)
        else:
            # Offline / virtual mode — just noise
            self.source = analog.noise_source_c(analog.GR_GAUSSIAN, 0.001, 0)

    def _build_interdictors(self):
        """Build primary and secondary interdictor blocks."""
        cfg = self.config
        output_mode = "Auto-Surgical" if cfg.hydra_auto_surgical else "Continuous (Stream)"

        try:
            from gnuradio.techniquemaker import interdictor_cpp

            kwargs = dict(
                technique=cfg.template,
                sample_rate_hz=cfg.samp_rate,
                bandwidth_hz=cfg.bw,
                reactive_threshold_db=cfg.threshold,
                reactive_dwell_ms=cfg.dwell,
                num_targets=cfg.num_targets,
                manual_mode=cfg.manual_mode,
                manual_freq=cfg.manual_freq,
                jamming_enabled=cfg.interdiction_enabled,
                adaptive_bw=cfg.adaptive_bw,
                preamble_sabotage=cfg.preamble_sabotage,
                sabotage_duration_ms=cfg.sabotage_duration,
                clock_pull_drift_hz_s=cfg.clock_pull,
                stutter_enabled=cfg.stutter_enabled,
                stutter_clean_count=cfg.stutter_clean,
                stutter_burst_count=cfg.stutter_burst,
                stutter_randomize=cfg.stutter_randomize,
                frame_duration_ms=cfg.frame_dur,
                output_mode=output_mode,
            )
            self.interdictor = interdictor_cpp(**kwargs)

            kwargs2 = kwargs.copy()
            kwargs2.update(
                dict(
                    technique=cfg.tx2_template,
                    reactive_threshold_db=cfg.tx2_threshold,
                    num_targets=cfg.tx2_targets,
                    manual_freq=0.0,
                    jamming_enabled=cfg.tx2_interdiction_enabled,
                    output_mode="Continuous (Stream)",
                )
            )
            self.interdictor2 = interdictor_cpp(**kwargs2)

        except ImportError:
            from gnuradio.techniquemaker import techniquepdu

            kwargs = dict(
                technique="Reactive Jammer",
                warhead_technique=cfg.template,
                sample_rate_hz=cfg.samp_rate,
                bandwidth_hz=cfg.bw,
                reactive_threshold_db=cfg.threshold,
                reactive_dwell_ms=cfg.dwell,
                num_targets=cfg.num_targets,
                manual_mode=cfg.manual_mode,
                manual_freq=cfg.manual_freq,
                jamming_enabled=cfg.interdiction_enabled,
                adaptive_bw=cfg.adaptive_bw,
                preamble_sabotage=cfg.preamble_sabotage,
                sabotage_duration_ms=cfg.sabotage_duration,
                clock_pull_drift_hz_s=cfg.clock_pull,
                stutter_enabled=cfg.stutter_enabled,
                stutter_clean_count=cfg.stutter_clean,
                stutter_burst_count=cfg.stutter_burst,
                stutter_randomize=cfg.stutter_randomize,
                frame_duration_ms=cfg.frame_dur,
                output_mode=output_mode,
            )
            self.interdictor = techniquepdu(**kwargs)

            kwargs2 = kwargs.copy()
            kwargs2.update(
                dict(
                    warhead_technique=cfg.tx2_template,
                    reactive_threshold_db=cfg.tx2_threshold,
                    num_targets=cfg.tx2_targets,
                    manual_freq=0.0,
                    jamming_enabled=cfg.tx2_interdiction_enabled,
                    output_mode="Continuous (Stream)",
                )
            )
            self.interdictor2 = techniquepdu(**kwargs2)

    def _build_sinks(self, tb):
        """Build TX sink(s) for primary and secondary SDRs."""
        cfg = self.config

        # Primary TX sink
        try:
            if cfg.tx_sink_type == "UHD" and cfg.serial:
                self.sink = uhd.usrp_sink(
                    device_addr=f"serial={cfg.serial}",
                    stream_args=uhd.stream_args(cpu_format="fc32", args="", channels=[0]),
                )
                self.sink.set_samp_rate(cfg.samp_rate)
                self.sink.set_center_freq(cfg.center_freq, 0)
                self.sink.set_gain(cfg.tx_gain, 0)
                tb.connect(self.interdictor, self.sink)

            elif cfg.tx_sink_type == "SoapySDR":
                driver_str = f"driver=vsg60,serial={cfg.sh_serial}"
                self.sink = soapy.sink(driver_str, "fc32", 1, "", "", [""], [""])
                self.sink.set_sample_rate(0, cfg.samp_rate)
                self.sink.set_frequency(0, cfg.center_freq)
                self.sink.set_gain(0, cfg.tx_level)
                tb.connect(self.interdictor, self.sink)

            elif cfg.tx_sink_type == "Sidekiq":
                self.sink = soapy.sink("driver=sidekiq", "fc32", 1, "", "", [""], [""])
                self.sink.set_sample_rate(0, cfg.samp_rate)
                self.sink.set_frequency(0, cfg.center_freq)
                self.sink.set_gain(0, cfg.tx_level)
                tb.connect(self.interdictor, self.sink)

            else:
                # No hardware — null sink
                self.sink = blocks.null_sink(gr.sizeof_gr_complex)
                tb.connect(self.interdictor, self.sink)
        except Exception as e:
            logger.error(f"Primary sink failed: {e}")
            self.sink = blocks.null_sink(gr.sizeof_gr_complex)
            tb.connect(self.interdictor, self.sink)

        # Secondary TX sink
        if (
            cfg.dual_tx_enabled
            and cfg.secondary_serial
            and cfg.serial
            and cfg.secondary_serial != cfg.serial
        ):
            logger.info(f"Staging Secondary SDR {cfg.secondary_serial}...")
            time.sleep(2.0)
            try:
                self.sink2 = uhd.usrp_sink(
                    device_addr=f"serial={cfg.secondary_serial}",
                    stream_args=uhd.stream_args(cpu_format="fc32", args="", channels=[0]),
                )
                self.sink2.set_samp_rate(cfg.samp_rate)
                self.sink2.set_center_freq(cfg.tx2_freq, 0)
                self.sink2.set_gain(cfg.tx_gain, 0)
                tb.connect(self.interdictor2, self.sink2)
                logger.info(f"Secondary Warhead deployed")
            except Exception as e:
                logger.error(f"Secondary sink failed: {e}")
                self.sink2 = blocks.null_sink(gr.sizeof_gr_complex)
                tb.connect(self.interdictor2, self.sink2)
        else:
            self.sink2 = blocks.null_sink(gr.sizeof_gr_complex)
            tb.connect(self.interdictor2, self.sink2)

        # File sink for session recording
        self.file_sink = blocks.file_sink(gr.sizeof_gr_complex, "session.bin", False)
        self.file_sink.set_unbuffered(True)

    def _build_display(self, tb):
        """Mix source + interdictor output for waterfall display."""
        cfg = self.config

        if cfg.sim_mode:
            final_source = self.mixer
        else:
            final_source = self.source

        self.display_mixer = blocks.add_cc()
        tb.connect(final_source, (self.display_mixer, 0))
        tb.connect(self.interdictor, (self.display_mixer, 1))
        tb.connect(final_source, self.interdictor)
        tb.connect(final_source, self.interdictor2)
        # Waterfall connections handled by UI layer (needs Qt widget ref)

    def _apply_advanced_settings(self):
        """Apply sticky denial, look-through, and jam cycle settings."""
        cfg = self.config

        if hasattr(self.interdictor, "set_sticky_denial"):
            self.interdictor.set_sticky_denial(cfg.sticky_denial)
        if hasattr(self.interdictor, "set_targets") and cfg.sticky_denial:
            self.interdictor.set_targets([])
        if hasattr(self.interdictor, "set_look_through_ms"):
            self.interdictor.set_look_through_ms(cfg.look_through_ms)
        if hasattr(self.interdictor, "set_jam_cycle_ms"):
            self.interdictor.set_jam_cycle_ms(cfg.jam_cycle_ms)

    def set_waveform(self, interdictor_idx, waveform_array):
        """Set base waveform on an interdictor block."""
        target = self.interdictor if interdictor_idx == 0 else self.interdictor2
        if target and hasattr(target, "set_base_waveform"):
            target.set_base_waveform(np.array(waveform_array, dtype=np.complex64))

    def set_technique(self, interdictor_idx, technique_name):
        """Change the technique on a live interdictor."""
        target = self.interdictor if interdictor_idx == 0 else self.interdictor2
        if target and hasattr(target, "set_technique"):
            target.set_technique(technique_name)

    def set_jamming_enabled(self, enabled):
        if self.interdictor:
            self.interdictor.set_jamming_enabled(enabled)
        if self.interdictor2:
            self.interdictor2.set_jamming_enabled(enabled)

    def get_targets(self):
        """Get currently tracked targets from primary interdictor."""
        if self.interdictor and hasattr(self.interdictor, "get_targets"):
            return self.interdictor.get_targets()
        return []
