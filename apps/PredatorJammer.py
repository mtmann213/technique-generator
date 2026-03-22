#!/usr/bin/env python3
import numpy as np
from gnuradio import gr, uhd, qtgui, blocks
from gnuradio.fft import window
from PyQt5 import Qt, QtCore, QtWidgets
import sys
import json
import time
import signal
import sip
import os
from techniquemaker import techniquepdu, BaseWaveforms
from core_utils import ConfigManager, parse_scientific_notation

class PredatorJammer(gr.top_block, Qt.QWidget):
    def __init__(self):
        gr.top_block.__init__(self, "Predator Reactive Analysis Console")
        Qt.QWidget.__init__(self)
        
        self.config_manager = ConfigManager()
        self.sys_logger = self.config_manager.get_logger()
        
        # Hardware state
        self.serial = None
        self.hardware_connected = False
        
        # Load defaults from config
        default_serial = self.config_manager.get("hardware", "tx_usrp_serial", "34573DD")
        self.samp_rate = self.config_manager.get("hardware", "default_sample_rate_hz", 2e6)
        self.center_freq = self.config_manager.get("hardware", "default_center_freq_hz", 915e6)
        self.rx_gain = self.config_manager.get("rf_defaults", "rx_gain", 40)
        self.tx_gain = self.config_manager.get("rf_defaults", "tx_gain", 50)
        
        self.setWindowTitle("Predator Reactive Analysis Console")

        # --- Parameters ---
        self.target_level = 0.5
        self.threshold = -45  
        self.bw = 100e3
        self.dwell = 400
        self.template = 'Narrowband Noise'
        self.num_targets = 1
        self.manual_mode = False
        self.manual_freq = 0.0
        self.interdiction_enabled = True
        self.adaptive_bw = False
        self.preamble_sabotage = False
        self.sabotage_duration = 20.0
        self.clock_pull = 0.0
        self.stutter_enabled = False
        self.stutter_clean = 3
        self.stutter_burst = 1
        self.stutter_randomize = False
        self.frame_dur = 40.0
        self.hydra_auto_surgical = False
        self.is_recording = False
        self.presets = {}
        self.preset_file = "config/predator_presets.json"
        self.cal_data = {}
        self.load_calibration()

        # --- Main Layout ---
        self.layout = Qt.QVBoxLayout()
        self.setLayout(self.layout)

        # --- 1. Status Display ---
        self.label = Qt.QLabel("OFFLINE (VIRTUAL MODE)")
        self.label.setStyleSheet("font-size: 24px; font-weight: bold; color: #555; background-color: black; padding: 10px; border: 2px solid #333;")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(self.label)

        # --- 2. Split Layout ---
        self.main_split = Qt.QHBoxLayout()
        self.layout.addLayout(self.main_split)

        # --- LEFT Panel ---
        self.scroll = QtWidgets.QScrollArea()
        self.scroll_content = Qt.QWidget()
        self.scroll_layout = Qt.QVBoxLayout(self.scroll_content)
        self.scroll.setWidgetResizable(True); self.scroll.setFixedWidth(350)
        self.scroll.setWidget(self.scroll_content)
        self.main_split.addWidget(self.scroll)

        # Hardware Discovery
        hw_disc_box = Qt.QGroupBox("Hardware Discovery")
        hw_disc_grid = Qt.QGridLayout(); hw_disc_box.setLayout(hw_disc_grid)
        self.serial_combo = Qt.QComboBox()
        self.serial_combo.setEditable(True)
        self.serial_combo.addItem(default_serial)
        hw_disc_grid.addWidget(Qt.QLabel("USRP Serial:"), 0, 0)
        hw_disc_grid.addWidget(self.serial_combo, 0, 1)
        
        self.scan_btn = Qt.QPushButton("SCAN DEVICES")
        self.scan_btn.clicked.connect(self.on_scan_clicked)
        hw_disc_grid.addWidget(self.scan_btn, 1, 0)
        
        self.connect_btn = Qt.QPushButton("CONNECT")
        self.connect_btn.setCheckable(True)
        self.connect_btn.setStyleSheet("background-color: #005; color: white; font-weight: bold;")
        self.connect_btn.toggled.connect(self.on_connect_toggled)
        hw_disc_grid.addWidget(self.connect_btn, 1, 1)
        self.scroll_layout.addWidget(hw_disc_box)

        # Session & Presets
        session_box = Qt.QGroupBox("Session & Presets")
        session_grid = Qt.QGridLayout(); session_box.setLayout(session_grid)
        self.fire_btn = Qt.QPushButton("CEASE OUTPUT"); self.fire_btn.setCheckable(True); self.fire_btn.setStyleSheet("background-color: #050; color: white; font-weight: bold; height: 35px;")
        self.fire_btn.toggled.connect(self.on_fire_toggle); session_grid.addWidget(self.fire_btn, 0, 0, 1, 2)
        self.preset_combo = Qt.QComboBox(); self.preset_combo.currentTextChanged.connect(self.load_selected_preset); session_grid.addWidget(Qt.QLabel("Preset:"), 1, 0); session_grid.addWidget(self.preset_combo, 1, 1)
        self.save_btn = Qt.QPushButton("Save New"); self.save_btn.clicked.connect(self.save_current_preset); session_grid.addWidget(self.save_btn, 2, 0)
        self.del_btn = Qt.QPushButton("Delete"); self.del_btn.clicked.connect(self.delete_current_preset); session_grid.addWidget(self.del_btn, 2, 1)
        self.record_btn = Qt.QPushButton("LOG SESSION"); self.record_btn.setCheckable(True); self.record_btn.setStyleSheet("background-color: #333; color: white;"); self.record_btn.toggled.connect(self.on_record_toggle); session_grid.addWidget(self.record_btn, 3, 0, 1, 2)
        self.scroll_layout.addWidget(session_box)

        # Tracking & Protocol
        target_box = Qt.QGroupBox("Tracking & Protocol")
        target_grid = Qt.QGridLayout(); target_box.setLayout(target_grid)
        self.auto_radio = Qt.QRadioButton("Auto Track"); self.auto_radio.setChecked(True); self.auto_radio.toggled.connect(self.on_mode_change); self.manual_radio = Qt.QRadioButton("Manual Offset")
        target_grid.addWidget(self.auto_radio, 0, 0); target_grid.addWidget(self.manual_radio, 0, 1)
        
        self.hydra_cb = Qt.QCheckBox("Hydra Auto-Surgical Comb"); self.hydra_cb.toggled.connect(self.on_hydra_toggle); target_grid.addWidget(self.hydra_cb, 1, 0, 1, 2)

        self.manual_slider = Qt.QSlider(QtCore.Qt.Horizontal); self.manual_slider.setRange(-1000000, 1000000); self.manual_slider.setEnabled(False); self.manual_slider.valueChanged.connect(self.on_manual_freq_change); self.manual_label = Qt.QLabel("Offset: 0 kHz"); target_grid.addWidget(self.manual_label, 2, 0); target_grid.addWidget(self.manual_slider, 2, 1)
        
        # Mode Selectors
        self.adapt_cb = Qt.QCheckBox("Adaptive Bandwidth Sculpting"); self.adapt_cb.toggled.connect(self.on_adapt_toggle); target_grid.addWidget(self.adapt_cb, 3, 0, 1, 2)
        self.sab_cb = Qt.QCheckBox("Preamble Sabotage (Invisible)"); self.sab_cb.toggled.connect(self.on_sab_toggle); target_grid.addWidget(self.sab_cb, 4, 0, 1, 2)
        self.stutter_cb = Qt.QCheckBox("Stability Frame Stutter"); self.stutter_cb.toggled.connect(self.on_stutter_toggle); target_grid.addWidget(self.stutter_cb, 5, 0, 1, 2)

        # Parameters
        self.sab_input = Qt.QLineEdit(str(self.sabotage_duration)); self.sab_input.editingFinished.connect(self.on_sab_duration_change); target_grid.addWidget(Qt.QLabel("Sabotage (ms):"), 6, 0); target_grid.addWidget(self.sab_input, 6, 1)
        self.stutter_clean_input = Qt.QLineEdit(str(self.stutter_clean)); self.stutter_clean_input.editingFinished.connect(self.on_stutter_clean_change); target_grid.addWidget(Qt.QLabel("Clean Frames:"), 7, 0); target_grid.addWidget(self.stutter_clean_input, 7, 1)
        self.stutter_burst_input = Qt.QLineEdit(str(self.stutter_burst)); self.stutter_burst_input.editingFinished.connect(self.on_stutter_burst_change); target_grid.addWidget(Qt.QLabel("Burst Frames:"), 8, 0); target_grid.addWidget(self.stutter_burst_input, 8, 1)
        self.stutter_rand_cb = Qt.QCheckBox("Randomize Clean Count"); self.stutter_rand_cb.toggled.connect(self.on_stutter_rand_toggle); target_grid.addWidget(self.stutter_rand_cb, 9, 0, 1, 2)
        self.frame_input = Qt.QLineEdit(str(self.frame_dur)); self.frame_input.editingFinished.connect(self.on_frame_dur_change); target_grid.addWidget(Qt.QLabel("Frame Dur (ms):"), 10, 0); target_grid.addWidget(self.frame_input, 10, 1)
        
        target_grid.addWidget(Qt.QLabel("Clock-Pull (Hz/s):"), 11, 0); self.pull_input = Qt.QLineEdit(str(self.clock_pull)); self.pull_input.editingFinished.connect(self.on_pull_input_change); target_grid.addWidget(self.pull_input, 11, 1)
        self.targets_label = Qt.QLabel(f"Max Targets: {self.num_targets}"); self.targets_slider = Qt.QSlider(QtCore.Qt.Horizontal); self.targets_slider.setRange(1, 16); self.targets_slider.setValue(self.num_targets); self.targets_slider.valueChanged.connect(self.on_targets_change); target_grid.addWidget(self.targets_label, 12, 0); target_grid.addWidget(self.targets_slider, 12, 1)
        self.thresh_slider = Qt.QSlider(QtCore.Qt.Horizontal); self.thresh_slider.setRange(-120, 0); self.thresh_slider.setValue(-45); self.thresh_slider.valueChanged.connect(self.on_threshold_change); self.thresh_label = Qt.QLabel("Thresh: -45 dB"); target_grid.addWidget(self.thresh_label, 13, 0); target_grid.addWidget(self.thresh_slider, 13, 1)
        
        # Sticky Denial & Look-through
        self.sticky_cb = Qt.QCheckBox("Persistent Channel Denial"); self.sticky_cb.toggled.connect(self.on_sticky_toggle); target_grid.addWidget(self.sticky_cb, 14, 0, 1, 2)
        self.reset_denial_btn = Qt.QPushButton("RESET DENIAL GRID"); self.reset_denial_btn.clicked.connect(self.on_reset_denial); self.reset_denial_btn.setStyleSheet("background-color: #500; color: white;"); target_grid.addWidget(self.reset_denial_btn, 15, 0, 1, 2)
        
        self.look_input = Qt.QLineEdit("10.0"); self.look_input.editingFinished.connect(self.on_look_change); target_grid.addWidget(Qt.QLabel("Look-thru (ms):"), 16, 0); target_grid.addWidget(self.look_input, 16, 1)
        self.cycle_input = Qt.QLineEdit("90.0"); self.cycle_input.editingFinished.connect(self.on_jam_cycle_change); target_grid.addWidget(Qt.QLabel("Jam Cycle (ms):"), 17, 0); target_grid.addWidget(self.cycle_input, 17, 1)
        
        self.scroll_layout.addWidget(target_box)

        # Template Selection
        template_box = Qt.QGroupBox("Signal Template"); template_layout = Qt.QVBoxLayout(); template_box.setLayout(template_layout)
        self.template_combo = Qt.QComboBox(); self.template_combo.addItems(list(BaseWaveforms.waveform_definitions.keys())); self.template_combo.currentTextChanged.connect(self.on_template_change); template_layout.addWidget(self.template_combo); self.scroll_layout.addWidget(template_box)
        self.param_group = Qt.QGroupBox("Template Parameters"); self.param_layout = Qt.QFormLayout(); self.param_group.setLayout(self.param_layout); self.scroll_layout.addWidget(self.param_group)

        # Hardware
        hw_box = Qt.QGroupBox("Hardware Controls"); hw_layout = Qt.QFormLayout(); hw_box.setLayout(hw_layout)
        self.rx_gain_slider = Qt.QSlider(QtCore.Qt.Horizontal); self.rx_gain_slider.setRange(0, 76); self.rx_gain_slider.setValue(40); self.rx_gain_slider.valueChanged.connect(self.on_rx_gain_change); hw_layout.addRow("RX Gain", self.rx_gain_slider)
        self.tx_gain_slider = Qt.QSlider(QtCore.Qt.Horizontal); self.tx_gain_slider.setRange(0, 89); self.tx_gain_slider.setValue(50); self.tx_gain_slider.valueChanged.connect(self.on_tx_gain_change); hw_layout.addRow("TX Gain", self.tx_gain_slider)
        
        self.cal_label = Qt.QLabel("Est. Output: --- dBm")
        self.cal_label.setStyleSheet("color: cyan; font-weight: bold;")
        hw_layout.addRow(self.cal_label)
        self.scroll_layout.addWidget(hw_box)

        # Tuning
        freq_box = Qt.QGroupBox("Radio Tuning"); freq_layout = Qt.QGridLayout(); freq_box.setLayout(freq_layout)
        freq_layout.addWidget(Qt.QLabel("Center Freq (Hz):"), 0, 0); self.freq_input = Qt.QLineEdit(str(int(self.center_freq))); self.freq_input.returnPressed.connect(self.on_freq_change); freq_layout.addWidget(self.freq_input, 0, 1)
        freq_layout.addWidget(Qt.QLabel("Sample Rate (Hz):"), 1, 0); self.samp_input = Qt.QLineEdit(str(int(self.samp_rate))); self.samp_input.returnPressed.connect(self.on_samp_change); freq_layout.addWidget(self.samp_input, 1, 1)
        self.apply_btn = Qt.QPushButton("RESTART FLOWGRAPH"); self.apply_btn.clicked.connect(self.restart_flowgraph); freq_layout.addWidget(self.apply_btn, 2, 0, 1, 2)
        self.scroll_layout.addWidget(freq_box)

        # --- CENTER: Waterfall ---
        self.waterfall = qtgui.waterfall_sink_c(1024, window.WIN_BLACKMAN_hARRIS, self.center_freq, self.samp_rate, "Spectral Analysis Zone", 1)
        self.waterfall.set_intensity_range(-120, 20); self.pyqt_widget = sip.wrapinstance(self.waterfall.qwidget(), Qt.QWidget); self.main_split.addWidget(self.pyqt_widget, stretch=5)

        # --- RIGHT: Target Log ---
        self.history_panel = Qt.QVBoxLayout(); self.history_list = Qt.QListWidget(); self.history_list.setFixedWidth(180); self.history_list.setStyleSheet("background-color: #111; color: #0F0; font-family: monospace;"); self.main_split.addLayout(self.history_panel); self.history_panel.addWidget(Qt.QLabel("TRACK LOG (kHz)")); self.history_panel.addWidget(self.history_list); clear_hist = Qt.QPushButton("Clear Log"); clear_hist.clicked.connect(self.history_list.clear); self.history_panel.addWidget(clear_hist)

        # --- Blocks ---
        self.source = None
        self.interdictor = None
        self.sink = None
        self.file_sink = None
        
        self.update_dynamic_params(); self.load_presets_from_file(); self.update_cal_display()
        self.timer = QtCore.QTimer(); self.timer.timeout.connect(self.check_detections); self.timer.start(100)

    def on_scan_clicked(self):
        self.sys_logger.info("Scanning for USRP devices...")
        try:
            devices = uhd.find_devices()
            self.serial_combo.clear()
            if not devices:
                self.sys_logger.warning("No USRP devices found.")
                return
            for dev in devices:
                serial = dev.get('serial')
                model = dev.get('product', 'Unknown')
                self.serial_combo.addItem(f"{serial} ({model})")
            self.sys_logger.info(f"Found {len(devices)} devices.")
        except Exception as e:
            self.sys_logger.error(f"Scan failed: {e}")

    def on_connect_toggled(self, checked):
        if checked:
            selected_text = self.serial_combo.currentText()
            self.serial = selected_text.split(' ')[0] # Extract serial from "SERIAL (MODEL)"
            self.sys_logger.info(f"Connecting to USRP {self.serial}...")
            try:
                self.init_blocks()
                self.start()
                self.hardware_connected = True
                self.connect_btn.setText("DISCONNECT")
                self.connect_btn.setStyleSheet("background-color: #700; color: white; font-weight: bold;")
                self.label.setText("SCANNING...")
                self.label.setStyleSheet("font-size: 24px; font-weight: bold; color: yellow; background-color: black; padding: 10px; border: 2px solid #00F;")
                self.setWindowTitle(f"Predator Reactive Analysis Console: USRP {self.serial}")
            except Exception as e:
                self.sys_logger.error(f"Hardware connection failed: {e}")
                self.connect_btn.setChecked(False)
        else:
            self.sys_logger.info("Disconnecting hardware...")
            self.stop(); self.wait()
            self.disconnect_all()
            self.source = self.interdictor = self.sink = self.file_sink = None
            self.hardware_connected = False
            self.connect_btn.setText("CONNECT")
            self.connect_btn.setStyleSheet("background-color: #005; color: white; font-weight: bold;")
            self.label.setText("OFFLINE (VIRTUAL MODE)")
            self.label.setStyleSheet("font-size: 24px; font-weight: bold; color: #555; background-color: black; padding: 10px; border: 2px solid #333;")
            self.setWindowTitle("Predator Reactive Analysis Console")

    def init_blocks(self):
        if not self.serial:
            raise ValueError("No USRP serial specified.")
            
        self.source = uhd.usrp_source(",".join(("", f"serial={self.serial}")), uhd.stream_args(cpu_format="fc32", args='', channels=list(range(1)))); self.source.set_samp_rate(self.samp_rate); self.source.set_center_freq(self.center_freq, 0); self.source.set_gain(self.rx_gain, 0)
        try:
            from techniquemaker import interdictor_cpp
            self.sys_logger.info("Using high-performance C++ interdictor core.")
            self.interdictor = interdictor_cpp(
                technique='Direct CW',
                sample_rate_hz=self.samp_rate, bandwidth_hz=self.bw, reactive_threshold_db=self.threshold, reactive_dwell_ms=self.dwell, num_targets=self.num_targets, manual_mode=self.manual_mode, manual_freq=self.manual_freq, jamming_enabled=self.interdiction_enabled, adaptive_bw=self.adaptive_bw, preamble_sabotage=self.preamble_sabotage, sabotage_duration_ms=self.sabotage_duration, clock_pull_drift_hz_s=self.clock_pull, stutter_enabled=self.stutter_enabled, stutter_clean_count=self.stutter_clean, stutter_burst_count=self.stutter_burst, stutter_randomize=self.stutter_randomize, frame_duration_ms=self.frame_dur, output_mode='Continuous (Stream)'
            )
        except ImportError:
            self.sys_logger.warning("C++ core not found. Falling back to Python techniquepdu.")
            self.interdictor = techniquepdu(
                technique='Reactive Jammer', warhead_technique=self.template, sample_rate_hz=self.samp_rate, bandwidth_hz=self.bw, reactive_threshold_db=self.threshold, reactive_dwell_ms=self.dwell, num_targets=self.num_targets, manual_mode=self.manual_mode, manual_freq=self.manual_freq, jamming_enabled=self.interdiction_enabled, adaptive_bw=self.adaptive_bw, preamble_sabotage=self.preamble_sabotage, sabotage_duration_ms=self.sabotage_duration, clock_pull_drift_hz_s=self.clock_pull, stutter_enabled=self.stutter_enabled, stutter_clean_count=self.stutter_clean, stutter_burst_count=self.stutter_burst, stutter_randomize=self.stutter_randomize, frame_duration_ms=self.frame_dur, output_mode='Continuous (Stream)'
            )
        self.sink = uhd.usrp_sink(",".join(("", f"serial={self.serial}")), uhd.stream_args(cpu_format="fc32", args='', channels=list(range(1)))); self.sink.set_samp_rate(self.samp_rate); self.sink.set_center_freq(self.center_freq, 0); self.sink.set_gain(self.tx_gain, 0)
        self.file_sink = blocks.file_sink(gr.sizeof_gr_complex, "session.bin", False); self.file_sink.set_unbuffered(True)
        self.connect(self.source, self.interdictor); self.connect(self.interdictor, self.sink); self.connect(self.source, self.waterfall)

    def restart_flowgraph(self):
        if not self.hardware_connected:
            self.sys_logger.warning("Cannot restart flowgraph: No hardware connected.")
            return
        self.sys_logger.info("Restarting Flowgraph...")
        self.stop(); self.wait()
        self.disconnect_all()
        # Re-init parameters from UI
        self.on_freq_change()
        self.on_samp_change()
        self.init_blocks()
        self.start()

    def on_hydra_toggle(self, checked):
        self.hydra_auto_surgical = checked
        if self.interdictor and hasattr(self.interdictor, 'set_output_mode'):
            self.interdictor.set_output_mode("Auto-Surgical" if checked else "Continuous (Stream)")

    def on_sticky_toggle(self, checked):
        if self.interdictor and hasattr(self.interdictor, 'set_sticky_denial'):
            self.interdictor.set_sticky_denial(checked)

    def on_reset_denial(self):
        if self.interdictor and hasattr(self.interdictor, 'clear_persistent_targets'):
            self.interdictor.clear_persistent_targets()
            self.sys_logger.info("Persistent Denial Grid Cleared.")

    def on_look_change(self):
        try:
            ms = float(self.look_input.text())
            if self.interdictor and hasattr(self.interdictor, 'set_look_through_ms'):
                self.interdictor.set_look_through_ms(ms)
        except: pass

    def on_jam_cycle_change(self):
        try:
            ms = float(self.cycle_input.text())
            if self.interdictor and hasattr(self.interdictor, 'set_jam_cycle_ms'):
                self.interdictor.set_jam_cycle_ms(ms)
        except: pass

    def load_calibration(self):
        if os.path.exists("config/calibration_matrix.json"):
            try:
                with open("config/calibration_matrix.json", "r") as f:
                    raw = json.load(f); m = raw.get("matrix", {})
                    self.cal_data = {float(k): {float(gk): gv for gk, gv in v.items()} for k, v in m.items()}
            except: self.cal_data = {}

    def update_cal_display(self):
        if not self.cal_data: self.cal_label.setText("Est. Output: --- dBm"); return
        freqs = sorted(self.cal_data.keys()); closest_f = freqs[np.argmin(np.abs(np.array(freqs) - self.center_freq))]
        gain_map = self.cal_data[closest_f]; gain_keys = sorted(gain_map.keys()); closest_g = gain_keys[np.argmin(np.abs(np.array(gain_keys) - self.tx_gain))]
        pwr = gain_map[closest_g]; self.cal_label.setText(f"Est. Output: {pwr:.1f} dBm (@{closest_f/1e6:.0f}M)")

    def on_pull_input_change(self):
        try:
            self.clock_pull = float(self.pull_input.text())
            if self.interdictor: self.interdictor.set_clock_pull_drift_hz_s(self.clock_pull)
        except: pass
    def on_adapt_toggle(self, checked):
        self.adaptive_bw = checked
        if self.interdictor: self.interdictor.set_adaptive_bw(checked)
    def on_sab_toggle(self, checked):
        self.preamble_sabotage = checked
        if self.interdictor: self.interdictor.set_preamble_sabotage(checked)
    def on_sab_duration_change(self):
        try:
            self.sabotage_duration = float(self.sab_input.text())
            if self.interdictor: self.interdictor.set_sabotage_duration_ms(self.sabotage_duration)
        except: pass
    def on_stutter_toggle(self, checked):
        self.stutter_enabled = checked
        if self.interdictor: self.interdictor.set_stutter_enabled(checked)
    def on_stutter_clean_change(self):
        try:
            self.stutter_clean = int(self.stutter_clean_input.text())
            if self.interdictor: self.interdictor.set_stutter_clean_count(self.stutter_clean)
        except: pass
    def on_stutter_burst_change(self):
        try:
            self.stutter_burst = int(self.stutter_burst_input.text())
            if self.interdictor: self.interdictor.set_stutter_burst_count(self.stutter_burst)
        except: pass
    def on_stutter_rand_toggle(self, checked):
        self.stutter_randomize = checked
        if self.interdictor: self.interdictor.set_stutter_randomize(checked)
    def on_frame_dur_change(self):
        try:
            self.frame_dur = float(self.frame_input.text())
            if self.interdictor: self.interdictor.set_frame_duration_ms(self.frame_dur)
        except: pass
    def load_presets_from_file(self):
        if os.path.exists(self.preset_file):
            try:
                with open(self.preset_file, 'r') as f: self.presets = json.load(f)
            except: self.presets = {}
        self.preset_combo.clear(); self.preset_combo.addItems(list(self.presets.keys()))
    def save_current_preset(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Save Preset", "Enter Preset Name:")
        if ok and name:
            self.presets[name] = {"rx_gain": self.rx_gain, "tx_gain": self.tx_gain, "threshold": self.threshold, "template": self.template, "num_targets": self.num_targets, "center_freq": self.center_freq, "samp_rate": self.samp_rate, "adaptive_bw": self.adaptive_bw, "preamble_sabotage": self.preamble_sabotage, "clock_pull": self.clock_pull, "stutter_enabled": self.stutter_enabled, "stutter_clean": self.stutter_clean, "stutter_burst": self.stutter_burst, "stutter_randomize": self.stutter_randomize, "frame_dur": self.frame_dur}
            with open(self.preset_file, 'w') as f: json.dump(self.presets, f, indent=4)
            self.load_presets_from_file(); self.preset_combo.setCurrentText(name)
    def delete_current_preset(self):
        name = self.preset_combo.currentText()
        if name in self.presets: del self.presets[name]; json.dump(self.presets, open(self.preset_file, 'w'), indent=4); self.load_presets_from_file()
    def load_selected_preset(self, name):
        if name in self.presets:
            p = self.presets[name]; self.rx_gain = p.get("rx_gain", 40); self.rx_gain_slider.setValue(self.rx_gain); self.tx_gain = p.get("tx_gain", 50); self.tx_gain_slider.setValue(self.tx_gain); self.threshold = p.get("threshold", -45); self.thresh_slider.setValue(int(self.threshold)); self.num_targets = p.get("num_targets", 1); self.targets_slider.setValue(self.num_targets); self.center_freq = p.get("center_freq", 915e6); self.samp_rate = p.get("samp_rate", 2e6); self.template = p.get("template", "Narrowband Noise"); self.adaptive_bw = p.get("adaptive_bw", False); self.adapt_cb.setChecked(self.adaptive_bw); self.preamble_sabotage = p.get("preamble_sabotage", False); self.sab_cb.setChecked(self.preamble_sabotage); self.clock_pull = p.get("clock_pull", 0.0); self.pull_input.setText(str(self.clock_pull)); self.stutter_enabled = p.get("stutter_enabled", False); self.stutter_cb.setChecked(self.stutter_enabled); self.stutter_clean = p.get("stutter_clean", 3); self.stutter_clean_input.setText(str(self.stutter_clean)); self.stutter_burst = p.get("stutter_burst", 1); self.stutter_burst_input.setText(str(self.stutter_burst)); self.stutter_randomize = p.get("stutter_randomize", False); self.stutter_rand_cb.setChecked(self.stutter_randomize); self.frame_dur = p.get("frame_dur", 40.0); self.frame_input.setText(str(self.frame_dur)); self.template_combo.setCurrentText(self.template); self.update_cal_display()
    def check_detections(self):
        if not self.hardware_connected: return
        if not self.interdiction_enabled: self.label.setText("STBY (CEASE OUTPUT)"); self.label.setStyleSheet("font-size: 24px; font-weight: bold; color: gray; background-color: black; padding: 10px; border: 2px solid #0F0;"); return
        if self.manual_mode: self.label.setText(f"MANUAL: {self.manual_freq/1e3:.1f} kHz")
        elif self.hydra_auto_surgical: self.label.setText(f"HYDRA AUTO-SURGICAL ACTIVE"); self.label.setStyleSheet("font-size: 24px; font-weight: bold; color: cyan; background-color: black; padding: 10px; border: 2px solid #FF0;")
        elif self.interdictor and getattr(self.interdictor, '_dwell_counter', 0) > 0:
            self.label.setText(f"TRACKING ACTIVE"); self.label.setStyleSheet("font-size: 24px; font-weight: bold; color: #F00; background-color: black; padding: 10px; border: 2px solid #FF0;")
        else: self.label.setText("SCANNING..."); self.label.setStyleSheet("font-size: 24px; font-weight: bold; color: #0F0; background-color: black; padding: 10px; border: 2px solid white;")
    def on_record_toggle(self, checked):
        if not self.hardware_connected: return
        if checked: ts = int(time.time()); self.lock(); self.file_sink.open(f"analysis_{ts}.sigmf-data"); self.connect(self.source, self.file_sink); self.unlock(); self.record_btn.setText("LOGGING..."); self.record_btn.setStyleSheet("background-color: #A00; color: white;")
        else: self.lock(); self.disconnect(self.source, self.file_sink); self.file_sink.close(); self.unlock(); self.record_btn.setText("LOG SESSION"); self.record_btn.setStyleSheet("background-color: #333; color: white;")
    def on_targets_change(self, val):
        self.num_targets = val
        self.targets_label.setText(f"Max Targets: {val}")
        if self.interdictor: self.interdictor.set_num_targets(self.num_targets)
    def on_mode_change(self):
        self.manual_mode = self.manual_radio.isChecked()
        if self.interdictor: self.interdictor.set_manual_mode(self.manual_mode)
        self.manual_slider.setEnabled(self.manual_mode); self.thresh_slider.setEnabled(not self.manual_mode)
    def on_manual_freq_change(self, val):
        self.manual_freq = float(val)
        self.manual_label.setText(f"Offset: {val/1e3:.1f} kHz")
        if self.interdictor: self.interdictor.set_manual_freq(self.manual_freq)
    def update_dynamic_params(self):
        while self.param_layout.count():
            child = self.param_layout.takeAt(0);
            if child.widget(): child.widget().deleteLater()
        wf_def = BaseWaveforms.waveform_definitions.get(self.template)
        if not wf_def: return
        for p in wf_def['params']:
            if p['name'] in ['sample_rate_hz', 'technique_length_seconds']: continue
            if p['type'] == 'entry':
                w = Qt.QLineEdit("0")
                if self.interdictor: w.setText(str(getattr(self.interdictor, p['name'], "0")))
                w.editingFinished.connect(lambda n=p['name'], widget=w: self.on_dynamic_change(n, widget.text())); self.param_layout.addRow(p['title'], w)
            elif p['type'] == 'options':
                w = Qt.QComboBox(); w.addItems(p['choices'])
                if self.interdictor: w.setCurrentText(str(getattr(self.interdictor, p['name'], p['choices'][0])))
                w.currentTextChanged.connect(lambda val, n=p['name']: self.on_dynamic_change(n, val)); self.param_layout.addRow(p['title'], w)
    def on_dynamic_change(self, name, value):
        setter = f"set_{name}"
        if self.interdictor and hasattr(self.interdictor, setter):
            try:
                val = float(value) if '.' in value else int(value)
                getattr(self.interdictor, setter)(val)
            except: pass
    def on_template_change(self, value):
        self.template = value
        if self.interdictor: self.interdictor.set_technique(self.template)
        self.update_dynamic_params()
    def on_fire_toggle(self, checked):
        self.interdiction_enabled = not checked
        if self.interdictor: self.interdictor.set_jamming_enabled(self.interdiction_enabled)
    def on_threshold_change(self, value):
        self.threshold = value
        self.thresh_label.setText(f"Thresh: {value} dB")
        if self.interdictor: self.interdictor.set_reactive_threshold_db(value)
    def on_rx_gain_change(self, value):
        self.rx_gain = value
        if self.source: self.source.set_gain(value, 0)
    def on_tx_gain_change(self, value):
        self.tx_gain = value
        if self.sink: self.sink.set_gain(value, 0)
        self.update_cal_display()
    def on_freq_change(self):
        try:
            self.center_freq = float(self.freq_input.text())
            if self.source: self.source.set_center_freq(self.center_freq, 0)
            if self.sink: self.sink.set_center_freq(self.center_freq, 0)
            self.waterfall.set_frequency_range(self.center_freq, self.samp_rate)
            self.update_cal_display()
        except: pass
    def on_samp_change(self):
        try: self.samp_rate = float(self.samp_input.text())
        except: pass
    def stop_all(self): self.stop(); self.wait()

if __name__ == '__main__':
    app = Qt.QApplication(sys.argv); tb = PredatorJammer(); signal.signal(signal.SIGINT, lambda sig, frame: tb.stop_all() or sys.exit(0)); tb.start(); tb.show()
    app.aboutToQuit.connect(lambda: tb.stop_all()); sys.exit(app.exec_())
