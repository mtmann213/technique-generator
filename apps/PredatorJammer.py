#!/usr/bin/env python3
import numpy as np
from gnuradio import gr, uhd, qtgui, blocks, analog, soapy
from gnuradio.fft import window
from PyQt5 import Qt, QtCore, QtWidgets
import sys
import json
import time
import signal
import sip
import os
import random
try:
    from gnuradio.techniquemaker import techniquepdu, BaseWaveforms
except ImportError:
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
        self.burned_channels = [] # Shadow list of C++ targets
        
        # Load defaults from config
        default_serial = self.config_manager.get("hardware", "tx_usrp_serial", "34573DD")
        self.samp_rate = self.config_manager.get("hardware", "default_sample_rate_hz", 2e6)
        self.center_freq = self.config_manager.get("hardware", "default_center_freq_hz", 915e6)
        self.rx_gain = self.config_manager.get("rf_defaults", "rx_gain", 40)
        self.tx_gain = self.config_manager.get("rf_defaults", "tx_gain", 50)
        self.tx_level = -10.0
        self.tx_sink_type = "UHD"
        self.sh_serial = self.config_manager.get("hardware", "signal_hound_serial", "24248760")
        self.secondary_serial = self.config_manager.get("hardware", "tx_secondary_serial", "")
        self.tx2_offset = 0.0
        self.dual_tx_enabled = False
        self.bw_expand_enabled = False
        self.sync_tx1 = False
        
        # State for Secondary Warhead
        self.tx2_freq = self.center_freq + 20e6
        self.tx2_gain = self.tx_gain
        self.tx2_level = -10.0
        self.tx2_template = 'Narrowband Noise'
        self.tx2_targets = 1
        self.tx2_threshold = -45
        self.tx2_interdiction_enabled = True
        
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
        self.resize(1280, 800) # Slightly smaller for better fit

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
        tuning_layout.addWidget(Qt.QLabel("Band:"))
        self.band_combo = Qt.QComboBox()
        self.band_combo.addItems(["Custom", "ISM 915", "WiFi 2.4 (Ch 1)", "WiFi 2.4 (Ch 6)", "WiFi 2.4 (Ch 11)", "WiFi 5.8 (Ch 149)"])
        self.band_combo.currentTextChanged.connect(self.on_band_change)
        tuning_layout.addWidget(self.band_combo)
        
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

        # --- LEFT: Sidebar Container (Now Scrollable) ---
        self.sidebar_scroll = Qt.QScrollArea()
        self.sidebar_scroll.setWidgetResizable(True)
        self.sidebar_scroll.setMinimumWidth(400)
        self.middle_split.addWidget(self.sidebar_scroll, stretch=1)
        
        self.sidebar_container = Qt.QWidget()
        self.sidebar_layout = Qt.QVBoxLayout(self.sidebar_container)
        self.sidebar_scroll.setWidget(self.sidebar_container)

        self.tabs = Qt.QTabWidget()
        self.sidebar_layout.addWidget(self.tabs)

        # Tab 1: Hardware (Corrected Order)
        hw_tab = Qt.QWidget(); hw_layout = Qt.QVBoxLayout(hw_tab)
        self.tabs.addTab(hw_tab, "Hardware")
        
        hw_disc_box = Qt.QGroupBox("Device Setup")
        hw_disc_grid = Qt.QGridLayout(hw_disc_box)
        self.serial_combo = Qt.QComboBox(); self.serial_combo.setEditable(True); self.serial_combo.addItem(default_serial)
        hw_disc_grid.addWidget(Qt.QLabel("Serial:"), 0, 0)
        hw_disc_grid.addWidget(self.serial_combo, 0, 1)
        
        self.scan_btn = Qt.QPushButton("SCAN")
        self.scan_btn.clicked.connect(self.on_scan_clicked)
        hw_disc_grid.addWidget(self.scan_btn, 1, 0)
        
        self.connect_btn = Qt.QPushButton("CONNECT")
        self.connect_btn.setCheckable(True)
        self.connect_btn.toggled.connect(self.on_connect_toggled)
        hw_disc_grid.addWidget(self.connect_btn, 1, 1)

        self.sink_type_combo = Qt.QComboBox()
        self.sink_type_combo.addItems(["UHD (USRP)", "SoapySDR (Signal Hound)", "Sidekiq S4 (Soapy)"])
        self.sink_type_combo.currentTextChanged.connect(self.on_sink_type_change)
        hw_disc_grid.addWidget(Qt.QLabel("TX Sink:"), 2, 0)
        hw_disc_grid.addWidget(self.sink_type_combo, 2, 1)

        self.sh_serial_input = Qt.QLineEdit(self.sh_serial)
        self.sh_serial_input.setEnabled(False)
        hw_disc_grid.addWidget(Qt.QLabel("SH Serial:"), 3, 0)
        hw_disc_grid.addWidget(self.sh_serial_input, 3, 1)
        
        self.sim_cb = Qt.QCheckBox("Enable Simulated Signal Generator")
        self.sim_cb.toggled.connect(self.on_sim_toggle)
        hw_disc_grid.addWidget(self.sim_cb, 4, 0, 1, 2)

        # Secondary TX Group (Verticalized)
        self.sec_box = Qt.QGroupBox("Secondary Warhead Control")
        self.sec_grid = Qt.QGridLayout(self.sec_box)
        self.dual_tx_cb = Qt.QCheckBox("ENABLE SECONDARY SDR")
        self.dual_tx_cb.toggled.connect(self.on_dual_tx_toggle)
        self.sec_grid.addWidget(self.dual_tx_cb, 0, 0, 1, 2)
        
        self.secondary_serial_combo = Qt.QComboBox(); self.secondary_serial_combo.setEditable(True); self.secondary_serial_combo.addItem(self.secondary_serial)
        self.sec_grid.addWidget(Qt.QLabel("2nd Serial:"), 1, 0)
        self.sec_grid.addWidget(self.secondary_serial_combo, 1, 1)
        
        self.sync_cb = Qt.QCheckBox("SAME SETTINGS AS TX 1 (LINK)")
        self.sync_cb.toggled.connect(self.on_sync_toggle)
        self.sec_grid.addWidget(self.sync_cb, 2, 0, 1, 2)

        self.tx2_freq_input = Qt.QLineEdit(str(int(self.tx2_freq)))
        self.tx2_freq_input.editingFinished.connect(self.on_tx2_freq_change)
        self.tx2_freq_input.setStyleSheet("background-color: #033; color: cyan; font-weight: bold;") # Highlighted for visibility
        self.sec_grid.addWidget(Qt.QLabel("TX2 CENTER FREQ (Hz):"), 3, 0)
        self.sec_grid.addWidget(self.tx2_freq_input, 3, 1)

        self.bw_expand_cb = Qt.QCheckBox("Spectral Stitch Mode (+BW)")
        self.bw_expand_cb.toggled.connect(self.on_bw_expand_toggle)
        self.sec_grid.addWidget(self.bw_expand_cb, 4, 0, 1, 2)
        
        self.tx2_gain_slider = Qt.QSlider(QtCore.Qt.Horizontal); self.tx2_gain_slider.setRange(0, 89); self.tx2_gain_slider.setValue(50); self.tx2_gain_slider.valueChanged.connect(self.on_tx2_gain_change)
        self.sec_grid.addWidget(Qt.QLabel("TX2 Gain:"), 5, 0)
        self.sec_grid.addWidget(self.tx2_gain_slider, 5, 1)
        
        self.tx2_template_combo = Qt.QComboBox(); self.tx2_template_combo.addItems(list(BaseWaveforms.waveform_definitions.keys())); self.tx2_template_combo.currentTextChanged.connect(self.on_tx2_template_change)
        self.sec_grid.addWidget(Qt.QLabel("TX2 Warhead:"), 6, 0)
        self.sec_grid.addWidget(self.tx2_template_combo, 6, 1)
        
        hw_layout.addWidget(hw_disc_box)
        hw_layout.addWidget(self.sec_box)
        
        rf_box = Qt.QGroupBox("Gain & RF Output")
        rf_grid = Qt.QFormLayout(rf_box)
        self.rx_gain_slider = Qt.QSlider(QtCore.Qt.Horizontal); self.rx_gain_slider.setRange(0, 76); self.rx_gain_slider.setValue(40); self.rx_gain_slider.valueChanged.connect(self.on_rx_gain_change); rf_grid.addRow("RX Gain", self.rx_gain_slider)
        self.tx_gain_slider = Qt.QSlider(QtCore.Qt.Horizontal); self.tx_gain_slider.setRange(0, 89); self.tx_gain_slider.setValue(50); self.tx_gain_slider.valueChanged.connect(self.on_tx_gain_change); rf_grid.addRow("TX Gain", self.tx_gain_slider)
        self.tx_level_input = Qt.QLineEdit("-10.0"); self.tx_level_input.setFixedWidth(80); self.tx_level_input.editingFinished.connect(self.on_tx_level_change); rf_grid.addRow("TX Level (dBm)", self.tx_level_input); self.tx_level_input.setHidden(True)
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
        self.predictive_cb = Qt.QCheckBox("Enable Predictive Tracking (PRNG Cracker)"); self.predictive_cb.toggled.connect(self.on_predictive_toggle); hydra_grid.addRow(self.predictive_cb)
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
        self.frame_input = Qt.QLineEdit(str(self.frame_dur)); self.frame_input.editingFinished.connect(self.on_frame_dur_change); adv_grid.addRow("Frame Dur (ms):", self.frame_input)
        self.pull_input = Qt.QLineEdit(str(self.clock_pull)); self.pull_input.editingFinished.connect(self.on_pull_input_change); adv_grid.addRow("Clock-Pull (Hz/s):", self.pull_input)
        prot_layout.addWidget(adv_box); prot_layout.addStretch()

        # Warhead Selection at Bottom
        template_box = Qt.QGroupBox("Warhead Selection")
        template_layout = Qt.QVBoxLayout(template_box)
        self.template_combo = Qt.QComboBox(); self.template_combo.addItems(list(BaseWaveforms.waveform_definitions.keys())); self.template_combo.currentTextChanged.connect(self.on_template_change); template_layout.addWidget(self.template_combo)
        self.param_group = Qt.QGroupBox("Technique Parameters"); self.param_layout = Qt.QFormLayout(); self.param_group.setLayout(self.param_layout)
        template_layout.addWidget(self.param_group)
        self.sidebar_layout.addWidget(template_box)
        self.sidebar_layout.addStretch()

        # --- Waterfall (Combined View) ---
        self.waterfall = qtgui.waterfall_sink_c(1024, window.WIN_BLACKMAN_hARRIS, self.center_freq, self.samp_rate, "Active Tactical Waterfall", 2)
        self.waterfall.set_intensity_range(-120, 20); self.pyqt_widget = sip.wrapinstance(self.waterfall.qwidget(), Qt.QWidget); self.middle_split.addWidget(self.pyqt_widget, stretch=5)

        # --- Track Log ---
        self.history_panel = Qt.QVBoxLayout(); self.history_list = Qt.QListWidget(); self.history_list.setFixedWidth(250); self.history_list.setStyleSheet("background-color: #111; color: #0F0; font-family: monospace;"); self.middle_split.addLayout(self.history_panel); self.history_panel.addWidget(Qt.QLabel("DYNAMIC TRACK LOG")); self.history_panel.addWidget(self.history_list); clear_hist = Qt.QPushButton("Clear"); clear_hist.clicked.connect(self.history_list.clear); self.history_panel.addWidget(clear_hist)

        # --- Blocks ---
        self.source_node = self.interdictor = self.sink = self.file_sink = self.sim_src = None
        self.load_calibration(); self.load_presets_from_file()
        self.timer = QtCore.QTimer(); self.timer.timeout.connect(self.check_detections); self.timer.start(100)
        self.sim_timer = QtCore.QTimer(); self.sim_timer.timeout.connect(self.on_sim_hop)

    # --- Simulation Logic ---
    def on_sim_toggle(self, checked):
        self.sim_mode = checked
        if checked:
            self.sim_timer.start(500)
            self.sys_logger.info("Simulation Mode Started.")
        else:
            self.sim_timer.stop()
            self.sys_logger.info("Simulation Mode Stopped.")
        self.restart_flowgraph()

    def on_sim_hop(self):
        if not self.sim_src: return
        # LCG Pattern for predictable sequence cracking
        if not hasattr(self, '_sim_lcg_state'): self._sim_lcg_state = 1
        a = 1103515245; c = 12345; m = 2**31
        self._sim_lcg_state = (a * self._sim_lcg_state + c) % m
        # Map to discrete channels: +/- 400k, 200k, 0
        channels = [-0.4, -0.2, 0, 0.2, 0.4]
        hop_idx = int((self._sim_lcg_state / m) * len(channels))
        self.sim_src.set_frequency(channels[hop_idx] * self.samp_rate)

    # --- Hardware Scanning ---
    def on_scan_clicked(self):
        self.sys_logger.info("Scanning for USRP devices...")
        try:
            import uhd as standalone_uhd
            devices = standalone_uhd.find("")
            self.serial_combo.clear()
            if not devices:
                self.sys_logger.warning("No USRP devices found.")
                return
            for dev in devices:
                serial = dev.get('serial', 'N/A')
                product = dev.get('product', 'Unknown')
                disp = f"{serial} ({product})"
                self.serial_combo.addItem(disp)
                self.secondary_serial_combo.addItem(disp)
            self.sys_logger.info(f"Found {len(devices)} devices.")
        except Exception as e:
            self.sys_logger.error(f"Scan failed: {e}")

    def on_connect_toggled(self, checked):
        if checked:
            self.stop(); self.wait()
            selected_text = self.serial_combo.currentText()
            self.serial = selected_text.split(' ')[0]
            self.sys_logger.info(f"Connecting to USRP {self.serial}...")
            try:
                self.hardware_connected = True
                self.init_blocks()
                self.start()
                self.connect_btn.setText("DISCONNECT"); self.connect_btn.setStyleSheet("background-color: #700; color: white; font-weight: bold;")
                self.status_label.setText("CONNECTED"); self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; background: #040; color: #0F0; border: 2px solid #0F0; border-radius: 5px;")
                self.setWindowTitle(f"Predator Console [ONLINE - {self.serial}]")
                self.update_cal_display(); self.update_dynamic_params()
            except Exception as e:
                self.sys_logger.error(f"Hardware connection failed: {e}")
                self.hardware_connected = False
                self.connect_btn.setChecked(False)
        else:
            self.sys_logger.info("Disconnecting hardware...")
            self.stop(); self.wait(); self.disconnect_all()
            self.hw_source = self.interdictor = self.sink = self.sink2 = self.file_sink = self.sim_src = None
            self.hardware_connected = False
            self.connect_btn.setText("CONNECT"); self.connect_btn.setStyleSheet("background-color: #005; color: white; font-weight: bold;")
            self.status_label.setText("OFFLINE"); self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; background: #222; color: #555; border: 2px solid #333; border-radius: 5px;")
            self.setWindowTitle("Predator Console [OFFLINE]")

    def init_blocks(self):
        if self.hardware_connected and self.serial:
            self.hw_source = uhd.usrp_source(device_addr=f"serial={self.serial}", stream_args=uhd.stream_args(cpu_format="fc32", args='', channels=list(range(1))))
            self.hw_source.set_samp_rate(self.samp_rate); self.hw_source.set_center_freq(self.center_freq, 0); self.hw_source.set_gain(self.rx_gain, 0)
        else:
            self.hw_source = analog.noise_source_c(analog.GR_GAUSSIAN, 0.001, 0)

        if self.sim_mode:
            self.sim_src = analog.sig_source_c(self.samp_rate, analog.GR_COS_WAVE, 0, 0.5, 0)
            self.mixer = blocks.add_cc()
            self.connect(self.hw_source, (self.mixer, 0)); self.connect(self.sim_src, (self.mixer, 1))
            self.final_source = self.mixer
        else:
            self.sim_src = None
            self.final_source = self.hw_source

        try:
            from gnuradio.techniquemaker import interdictor_cpp
            self.sys_logger.info("Initializing Dual-Warhead C++ Matrix.")
            self.interdictor = interdictor_cpp(technique=self.template, sample_rate_hz=self.samp_rate, bandwidth_hz=self.bw, reactive_threshold_db=self.threshold, reactive_dwell_ms=self.dwell, num_targets=self.num_targets, manual_mode=self.manual_mode, manual_freq=self.manual_freq, jamming_enabled=self.interdiction_enabled, adaptive_bw=self.adaptive_bw, preamble_sabotage=self.preamble_sabotage, sabotage_duration_ms=self.sabotage_duration, clock_pull_drift_hz_s=self.clock_pull, stutter_enabled=self.stutter_enabled, stutter_clean_count=self.stutter_clean, stutter_burst_count=self.stutter_burst, stutter_randomize=self.stutter_randomize, frame_duration_ms=self.frame_dur, output_mode='Auto-Surgical' if self.hydra_auto_surgical else 'Continuous (Stream)')
            
            self.interdictor2 = interdictor_cpp(technique=self.tx2_template, sample_rate_hz=self.samp_rate, bandwidth_hz=self.bw, reactive_threshold_db=self.tx2_threshold, reactive_dwell_ms=self.dwell, num_targets=self.tx2_targets, manual_mode=self.manual_mode, manual_freq=0.0, jamming_enabled=self.tx2_interdiction_enabled, adaptive_bw=self.adaptive_bw, preamble_sabotage=self.preamble_sabotage, sabotage_duration_ms=self.sabotage_duration, clock_pull_drift_hz_s=self.clock_pull, stutter_enabled=self.stutter_enabled, stutter_clean_count=self.stutter_clean, stutter_burst_count=self.stutter_burst, stutter_randomize=self.stutter_randomize, frame_duration_ms=self.frame_dur, output_mode='Continuous (Stream)')
        except ImportError as e:
            self.sys_logger.warning(f"Dual-Warhead Fallback: {e}")
            self.interdictor = techniquepdu(technique='Reactive Jammer', warhead_technique=self.template, sample_rate_hz=self.samp_rate, bandwidth_hz=self.bw, reactive_threshold_db=self.threshold, reactive_dwell_ms=self.dwell, num_targets=self.num_targets, manual_mode=self.manual_mode, manual_freq=self.manual_freq, jamming_enabled=self.interdiction_enabled, adaptive_bw=self.adaptive_bw, preamble_sabotage=self.preamble_sabotage, sabotage_duration_ms=self.sabotage_duration, clock_pull_drift_hz_s=self.clock_pull, stutter_enabled=self.stutter_enabled, stutter_clean_count=self.stutter_clean, stutter_burst_count=self.stutter_burst, stutter_randomize=self.stutter_randomize, frame_duration_ms=self.frame_dur, output_mode='Continuous (Stream)')
            self.interdictor2 = techniquepdu(technique='Reactive Jammer', warhead_technique=self.tx2_template, sample_rate_hz=self.samp_rate, bandwidth_hz=self.bw, reactive_threshold_db=self.tx2_threshold, reactive_dwell_ms=self.dwell, num_targets=self.tx2_targets, manual_mode=self.manual_mode, manual_freq=0.0, jamming_enabled=self.tx2_interdiction_enabled, adaptive_bw=self.adaptive_bw, preamble_sabotage=self.preamble_sabotage, sabotage_duration_ms=self.sabotage_duration, clock_pull_drift_hz_s=self.clock_pull, stutter_enabled=self.stutter_enabled, stutter_clean_count=self.stutter_clean, stutter_burst_count=self.stutter_burst, stutter_randomize=self.stutter_randomize, frame_duration_ms=self.frame_dur, output_mode='Continuous (Stream)')

        if self.hardware_connected:
            # Primary Sink
            if self.tx_sink_type == "UHD":
                self.sink = uhd.usrp_sink(device_addr=f"serial={self.serial}", stream_args=uhd.stream_args(cpu_format="fc32", args='', channels=list(range(1))))
                self.sink.set_samp_rate(self.samp_rate); self.sink.set_center_freq(self.center_freq, 0); self.sink.set_gain(self.tx_gain, 0)
            elif self.tx_sink_type == "SoapySDR":
                sh_serial = self.sh_serial_input.text()
                self.sink = soapy.sink(f"driver=vsg60,serial={sh_serial}", "fc32", 1, "", "", [""], [""])
                self.sink.set_sample_rate(0, self.samp_rate); self.sink.set_frequency(0, self.center_freq)
                self.sink.set_gain(0, self.tx_level)
            else: # Sidekiq S4 (Soapy)
                self.sink = soapy.sink("driver=sidekiq", "fc32", 1, "", "", [""], [""])
                self.sink.set_sample_rate(0, self.samp_rate); self.sink.set_frequency(0, self.center_freq)
                self.sink.set_gain(0, self.tx_level)
            self.connect(self.interdictor, self.sink)

            # Secondary Sink
            if self.dual_tx_enabled:
                sec_serial = self.secondary_serial_combo.currentText()
                if sec_serial and sec_serial != self.serial:
                    self.sys_logger.info(f"Staging Secondary SDR {sec_serial}...")
                    time.sleep(2.0) # Hardware settling delay for USB devices
                    self.sink2 = uhd.usrp_sink(device_addr=f"serial={sec_serial}", stream_args=uhd.stream_args(cpu_format="fc32", args='', channels=list(range(1))))
                    self.sink2.set_samp_rate(self.samp_rate)
                    self.sink2.set_center_freq(self.tx2_freq, 0); self.sink2.set_gain(self.tx2_gain, 0)
                    self.connect(self.interdictor2, self.sink2)
                    self.sys_logger.info(f"Secondary Warhead deployed on USRP {sec_serial} (Freq: {self.tx2_freq/1e6} MHz)")
        else:
            self.sink = blocks.null_sink(gr.sizeof_gr_complex); self.connect(self.interdictor, self.sink)
            self.sink2 = blocks.null_sink(gr.sizeof_gr_complex); self.connect(self.interdictor2, self.sink2)

        self.file_sink = blocks.file_sink(gr.sizeof_gr_complex, "session.bin", False); self.file_sink.set_unbuffered(True)
        self.display_mixer = blocks.add_cc()
        self.connect(self.final_source, (self.display_mixer, 0))
        self.connect(self.interdictor, (self.display_mixer, 1))
        self.connect(self.final_source, self.interdictor)
        self.connect(self.final_source, self.interdictor2)
        self.connect(self.display_mixer, (self.waterfall, 0)) # RX + TX1 Visual
        self.connect(self.interdictor2, (self.waterfall, 1)) # TX2 Visual (Overlay)
        
        if hasattr(self.interdictor, 'set_sticky_denial'):
            self.interdictor.set_sticky_denial(self.sticky_cb.isChecked())
            self.interdictor.set_targets(self.burned_channels)
        if hasattr(self.interdictor, 'set_look_through_ms'):
            try: self.interdictor.set_look_through_ms(float(self.look_input.text()))
            except: pass
        if hasattr(self.interdictor, 'set_jam_cycle_ms'):
            try: self.interdictor.set_jam_cycle_ms(float(self.cycle_input.text()))
            except: pass
            
        self.update_dynamic_params()

    def restart_flowgraph(self):
        if not self.hardware_connected and not self.sim_mode: return
        self.sys_logger.info("Restarting Flowgraph...")
        self.stop(); self.wait(); self.disconnect_all()
        self.waterfall.set_frequency_range(self.center_freq, self.samp_rate)
        self.init_blocks(); self.start()

    def on_freq_change(self):
        try:
            self.center_freq = float(self.freq_input.text())
            if self.sync_tx1:
                self.tx2_freq = self.center_freq
                self.tx2_freq_input.setText(str(int(self.tx2_freq)))
            
            if not self.sim_mode and hasattr(self, 'hw_source'):
                if hasattr(self.hw_source, 'set_center_freq'): self.hw_source.set_center_freq(self.center_freq, 0)
            if hasattr(self, 'sink') and self.sink: 
                if hasattr(self.sink, 'set_center_freq'): self.sink.set_center_freq(self.center_freq, 0)
            if hasattr(self, 'sink2') and self.sink2:
                self.sink2.set_center_freq(self.tx2_freq, 0)
            self.waterfall.set_frequency_range(self.center_freq, self.samp_rate)
            self.update_cal_display()
        except Exception as e:
            self.sys_logger.error(f"Frequency update failed: {e}")

    def on_samp_change(self):
        try:
            val = float(self.samp_input.text())
            limit = 40e6 if self.tx_sink_type == "SoapySDR" else 20e6
            if val > limit:
                self.sys_logger.warning(f"Sample rate {val/1e6}M exceeds limit for {self.tx_sink_type}. Clipping to {limit/1e6}M.")
                val = limit; self.samp_input.setText(str(int(val)))
            self.samp_rate = val
            self.waterfall.set_frequency_range(self.center_freq, self.samp_rate)
        except: pass

    def on_sink_type_change(self, text):
        if "Sidekiq" in text: self.tx_sink_type = "Sidekiq"
        elif "SoapySDR" in text: self.tx_sink_type = "SoapySDR"
        else: self.tx_sink_type = "UHD"
        
        self.sh_serial_input.setEnabled(self.tx_sink_type == "SoapySDR")
        self.tx_gain_slider.setHidden(self.tx_sink_type != "UHD")
        self.tx_level_input.setHidden(self.tx_sink_type == "UHD")
        self.sys_logger.info(f"TX Sink switched to {self.tx_sink_type}")

    def on_tx_level_change(self):
        try:
            val = float(self.tx_level_input.text())
            # Safety limit check (Sidekiq S4 can handle higher, but we stick to USRP parity of 10 dBm for now)
            if val > 10.0:
                self.sys_logger.warning(f"TX Level {val} exceeds safety limit of 10.0 dBm. Clipping to 10.0.")
                val = 10.0; self.tx_level_input.setText("10.0")
            elif val < -120.0:
                self.sys_logger.warning(f"TX Level {val} below minimum of -120.0 dBm. Clipping to -120.0.")
                val = -120.0; self.tx_level_input.setText("-120.0")
            self.tx_level = val
            if self.sink and self.tx_sink_type in ["SoapySDR", "Sidekiq"]: self.sink.set_gain(0, self.tx_level)
            self.update_cal_display()
        except: pass

    def on_dual_tx_toggle(self, checked):
        self.dual_tx_enabled = checked
        self.secondary_serial_combo.setEnabled(checked)
        self.sync_cb.setEnabled(checked)
        self.tx2_freq_input.setEnabled(checked and not self.sync_tx1)
        self.tx2_gain_slider.setEnabled(checked and not self.sync_tx1)
        self.tx2_template_combo.setEnabled(checked and not self.sync_tx1)
        self.bw_expand_cb.setEnabled(checked and not self.sync_tx1)
        self.sys_logger.info(f"Secondary SDR {'Enabled' if checked else 'Disabled'}")

    def on_bw_expand_toggle(self, checked):
        self.bw_expand_enabled = checked
        if checked:
            self.tx2_freq = self.center_freq + self.samp_rate
            self.tx2_freq_input.setText(str(int(self.tx2_freq)))
            self.on_tx2_freq_change()
            self.sys_logger.info("Spectral Stitch Mode Active (+BW Offset)")
        else:
            self.sys_logger.info("Spectral Stitch Mode Disabled")

    def on_sync_toggle(self, checked):
        self.sync_tx1 = checked
        if checked:
            # Mirror all settings from TX1
            self.tx2_freq = self.center_freq
            self.tx2_freq_input.setText(str(int(self.tx2_freq)))
            self.tx2_gain = self.tx_gain
            self.tx2_gain_slider.setValue(self.tx2_gain)
            self.tx2_template = self.template
            self.tx2_template_combo.setCurrentText(self.tx2_template)
            self.on_tx2_freq_change()
            self.sys_logger.info("Secondary SDR linked to Master (TX1)")
        
        # Disable controls if synced
        self.tx2_freq_input.setEnabled(not checked)
        self.tx2_gain_slider.setEnabled(not checked)
        self.tx2_template_combo.setEnabled(not checked)
        self.bw_expand_cb.setEnabled(not checked)

    def on_tx2_freq_change(self):
        try:
            self.tx2_freq = float(self.tx2_freq_input.text())
            if hasattr(self, 'sink2') and self.sink2:
                self.sink2.set_center_freq(self.tx2_freq, 0)
            self.sys_logger.info(f"TX2 Center Frequency updated: {self.tx2_freq/1e6} MHz")
        except: pass

    def on_tx2_gain_change(self, val):
        self.tx2_gain = val
        if hasattr(self, 'sink2') and self.sink2:
            self.sink2.set_gain(self.tx2_gain, 0)

    def on_tx2_template_change(self, val):
        self.tx2_template = val
        if hasattr(self, 'interdictor2') and self.interdictor2:
            self.interdictor2.set_technique(self.tx2_template)
            # We'll need to update dynamic params for TX2 later

    def on_band_change(self, band):
        bands = {
            "ISM 915": 915e6,
            "WiFi 2.4 (Ch 1)": 2412e6,
            "WiFi 2.4 (Ch 6)": 2437e6,
            "WiFi 2.4 (Ch 11)": 2462e6,
            "WiFi 5.8 (Ch 149)": 5745e6
        }
        if band in bands:
            self.center_freq = bands[band]
            self.freq_input.setText(str(int(self.center_freq)))
            # WiFi usually needs higher default bandwidth for detection
            if "WiFi" in band:
                self.samp_rate = 20e6
                self.samp_input.setText(str(int(self.samp_rate)))
            self.on_freq_change()

    def check_detections(self):
        if not self.hardware_connected and not self.sim_mode:
            self.status_label.setText("OFFLINE"); self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; background: #222; color: #555; border: 2px solid #333; border-radius: 5px;"); return
        if not self.interdiction_enabled:
            self.status_label.setText("TX SILENT"); self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; background: #440; color: yellow; border: 2px solid yellow; border-radius: 5px;"); return
        
        # Telemetry Sync
        if self.interdictor and hasattr(self.interdictor, 'get_targets'):
            cpp_targets = self.interdictor.get_targets()
            if self.sticky_denial:
                self.burned_channels = cpp_targets
            
            # Update UI Log - Optimized to reduce flicker
            new_report = [f"{t.center_freq/1e3:8.1f} kHz | {t.bandwidth/1e3:4.1f}k" for t in cpp_targets]
            existing_report = [self.history_list.item(i).text() for i in range(self.history_list.count())]
            
            if new_report != existing_report:
                self.history_list.clear()
                self.history_list.addItems(new_report)

        self.status_label.setText("ACTIVE"); self.status_label.setStyleSheet("font-size: 18px; font-weight: bold; background: #400; color: #F00; border: 2px solid #F00; border-radius: 5px;")

    def on_hydra_toggle(self, checked):
        self.hydra_auto_surgical = checked
        if self.interdictor: self.interdictor.set_output_mode("Auto-Surgical" if checked else "Continuous (Stream)")
    def on_predictive_toggle(self, checked):
        if self.interdictor and hasattr(self.interdictor, 'set_predictive_tracking'):
            self.interdictor.set_predictive_tracking(checked)
    def on_sticky_toggle(self, checked): 
        self.sticky_denial = checked
        if self.interdictor and hasattr(self.interdictor, 'set_sticky_denial'): self.interdictor.set_sticky_denial(checked)
    def on_reset_denial(self): 
        self.burned_channels = []
        if self.interdictor and hasattr(self.interdictor, 'clear_persistent_targets'): 
            self.interdictor.clear_persistent_targets()
            self.sys_logger.info("Denial Grid Cleared.")
    def on_look_change(self):
        try:
            ms = float(self.look_input.text())
            if self.interdictor: self.interdictor.set_look_through_ms(ms)
        except: pass
    def on_jam_cycle_change(self):
        try:
            ms = float(self.cycle_input.text())
            if self.interdictor: self.interdictor.set_jam_cycle_ms(ms)
        except: pass
    def on_rx_gain_change(self, value):
        self.rx_gain = value
        if not self.sim_mode and hasattr(self, 'hw_source'): self.hw_source.set_gain(value, 0)
    def on_tx_gain_change(self, value):
        self.tx_gain = value
        if self.sync_tx1:
            self.tx2_gain = self.tx_gain
            self.tx2_gain_slider.setValue(self.tx2_gain)
        if hasattr(self, 'sink') and self.sink and self.tx_sink_type == "UHD": self.sink.set_gain(value, 0)
        if hasattr(self, 'sink2') and self.sink2: self.sink2.set_gain(self.tx2_gain, 0)
        self.update_cal_display()
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
    def on_targets_change(self, val):
        self.num_targets = val; self.targets_label.setText(f"Max Targets: {val}")
        if self.interdictor: self.interdictor.set_num_targets(self.num_targets)
    def on_threshold_change(self, value):
        self.threshold = value; self.thresh_label.setText(f"Threshold: {value} dB")
        if self.interdictor: self.interdictor.set_reactive_threshold_db(value)
    def on_template_change(self, value):
        self.template = value
        if self.sync_tx1:
            self.tx2_template = self.template
            self.tx2_template_combo.setCurrentText(self.tx2_template)
            if hasattr(self, 'interdictor2') and self.interdictor2:
                self.interdictor2.set_technique(self.tx2_template)

        if self.interdictor: self.interdictor.set_technique(self.template)
        self.update_dynamic_params()
    def on_mode_change(self):
        self.manual_mode = self.manual_radio.isChecked()
        if self.interdictor: self.interdictor.set_manual_mode(self.manual_mode)
        self.manual_slider.setEnabled(self.manual_mode); self.thresh_slider.setEnabled(not self.manual_mode)
    def on_manual_freq_change(self, val):
        self.manual_freq = float(val); self.manual_label.setText(f"Offset: {val/1e3:.1f} kHz")
        if self.interdictor: self.interdictor.set_manual_freq(self.manual_freq)
    def on_fire_toggle(self, checked):
        self.interdiction_enabled = not checked
        if self.interdictor: self.interdictor.set_jamming_enabled(self.interdiction_enabled)
    def on_frame_dur_change(self):
        try:
            self.frame_dur = float(self.frame_input.text())
            if self.interdictor: self.interdictor.set_frame_duration_ms(self.frame_dur)
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
    def load_presets_from_file(self):
        if os.path.exists(self.preset_file):
            try:
                with open(self.preset_file, 'r') as f: self.presets = json.load(f)
            except: self.presets = {}
        self.preset_combo.clear(); self.preset_combo.addItems(list(self.presets.keys()))
    def save_current_preset(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Save Preset", "Enter Preset Name:")
        if ok and name:
            self.presets[name] = {
                "rx_gain": self.rx_gain, "tx_gain": self.tx_gain, "threshold": self.threshold, 
                "template": self.template, "num_targets": self.num_targets, "center_freq": self.center_freq, 
                "samp_rate": self.samp_rate, "adaptive_bw": self.adaptive_bw, "preamble_sabotage": self.preamble_sabotage, 
                "clock_pull": self.clock_pull, "stutter_enabled": self.stutter_enabled, "stutter_clean": self.stutter_clean, 
                "stutter_burst": self.stutter_burst, "stutter_randomize": self.stutter_randomize, "frame_dur": self.frame_dur,
                "tx_sink_type": self.tx_sink_type, "tx_level": self.tx_level,
                "dual_tx_enabled": self.dual_tx_enabled, "secondary_serial": self.secondary_serial_combo.currentText(),
                "bw_expand": self.bw_expand_enabled, "sync_tx1": self.sync_tx1,
                "tx2_freq": self.tx2_freq, "tx2_gain": self.tx2_gain, "tx2_template": self.tx2_template
            }
            with open(self.preset_file, 'w') as f: json.dump(self.presets, f, indent=4)
            self.load_presets_from_file(); self.preset_combo.setCurrentText(name)
    def load_selected_preset(self, name):
        if name in self.presets:
            p = self.presets[name]
            self.rx_gain = p.get("rx_gain", 40); self.rx_gain_slider.setValue(self.rx_gain)
            self.tx_gain = p.get("tx_gain", 50); self.tx_gain_slider.setValue(self.tx_gain)
            self.threshold = p.get("threshold", -45); self.thresh_slider.setValue(int(self.threshold))
            self.num_targets = p.get("num_targets", 1); self.targets_slider.setValue(self.num_targets)
            self.center_freq = p.get("center_freq", 915e6); self.freq_input.setText(str(int(self.center_freq)))
            self.samp_rate = p.get("samp_rate", 2e6); self.samp_input.setText(str(int(self.samp_rate)))
            self.template = p.get("template", "Narrowband Noise"); self.template_combo.setCurrentText(self.template)
            self.adaptive_bw = p.get("adaptive_bw", False); self.adapt_cb.setChecked(self.adaptive_bw)
            self.preamble_sabotage = p.get("preamble_sabotage", False); self.sab_cb.setChecked(self.preamble_sabotage)
            self.clock_pull = p.get("clock_pull", 0.0); self.pull_input.setText(str(self.clock_pull))
            self.stutter_enabled = p.get("stutter_enabled", False); self.stutter_cb.setChecked(self.stutter_enabled)
            self.stutter_clean = p.get("stutter_clean", 3); self.stutter_clean_input.setText(str(self.stutter_clean))
            self.stutter_burst = p.get("stutter_burst", 1); self.stutter_burst_input.setText(str(self.stutter_burst))
            self.frame_dur = p.get("frame_dur", 40.0)
            if hasattr(self, 'frame_input'): self.frame_input.setText(str(self.frame_dur))
            
            # Hardware Sink selection
            new_sink = p.get("tx_sink_type", "UHD")
            self.tx_level = p.get("tx_level", -10.0)
            self.tx_level_input.setText(str(self.tx_level))
            idx = self.sink_type_combo.findText("SoapySDR" if new_sink == "SoapySDR" else "UHD", QtCore.Qt.MatchContains)
            if idx >= 0: self.sink_type_combo.setCurrentIndex(idx)
            
            self.dual_tx_enabled = p.get("dual_tx_enabled", False)
            self.dual_tx_cb.setChecked(self.dual_tx_enabled)
            self.secondary_serial = p.get("secondary_serial", "")
            self.secondary_serial_combo.setCurrentText(self.secondary_serial)
            
            self.bw_expand_enabled = p.get("bw_expand", False)
            self.bw_expand_cb.setChecked(self.bw_expand_enabled)
            
            self.sync_tx1 = p.get("sync_tx1", False)
            self.sync_cb.setChecked(self.sync_tx1)
            
            self.tx2_freq = p.get("tx2_freq", self.center_freq + 20e6)
            self.tx2_freq_input.setText(str(int(self.tx2_freq)))
            
            self.tx2_gain = p.get("tx2_gain", 50)
            self.tx2_gain_slider.setValue(self.tx2_gain)
            
            self.tx2_template = p.get("tx2_template", "Narrowband Noise")
            self.tx2_template_combo.setCurrentText(self.tx2_template)
            
            self.update_cal_display()
    def on_record_toggle(self, checked):
        if not self.hardware_connected: return
        if checked: ts = int(time.time()); self.lock(); self.file_sink.open(f"analysis_{ts}.sigmf-data"); self.connect(self.hw_source, self.file_sink); self.unlock(); self.record_btn.setText("LOGGING..."); self.record_btn.setStyleSheet("background-color: #A00; color: white;")
        else: self.lock(); self.disconnect(self.hw_source, self.file_sink); self.file_sink.close(); self.unlock(); self.record_btn.setText("LOG SIGMF"); self.record_btn.setStyleSheet("background-color: #333; color: white;")
    def update_dynamic_params(self):
        while self.param_layout.count():
            child = self.param_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        wf_def = BaseWaveforms.waveform_definitions.get(self.template)
        if not wf_def: return
        self.current_template_kwargs = { 'sample_rate_hz': self.samp_rate, 'technique_length_seconds': 0.1 }
        for p in wf_def['params']:
            if p['name'] in ['sample_rate_hz', 'technique_length_seconds']: continue
            default_val = p.get('default', "0")
            try: self.current_template_kwargs[p['name']] = float(default_val) if '.' in default_val else int(default_val)
            except ValueError: self.current_template_kwargs[p['name']] = default_val
            if p['type'] == 'entry':
                w = Qt.QLineEdit(default_val); w.editingFinished.connect(lambda n=p['name'], widget=w: self.on_dynamic_change(n, widget.text())); self.param_layout.addRow(p['title'], w)
            elif p['type'] == 'options':
                w = Qt.QComboBox(); w.addItems(p['choices']); w.setCurrentText(default_val); w.currentTextChanged.connect(lambda val, n=p['name']: self.on_dynamic_change(n, val)); self.param_layout.addRow(p['title'], w)
        self.generate_and_load_waveform()
    def on_dynamic_change(self, name, value):
        try: val = float(value) if '.' in value else int(value); self.current_template_kwargs[name] = val
        except ValueError: self.current_template_kwargs[name] = value
        self.generate_and_load_waveform()
    def generate_and_load_waveform(self):
        try:
            # Warhead 1
            if self.interdictor and hasattr(self.interdictor, 'set_base_waveform'):
                wf_def = BaseWaveforms.waveform_definitions.get(self.template)
                if wf_def:
                    func = wf_def['func']; kwargs = self.current_template_kwargs.copy()
                    import inspect; sig = inspect.signature(func); valid_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}
                    numpy_array = func(**valid_kwargs)
                    complex_float_array = np.array(numpy_array, dtype=np.complex64).tolist()
                    self.interdictor.set_base_waveform(complex_float_array)
            
            # Warhead 2
            if hasattr(self, 'interdictor2') and self.interdictor2 and hasattr(self.interdictor2, 'set_base_waveform'):
                wf_def2 = BaseWaveforms.waveform_definitions.get(self.tx2_template)
                if wf_def2:
                    # Note: Using master sample rate and duration for now
                    func2 = wf_def2['func']
                    sig2 = inspect.signature(func2)
                    # For simplicity, if synced, use master kwargs; else use defaults/tx2 defaults
                    # (This part can be expanded for independent TX2 param UI later)
                    valid_kwargs2 = {k: v for k, v in self.current_template_kwargs.items() if k in sig2.parameters}
                    numpy_array2 = func2(**valid_kwargs2)
                    complex_float_array2 = np.array(numpy_array2, dtype=np.complex64).tolist()
                    self.interdictor2.set_base_waveform(complex_float_array2)
                    
            self.sys_logger.info(f"Loaded Warheads: [TX1: {self.template}] [TX2: {self.tx2_template}]")
        except Exception as e: self.sys_logger.error(f"Failed to generate waveforms: {e}")
    def stop_all(self): self.stop(); self.wait()

if __name__ == '__main__':
    app = Qt.QApplication(sys.argv); tb = PredatorJammer(); signal.signal(signal.SIGINT, lambda sig, frame: tb.stop_all() or sys.exit(0)); tb.start(); tb.show()
    app.aboutToQuit.connect(lambda: tb.stop_all()); sys.exit(app.exec_())
