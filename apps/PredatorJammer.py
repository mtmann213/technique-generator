#!/usr/bin/env python3
import numpy as np
from gnuradio import gr, uhd, qtgui, blocks, analog
from gnuradio.fft import window
from PyQt5 import Qt, QtCore, QtWidgets
import sys
import json
import time
import signal
import sip
import os
import random
from techniquemaker import techniquepdu, BaseWaveforms
from core_utils import ConfigManager, parse_scientific_notation

class PredatorJammer(gr.top_block, Qt.QWidget):
    def __init__(self):
        gr.top_block.__init__(self, "Predator Reactive Analysis Console")
        Qt.QWidget.__init__(self)
        
        self.config_manager = ConfigManager()
        self.sys_logger = self.config_manager.get_logger()
        
        # --- State ---
        self.serial = None
        self.hardware_connected = False
        self.sim_mode = False
        self.presets = {}
        self.preset_file = "config/predator_presets.json"
        self.cal_data = {}
        
        # Load defaults from config
        default_serial = self.config_manager.get("hardware", "tx_usrp_serial", "34573DD")
        self.samp_rate = self.config_manager.get("hardware", "default_sample_rate_hz", 2e6)
        self.center_freq = self.config_manager.get("hardware", "default_center_freq_hz", 915e6)
        self.rx_gain = self.config_manager.get("rf_defaults", "rx_gain", 40)
        self.tx_gain = self.config_manager.get("rf_defaults", "tx_gain", 50)
        
        # Parameters
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
        self.sticky_denial = False
        self.is_recording = False

        self.setWindowTitle("Predator Console [OFFLINE]")
        self.resize(1400, 900)

        # --- Main Layout ---
        self.root_layout = Qt.QVBoxLayout(self)

        # --- 1. GLOBAL HEADER ---
        self.header = Qt.QHBoxLayout()
        self.root_layout.addLayout(self.header)
        
        tuning_box = Qt.QGroupBox("Radio Master Control")
        tuning_layout = Qt.QHBoxLayout(tuning_box)
        tuning_layout.addWidget(Qt.QLabel("Center Freq (Hz):"))
        self.freq_input = Qt.QLineEdit(str(int(self.center_freq)))
        self.freq_input.returnPressed.connect(self.on_freq_change)
        tuning_layout.addWidget(self.freq_input)
        tuning_layout.addWidget(Qt.QLabel("Sample Rate (Hz):"))
        self.samp_input = Qt.QLineEdit(str(int(self.samp_rate)))
        self.samp_input.returnPressed.connect(self.on_samp_change)
        tuning_layout.addWidget(self.samp_input)
        self.apply_btn = Qt.QPushButton("APPLY HARDWARE CHANGES")
        self.apply_btn.clicked.connect(self.restart_flowgraph)
        self.apply_btn.setStyleSheet("background-color: #004; color: white; font-weight: bold;")
        tuning_layout.addWidget(self.apply_btn)
        self.header.addWidget(tuning_box, stretch=3)
        
        self.status_label = Qt.QLabel("OFFLINE")
        self.status_label.setFixedWidth(200)
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; background: #222; color: #555; border: 2px solid #333; border-radius: 5px;")
        self.header.addWidget(self.status_label)

        # --- 2. MIDDLE SPLIT ---
        self.middle_split = Qt.QHBoxLayout()
        self.root_layout.addLayout(self.middle_split)

        # --- LEFT: Sidebar Container ---
        self.sidebar_container = Qt.QVBoxLayout()
        self.middle_split.addLayout(self.sidebar_container)

        self.tabs = Qt.QTabWidget()
        self.tabs.setFixedWidth(380)
        self.sidebar_container.addWidget(self.tabs)

        # Tab 1: Hardware
        hw_tab = Qt.QWidget(); hw_layout = Qt.QVBoxLayout(hw_tab)
        self.tabs.addTab(hw_tab, "Hardware")
        
        hw_disc_box = Qt.QGroupBox("Device Setup")
        hw_disc_grid = Qt.QGridLayout(hw_disc_box)
        self.serial_combo = Qt.QComboBox(); self.serial_combo.setEditable(True); self.serial_combo.addItem(default_serial)
        hw_disc_grid.addWidget(Qt.QLabel("Serial:"), 0, 0); hw_disc_grid.addWidget(self.serial_combo, 0, 1)
        self.scan_btn = Qt.QPushButton("SCAN"); self.scan_btn.clicked.connect(self.on_scan_clicked); hw_disc_grid.addWidget(self.scan_btn, 1, 0)
        self.connect_btn = Qt.QPushButton("CONNECT"); self.connect_btn.setCheckable(True); self.connect_btn.toggled.connect(self.on_connect_toggled); hw_disc_grid.addWidget(self.connect_btn, 1, 1)
        self.sim_cb = Qt.QCheckBox("Enable Simulated Signal Generator"); self.sim_cb.toggled.connect(self.on_sim_toggle); hw_disc_grid.addWidget(self.sim_cb, 2, 0, 1, 2)
        hw_layout.addWidget(hw_disc_box)
        
        rf_box = Qt.QGroupBox("Gain & RF Output")
        rf_grid = Qt.QFormLayout(rf_box)
        self.rx_gain_slider = Qt.QSlider(QtCore.Qt.Horizontal); self.rx_gain_slider.setRange(0, 76); self.rx_gain_slider.setValue(40); self.rx_gain_slider.valueChanged.connect(self.on_rx_gain_change); rf_grid.addRow("RX Gain", self.rx_gain_slider)
        self.tx_gain_slider = Qt.QSlider(QtCore.Qt.Horizontal); self.tx_gain_slider.setRange(0, 89); self.tx_gain_slider.setValue(50); self.tx_gain_slider.valueChanged.connect(self.on_tx_gain_change); rf_grid.addRow("TX Gain", self.tx_gain_slider)
        self.cal_label = Qt.QLabel("Est. Output: --- dBm"); self.cal_label.setStyleSheet("color: cyan; font-weight: bold;"); rf_grid.addRow(self.cal_label)
        self.fire_btn = Qt.QPushButton("DISABLE TRANSMIT"); self.fire_btn.setCheckable(True); self.fire_btn.setStyleSheet("background-color: #050; color: white; font-weight: bold;"); self.fire_btn.toggled.connect(self.on_fire_toggle); rf_grid.addRow(self.fire_btn)
        hw_layout.addWidget(rf_box)
        
        pre_box = Qt.QGroupBox("Session & Records")
        pre_grid = Qt.QGridLayout(pre_box)
        self.preset_combo = Qt.QComboBox(); self.preset_combo.currentTextChanged.connect(self.load_selected_preset); pre_grid.addWidget(Qt.QLabel("Preset:"), 0, 0); pre_grid.addWidget(self.preset_combo, 0, 1)
        self.save_btn = Qt.QPushButton("Save Preset"); self.save_btn.clicked.connect(self.save_current_preset); pre_grid.addWidget(self.save_btn, 1, 0)
        self.record_btn = Qt.QPushButton("LOG SIGMF"); self.record_btn.setCheckable(True); self.record_btn.toggled.connect(self.on_record_toggle); pre_grid.addWidget(self.record_btn, 1, 1)
        hw_layout.addWidget(pre_box); hw_layout.addStretch()

        # Tab 2: Interdiction
        int_tab = Qt.QWidget(); int_layout = Qt.QVBoxLayout(int_tab)
        self.tabs.addTab(int_tab, "Interdiction")
        
        mode_box = Qt.QGroupBox("Target Selection")
        mode_layout = Qt.QVBoxLayout(mode_box)
        self.auto_radio = Qt.QRadioButton("Automatic Dynamic Tracking"); self.auto_radio.setChecked(True); self.auto_radio.toggled.connect(self.on_mode_change); mode_layout.addWidget(self.auto_radio)
        self.manual_radio = Qt.QRadioButton("Manual Frequency Offset"); self.manual_radio.toggled.connect(self.on_mode_change); mode_layout.addWidget(self.manual_radio)
        int_layout.addWidget(mode_box)
        
        hydra_box = Qt.QGroupBox("Hydra Auto-Surgical Engine")
        hydra_grid = Qt.QFormLayout(hydra_box)
        self.hydra_cb = Qt.QCheckBox("Enable Autonomous Comb"); self.hydra_cb.toggled.connect(self.on_hydra_toggle); hydra_grid.addRow(self.hydra_cb)
        self.adapt_cb = Qt.QCheckBox("Adaptive Bandwidth Sculpting"); self.adapt_cb.toggled.connect(self.on_adapt_toggle); hydra_grid.addRow(self.adapt_cb)
        self.targets_slider = Qt.QSlider(QtCore.Qt.Horizontal); self.targets_slider.setRange(1, 16); self.targets_slider.setValue(1); self.targets_slider.valueChanged.connect(self.on_targets_change); self.targets_label = Qt.QLabel("Max Targets: 1"); hydra_grid.addRow(self.targets_label, self.targets_slider)
        self.thresh_slider = Qt.QSlider(QtCore.Qt.Horizontal); self.thresh_slider.setRange(-120, 0); self.thresh_slider.setValue(-45); self.thresh_slider.valueChanged.connect(self.on_threshold_change); self.thresh_label = Qt.QLabel("Threshold: -45 dB"); hydra_grid.addRow(self.thresh_label, self.thresh_slider)
        int_layout.addWidget(hydra_box)
        
        sticky_box = Qt.QGroupBox("Sticky Channel Denial")
        sticky_grid = Qt.QFormLayout(sticky_box)
        self.sticky_cb = Qt.QCheckBox("Enable Persistent Trap"); self.sticky_cb.toggled.connect(self.on_sticky_toggle); sticky_grid.addRow(self.sticky_cb)
        self.look_input = Qt.QLineEdit("10.0"); self.look_input.editingFinished.connect(self.on_look_change); sticky_grid.addRow("Look-thru (ms):", self.look_input)
        self.cycle_input = Qt.QLineEdit("90.0"); self.cycle_input.editingFinished.connect(self.on_jam_cycle_change); sticky_grid.addRow("Jam Cycle (ms):", self.cycle_input)
        self.reset_denial_btn = Qt.QPushButton("FLUSH DENIAL GRID"); self.reset_denial_btn.clicked.connect(self.on_reset_denial); self.reset_denial_btn.setStyleSheet("background-color: #400; color: white;"); sticky_grid.addRow(self.reset_denial_btn)
        int_layout.addWidget(sticky_box)
        
        self.manual_box = Qt.QGroupBox("Manual Fine-Tuning")
        self.man_layout = Qt.QVBoxLayout(self.manual_box)
        self.manual_slider = Qt.QSlider(QtCore.Qt.Horizontal); self.manual_slider.setRange(-1000000, 1000000); self.manual_slider.setEnabled(False); self.manual_slider.valueChanged.connect(self.on_manual_freq_change); self.man_layout.addWidget(self.manual_slider)
        self.manual_label = Qt.QLabel("Offset: 0.0 kHz"); self.manual_label.setAlignment(QtCore.Qt.AlignCenter); self.man_layout.addWidget(self.manual_label)
        int_layout.addWidget(self.manual_box); int_layout.addStretch()

        # Tab 3: Protocol
        prot_tab = Qt.QWidget(); prot_layout = Qt.QVBoxLayout(prot_tab)
        self.tabs.addTab(prot_tab, "Protocol")
        
        adv_box = Qt.QGroupBox("Advanced Manipulations")
        adv_grid = Qt.QFormLayout(adv_box)
        self.sab_cb = Qt.QCheckBox("Preamble Sabotage (Invisible)"); self.sab_cb.toggled.connect(self.on_sab_toggle); adv_grid.addRow(self.sab_cb)
        self.sab_input = Qt.QLineEdit(str(self.sabotage_duration)); self.sab_input.editingFinished.connect(self.on_sab_duration_change); adv_grid.addRow("Duration (ms):", self.sab_input)
        self.stutter_cb = Qt.QCheckBox("Stability Frame Stutter"); self.stutter_cb.toggled.connect(self.on_stutter_toggle); adv_grid.addRow(self.stutter_cb)
        self.stutter_clean_input = Qt.QLineEdit(str(self.stutter_clean)); self.stutter_clean_input.editingFinished.connect(self.on_stutter_clean_change); adv_grid.addRow("Clean Count:", self.stutter_clean_input)
        self.stutter_burst_input = Qt.QLineEdit(str(self.stutter_burst)); self.stutter_burst_input.editingFinished.connect(self.on_stutter_burst_change); adv_grid.addRow("Burst Count:", self.stutter_burst_input)
        self.pull_input = Qt.QLineEdit(str(self.clock_pull)); self.pull_input.editingFinished.connect(self.on_pull_input_change); adv_grid.addRow("Clock-Pull (Hz/s):", self.pull_input)
        prot_layout.addWidget(adv_box); prot_layout.addStretch()

        # Signal Template at Bottom
        template_box = Qt.QGroupBox("Warhead Selection")
        template_layout = Qt.QVBoxLayout(template_box)
        self.template_combo = Qt.QComboBox(); self.template_combo.addItems(list(BaseWaveforms.waveform_definitions.keys())); self.template_combo.currentTextChanged.connect(self.on_template_change); template_layout.addWidget(self.template_combo)
        self.param_group = Qt.QGroupBox("Technique Parameters"); self.param_layout = Qt.QFormLayout(); self.param_group.setLayout(self.param_layout)
        template_layout.addWidget(self.param_group)
        self.sidebar_container.addWidget(template_box)

        # --- Waterfall ---
        self.waterfall = qtgui.waterfall_sink_c(1024, window.WIN_BLACKMAN_hARRIS, self.center_freq, self.samp_rate, "Active Tactical Waterfall", 1)
        self.waterfall.set_intensity_range(-120, 20); self.pyqt_widget = sip.wrapinstance(self.waterfall.qwidget(), Qt.QWidget); self.middle_split.addWidget(self.pyqt_widget, stretch=5)

        # --- Track Log ---
        self.history_panel = Qt.QVBoxLayout(); self.history_list = Qt.QListWidget(); self.history_list.setFixedWidth(180); self.history_list.setStyleSheet("background-color: #111; color: #0F0; font-family: monospace;"); self.middle_split.addLayout(self.history_panel); self.history_panel.addWidget(Qt.QLabel("DYNAMIC TRACK LOG")); self.history_panel.addWidget(self.history_list); clear_hist = Qt.QPushButton("Clear"); clear_hist.clicked.connect(self.history_list.clear); self.history_panel.addWidget(clear_hist)

        # --- Blocks ---
        self.source = self.interdictor = self.sink = self.file_sink = self.sim_src = None
        self.load_calibration(); self.load_presets_from_file()
        self.timer = QtCore.QTimer(); self.timer.timeout.connect(self.check_detections); self.timer.start(100)
        self.sim_timer = QtCore.QTimer(); self.sim_timer.timeout.connect(self.on_sim_hop)

    # --- SIMULATION LOGIC ---
    def on_sim_toggle(self, checked):
        self.sim_mode = checked
        if checked: self.sim_timer.start(500); self.sys_logger.info("Simulation Mode Started.")
        else: self.sim_timer.stop(); self.sys_logger.info("Simulation Mode Stopped.")
        if self.hardware_connected: self.restart_flowgraph()

    def on_sim_hop(self):
        if self.sim_src:
            # More aggressive hopping for better demonstration
            hop_offset = random.choice([-0.4, -0.2, 0, 0.2, 0.4]) * self.samp_rate
            self.sim_src.set_frequency(hop_offset)

    # --- UI LOGIC ---
    def on_scan_clicked(self):
        self.sys_logger.info("Scanning for USRP devices...")
        try:
            devices = uhd.find_devices()
            self.serial_combo.clear()
            if not devices: self.sys_logger.warning("No USRP devices found."); return
            for dev in devices:
                serial = dev.get('serial'); model = dev.get('product', 'Unknown')
                self.serial_combo.addItem(f"{serial} ({model})")
            self.sys_logger.info(f"Found {len(devices)} devices.")
        except Exception as e: self.sys_logger.error(f"Scan failed: {e}")

    def on_connect_toggled(self, checked):
        if checked:
            selected_text = self.serial_combo.currentText()
            self.serial = selected_text.split(' ')[0]
            self.sys_logger.info(f"Connecting to USRP {self.serial}...")
            try:
                self.init_blocks(); self.start(); self.hardware_connected = True
                self.connect_btn.setText("DISCONNECT"); self.connect_btn.setStyleSheet("background-color: #700; color: white; font-weight: bold;")
                self.status_label.setText("CONNECTED"); self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; background: #040; color: #0F0; border: 2px solid #0F0; border-radius: 5px;")
                self.setWindowTitle(f"Predator Console [ONLINE - {self.serial}]")
                self.update_cal_display(); self.update_dynamic_params()
            except Exception as e:
                self.sys_logger.error(f"Hardware connection failed: {e}"); self.connect_btn.setChecked(False)
        else:
            self.sys_logger.info("Disconnecting hardware...")
            self.stop(); self.wait(); self.disconnect_all()
            self.source = self.interdictor = self.sink = self.file_sink = self.sim_src = None
            self.hardware_connected = False
            self.connect_btn.setText("CONNECT"); self.connect_btn.setStyleSheet("background-color: #005; color: white; font-weight: bold;")
            self.status_label.setText("OFFLINE"); self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; background: #222; color: #555; border: 2px solid #333; border-radius: 5px;")
            self.setWindowTitle("Predator Console [OFFLINE]")

    def init_blocks(self):
        if self.sim_mode:
            self.sim_src = analog.sig_source_c(self.samp_rate, analog.GR_COS_WAVE, 0, 0.5, 0)
            self.source = blocks.add_cc()
            # We add a small amount of noise so the detector has a floor
            noise = analog.noise_source_c(analog.GR_GAUSSIAN, 0.01, 0)
            self.connect(self.sim_src, (self.source, 0))
            self.connect(noise, (self.source, 1))
        else:
            self.source = uhd.usrp_source(",".join(("", f"serial={self.serial}")), uhd.stream_args(cpu_format="fc32", args='', channels=list(range(1))))
            self.source.set_samp_rate(self.samp_rate); self.source.set_center_freq(self.center_freq, 0); self.source.set_gain(self.rx_gain, 0)
        
        try:
            from techniquemaker import interdictor_cpp
            self.interdictor = interdictor_cpp(technique=self.template, sample_rate_hz=self.samp_rate, bandwidth_hz=self.bw, reactive_threshold_db=self.threshold, reactive_dwell_ms=self.dwell, num_targets=self.num_targets, manual_mode=self.manual_mode, manual_freq=self.manual_freq, jamming_enabled=self.interdiction_enabled, adaptive_bw=self.adaptive_bw, preamble_sabotage=self.preamble_sabotage, sabotage_duration_ms=self.sabotage_duration, clock_pull_drift_hz_s=self.clock_pull, stutter_enabled=self.stutter_enabled, stutter_clean_count=self.stutter_clean, stutter_burst_count=self.stutter_burst, stutter_randomize=self.stutter_randomize, frame_duration_ms=self.frame_dur, output_mode='Auto-Surgical' if self.hydra_auto_surgical else 'Continuous (Stream)')
        except ImportError:
            self.interdictor = techniquepdu(technique='Reactive Jammer', warhead_technique=self.template, sample_rate_hz=self.samp_rate, bandwidth_hz=self.bw, reactive_threshold_db=self.threshold, reactive_dwell_ms=self.dwell, num_targets=self.num_targets, manual_mode=self.manual_mode, manual_freq=self.manual_freq, jamming_enabled=self.interdiction_enabled, adaptive_bw=self.adaptive_bw, preamble_sabotage=self.preamble_sabotage, sabotage_duration_ms=self.sabotage_duration, clock_pull_drift_hz_s=self.clock_pull, stutter_enabled=self.stutter_enabled, stutter_clean_count=self.stutter_clean, stutter_burst_count=self.stutter_burst, stutter_randomize=self.stutter_randomize, frame_duration_ms=self.frame_dur, output_mode='Continuous (Stream)')
        
        if not self.sim_mode:
            self.sink = uhd.usrp_sink(",".join(("", f"serial={self.serial}")), uhd.stream_args(cpu_format="fc32", args='', channels=list(range(1))))
            self.sink.set_samp_rate(self.samp_rate); self.sink.set_center_freq(self.center_freq, 0); self.sink.set_gain(self.tx_gain, 0)
            self.connect(self.interdictor, self.sink)
        
        self.file_sink = blocks.file_sink(gr.sizeof_gr_complex, "session.bin", False); self.file_sink.set_unbuffered(True)
        self.connect(self.source, self.interdictor); self.connect(self.source, self.waterfall)

    def restart_flowgraph(self):
        if not self.hardware_connected and not self.sim_mode: return
        self.sys_logger.info("Restarting Flowgraph..."); self.stop(); self.wait(); self.disconnect_all(); self.init_blocks(); self.start()

    def on_freq_change(self):
        try:
            self.center_freq = float(self.freq_input.text())
            if not self.sim_mode and self.source: self.source.set_center_freq(self.center_freq, 0)
            if self.sink: self.sink.set_center_freq(self.center_freq, 0)
            self.waterfall.set_center_freq(self.center_freq); self.update_cal_display()
        except: pass
    def on_samp_change(self):
        try:
            self.samp_rate = float(self.samp_input.text())
            self.waterfall.set_sample_rate(self.samp_rate)
        except: pass

    def on_hydra_toggle(self, checked):
        self.hydra_auto_surgical = checked
        if self.interdictor:
            self.interdictor.set_output_mode("Auto-Surgical" if checked else "Continuous (Stream)")

    def on_sticky_toggle(self, checked): 
        self.sticky_denial = checked
        if self.interdictor and hasattr(self.interdictor, 'set_sticky_denial'):
            self.interdictor.set_sticky_denial(checked)

    def on_reset_denial(self): 
        if self.interdictor and hasattr(self.interdictor, 'clear_persistent_targets'):
            self.interdictor.clear_persistent_targets()
            self.sys_logger.info("Denial Grid Cleared.")

    def on_look_change(self):
        try: 
            ms = float(self.look_input.text())
            if self.interdictor:
                self.interdictor.set_look_through_ms(ms)
        except: pass

    def on_jam_cycle_change(self):
        try: 
            ms = float(self.cycle_input.text())
            if self.interdictor:
                self.interdictor.set_jam_cycle_ms(ms)
        except: pass

    def on_rx_gain_change(self, value):
        self.rx_gain = value
        if not self.sim_mode and self.source:
            self.source.set_gain(value, 0)

    def on_tx_gain_change(self, value):
        self.tx_gain = value
        if self.sink:
            self.sink.set_gain(value, 0)
        self.update_cal_display()

    def on_pull_input_change(self):
        try: 
            self.clock_pull = float(self.pull_input.text())
            if self.interdictor:
                self.interdictor.set_clock_pull_drift_hz_s(self.clock_pull)
        except: pass

    def on_adapt_toggle(self, checked):
        self.adaptive_bw = checked
        if self.interdictor:
            self.interdictor.set_adaptive_bw(checked)

    def on_sab_toggle(self, checked):
        self.preamble_sabotage = checked
        if self.interdictor:
            self.interdictor.set_preamble_sabotage(checked)

    def on_sab_duration_change(self):
        try: 
            self.sabotage_duration = float(self.sab_input.text())
            if self.interdictor:
                self.interdictor.set_sabotage_duration_ms(self.sabotage_duration)
        except: pass

    def on_stutter_toggle(self, checked):
        self.stutter_enabled = checked
        if self.interdictor:
            self.interdictor.set_stutter_enabled(checked)

    def on_stutter_clean_change(self):
        try: 
            self.stutter_clean = int(self.stutter_clean_input.text())
            if self.interdictor:
                self.interdictor.set_stutter_clean_count(self.stutter_clean)
        except: pass

    def on_stutter_burst_change(self):
        try: 
            self.stutter_burst = int(self.stutter_burst_input.text())
            if self.interdictor:
                self.interdictor.set_stutter_burst_count(self.stutter_burst)
        except: pass

    def on_targets_change(self, val):
        self.num_targets = val
        self.targets_label.setText(f"Max Targets: {val}")
        if self.interdictor:
            self.interdictor.set_num_targets(self.num_targets)

    def on_threshold_change(self, value):
        self.threshold = value
        self.thresh_label.setText(f"Threshold: {value} dB")
        if self.interdictor:
            self.interdictor.set_reactive_threshold_db(value)

    def on_template_change(self, value):
        self.template = value
        if self.interdictor:
            self.interdictor.set_technique(self.template)
        self.update_dynamic_params()

    def on_mode_change(self):
        self.manual_mode = self.manual_radio.isChecked()
        if self.interdictor:
            self.interdictor.set_manual_mode(self.manual_mode)
        self.manual_slider.setEnabled(self.manual_mode)
        self.thresh_slider.setEnabled(not self.manual_mode)

    def on_manual_freq_change(self, val):
        self.manual_freq = float(val)
        self.manual_label.setText(f"Offset: {val/1e3:.1f} kHz")
        if self.interdictor:
            self.interdictor.set_manual_freq(self.manual_freq)

    def on_fire_toggle(self, checked):
        self.interdiction_enabled = not checked
        if self.interdictor:
            self.interdictor.set_jamming_enabled(self.interdiction_enabled)

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
    def load_selected_preset(self, name):
        if name in self.presets:
            p = self.presets[name]; self.rx_gain = p.get("rx_gain", 40); self.rx_gain_slider.setValue(self.rx_gain); self.tx_gain = p.get("tx_gain", 50); self.tx_gain_slider.setValue(self.tx_gain); self.threshold = p.get("threshold", -45); self.thresh_slider.setValue(int(self.threshold)); self.num_targets = p.get("num_targets", 1); self.targets_slider.setValue(self.num_targets); self.center_freq = p.get("center_freq", 915e6); self.samp_rate = p.get("samp_rate", 2e6); self.template = p.get("template", "Narrowband Noise"); self.adaptive_bw = p.get("adaptive_bw", False); self.adapt_cb.setChecked(self.adaptive_bw); self.preamble_sabotage = p.get("preamble_sabotage", False); self.sab_cb.setChecked(self.preamble_sabotage); self.clock_pull = p.get("clock_pull", 0.0); self.pull_input.setText(str(self.clock_pull)); self.stutter_enabled = p.get("stutter_enabled", False); self.stutter_cb.setChecked(self.stutter_enabled); self.stutter_clean = p.get("stutter_clean", 3); self.stutter_clean_input.setText(str(self.stutter_clean)); self.stutter_burst = p.get("stutter_burst", 1); self.stutter_burst_input.setText(str(self.stutter_burst)); self.stutter_randomize = p.get("stutter_randomize", False); self.stutter_rand_cb.setChecked(self.stutter_randomize); self.frame_dur = p.get("frame_dur", 40.0); self.frame_input.setText(str(self.frame_dur)); self.template_combo.setCurrentText(self.template); self.update_cal_display()
    def check_detections(self):
        if not self.hardware_connected and not self.sim_mode: self.status_label.setText("OFFLINE"); self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; background: #222; color: #555; border: 2px solid #333; border-radius: 5px;"); return
        if not self.interdiction_enabled: self.status_label.setText("TX SILENT"); self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; background: #440; color: yellow; border: 2px solid yellow; border-radius: 5px;"); return
        self.status_label.setText("ACTIVE"); self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; background: #400; color: #F00; border: 2px solid #F00; border-radius: 5px;")
    def on_record_toggle(self, checked):
        if not self.hardware_connected: return
        if checked: ts = int(time.time()); self.lock(); self.file_sink.open(f"analysis_{ts}.sigmf-data"); self.connect(self.source, self.file_sink); self.unlock(); self.record_btn.setText("LOGGING..."); self.record_btn.setStyleSheet("background-color: #A00; color: white;")
        else: self.lock(); self.disconnect(self.source, self.file_sink); self.file_sink.close(); self.unlock(); self.record_btn.setText("LOG SIGMF"); self.record_btn.setStyleSheet("background-color: #333; color: white;")
    
    def on_dynamic_change(self, name, value):
        setter = f"set_{name}"
        if self.interdictor and hasattr(self.interdictor, setter):
            try:
                val = float(value) if '.' in value else int(value)
                getattr(self.interdictor, setter)(val)
            except: pass

    def update_dynamic_params(self):
        while self.param_layout.count():
            child = self.param_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        wf_def = BaseWaveforms.waveform_definitions.get(self.template)
        if not wf_def: return
        for p in wf_def['params']:
            if p['name'] in ['sample_rate_hz', 'technique_length_seconds']: continue
            default_val = p.get('default', "0")
            if p['type'] == 'entry':
                w = Qt.QLineEdit(default_val); w.editingFinished.connect(lambda n=p['name'], widget=w: self.on_dynamic_change(n, widget.text())); self.param_layout.addRow(p['title'], w)
            elif p['type'] == 'options':
                w = Qt.QComboBox(); w.addItems(p['choices']); w.setCurrentText(default_val); w.currentTextChanged.connect(lambda val, n=p['name']: self.on_dynamic_change(n, val)); self.param_layout.addRow(p['title'], w)
    def stop_all(self): self.stop(); self.wait()

if __name__ == '__main__':
    app = Qt.QApplication(sys.argv); tb = PredatorJammer(); signal.signal(signal.SIGINT, lambda sig, frame: tb.stop_all() or sys.exit(0)); tb.start(); tb.show()
    app.aboutToQuit.connect(lambda: tb.stop_all()); sys.exit(app.exec_())
