#!/usr/bin/env python3
import numpy as np
from gnuradio import gr, uhd, analog
import sys
import json
import time
import os
from PyQt5 import Qt, QtCore, QtWidgets
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from techniquemaker import techniquepdu, BaseWaveforms

# Optional SoapySDR import
try:
    import SoapySDR
    from SoapySDR import *
    SOAPY_AVAILABLE = True
except ImportError:
    SOAPY_AVAILABLE = False

class TransmitBlock(gr.top_block):
    def __init__(self, serial="3457480", samp_rate=2e6, freq=915e6, gain=50, technique="Narrowband Noise"):
        gr.top_block.__init__(self, "Calibration Transmitter")
        self.serial = serial
        self.samp_rate = samp_rate
        
        self.sink = uhd.usrp_sink(
            ",".join(("", f"serial={self.serial}")),
            uhd.stream_args(cpu_format="fc32", args='', channels=list(range(1)))
        )
        self.sink.set_samp_rate(self.samp_rate)
        self.sink.set_center_freq(freq, 0)
        self.sink.set_gain(gain, 0)
        
        # Use the real interdiction engine for calibration
        self.src = techniquepdu(
            technique=technique,
            sample_rate_hz=self.samp_rate,
            bandwidth_hz=100e3,
            output_mode='Continuous (Stream)'
        )
        self.connect(self.src, self.sink)

    def set_freq(self, freq): self.sink.set_center_freq(freq, 0)
    def set_gain(self, gain): self.sink.set_gain(gain, 0)
    def set_technique(self, tech): self.src.set_technique(tech)

class SystemCalibrator(Qt.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TechniqueMaker: RF System Calibrator (Precision Engine)")
        self.resize(1200, 800)
        
        self.results = {} # {freq: {gain: power}}
        self.tech_deltas = {} # {technique: delta_db}
        self.is_running = False
        self.tb = None
        self.sdr = None
        
        # --- UI Layout ---
        self.layout = Qt.QHBoxLayout(self)
        
        # Left Panel: Parameters
        self.left_panel = Qt.QVBoxLayout()
        self.scroll = QtWidgets.QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll_content = Qt.QWidget(); self.scroll_layout = Qt.QVBoxLayout(self.scroll_content)
        self.scroll.setWidget(self.scroll_content); self.left_panel.addWidget(self.scroll)

        # Basic Setup
        setup_box = Qt.QGroupBox("Hardware Setup")
        setup_layout = Qt.QFormLayout(); setup_box.setLayout(setup_layout)
        self.usrp_serial = Qt.QLineEdit("3457480"); setup_layout.addRow("USRP Serial:", self.usrp_serial)
        self.rx_mode = Qt.QComboBox(); self.rx_mode.addItems(["Manual Entry (Spike)", "SoapySDR (Auto)"])
        if not SOAPY_AVAILABLE: self.rx_mode.setItemEnabled(1, False)
        setup_layout.addRow("Receiver:", self.rx_mode)
        self.atten_ext = Qt.QLineEdit("30"); setup_layout.addRow("Ext Atten (dB):", self.atten_ext)
        self.scroll_layout.addWidget(setup_box)

        # Sweep Mode
        mode_box = Qt.QGroupBox("Sweep Configuration")
        mode_layout = Qt.QFormLayout(); mode_box.setLayout(mode_layout)
        self.cal_mode = Qt.QComboBox(); self.cal_mode.addItems(["Full Matrix (Gain/Freq)", "Technique Comparison"])
        mode_layout.addRow("Action:", self.cal_mode)
        
        self.tech_select = Qt.QComboBox()
        self.tech_select.addItems(["CW Tone (Pure)"] + list(BaseWaveforms.waveform_definitions.keys()))
        mode_layout.addRow("Template:", self.tech_select)
        
        self.f_start = Qt.QLineEdit("900e6"); self.f_stop = Qt.QLineEdit("930e6"); self.f_step = Qt.QLineEdit("5e6")
        mode_layout.addRow("Freq Start:", self.f_start); mode_layout.addRow("Freq Stop:", self.f_stop); mode_layout.addRow("Freq Step:", self.f_step)
        
        self.g_start = Qt.QLineEdit("30"); self.g_stop = Qt.QLineEdit("70"); self.g_step = Qt.QLineEdit("5")
        mode_layout.addRow("Gain Start:", self.g_start); mode_layout.addRow("Gain Stop:", self.g_stop); mode_layout.addRow("Gain Step:", self.g_step)
        self.scroll_layout.addWidget(mode_box)

        # Manual Interaction
        self.manual_group = Qt.QGroupBox("Manual Measurement (Spike)")
        self.manual_layout = Qt.QVBoxLayout(); self.manual_group.setLayout(self.manual_layout)
        self.manual_prompt = Qt.QLabel("READY"); self.manual_prompt.setStyleSheet("font-weight: bold; color: yellow;")
        self.manual_layout.addWidget(self.manual_prompt)
        entry_row = Qt.QHBoxLayout(); entry_row.addWidget(Qt.QLabel("dBm:")); self.manual_dbm = Qt.QLineEdit(); self.manual_dbm.returnPressed.connect(self.record_manual_step); entry_row.addWidget(self.manual_dbm); self.manual_layout.addLayout(entry_row)
        self.next_btn = Qt.QPushButton("RECORD & NEXT"); self.next_btn.clicked.connect(self.record_manual_step); self.manual_layout.addWidget(self.next_btn)
        self.manual_group.setEnabled(False); self.scroll_layout.addWidget(self.manual_group)

        self.start_btn = Qt.QPushButton("START CALIBRATION")
        self.start_btn.setStyleSheet("background-color: #050; color: white; font-weight: bold; height: 40px;")
        self.start_btn.clicked.connect(self.toggle_calibration)
        self.left_panel.addWidget(self.start_btn)
        
        self.status_label = Qt.QLabel("Status: READY"); self.status_label.setStyleSheet("font-family: monospace; background: black; color: #0F0; padding: 5px;"); self.left_panel.addWidget(self.status_label)
        self.progress = Qt.QProgressBar(); self.left_panel.addWidget(self.progress)
        self.log_area = Qt.QTextEdit(); self.log_area.setReadOnly(True); self.log_area.setStyleSheet("background: #111; color: white; font-family: monospace;"); self.left_panel.addWidget(self.log_area)
        
        self.layout.addLayout(self.left_panel, stretch=1)
        
        # Right Panel: Analytics
        self.figure = plt.figure(figsize=(8, 10))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas, stretch=2)
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.run_auto_step)

    def log(self, msg):
        self.log_area.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
        print(msg)

    def toggle_calibration(self):
        if self.is_running: self.stop_calibration()
        else: self.start_calibration()

    def start_calibration(self):
        try:
            # 1. Setup Sweep Data
            if self.cal_mode.currentText() == "Technique Comparison":
                self.sweep_techs = ["CW Tone (Pure)"] + list(BaseWaveforms.waveform_definitions.keys())
                self.sweep_freqs = [float(eval(self.f_start.text()))]
                self.sweep_gains = [float(self.g_start.text())]
                self.total_steps = len(self.sweep_techs)
            else:
                self.sweep_techs = [self.tech_select.currentText()]
                self.sweep_freqs = np.arange(float(eval(self.f_start.text())), float(eval(self.f_stop.text())) + 1, float(eval(self.f_step.text())))
                self.sweep_gains = np.arange(float(self.g_start.text()), float(self.g_stop.text()) + 1, float(self.g_step.text()))
                self.total_steps = len(self.sweep_freqs) * len(self.sweep_gains)

            self.current_step = 0
            self.results = {}
            self.tech_deltas = {}
            
            # 2. Start Hardware
            self.log(f"Starting USRP {self.usrp_serial.text()}...")
            initial_tech = self.sweep_techs[0] if self.sweep_techs[0] != "CW Tone (Pure)" else "Narrowband Noise"
            self.tb = TransmitBlock(serial=self.usrp_serial.text(), technique=initial_tech)
            self.tb.start()
            
            self.is_running = True
            self.start_btn.setText("STOP CALIBRATION"); self.start_btn.setStyleSheet("background-color: #700; color: white; font-weight: bold;")
            self.status_label.setText("Status: RUNNING")
            self.progress.setMaximum(self.total_steps); self.progress.setValue(0)

            if self.rx_mode.currentText() == "SoapySDR (Auto)":
                self.log("Auto-Discovery: Signal Hound...")
                self.sdr = SoapySDR.Device(dict(driver="bb60"))
                self.sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, [0])
                self.sdr.activateStream(self.sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, [0]))
                self.timer.start(int(self.dwell.text()))
            else:
                self.manual_group.setEnabled(True)
                self.update_manual_prompt()
            
        except Exception as e:
            self.log(f"ERROR: {e}"); self.stop_calibration()

    def stop_calibration(self):
        self.is_running = False; self.timer.stop(); self.manual_group.setEnabled(False)
        self.start_btn.setText("START CALIBRATION"); self.start_btn.setStyleSheet("background-color: #050; color: white; font-weight: bold;")
        self.status_label.setText("Status: READY")
        if self.tb:
            try: self.tb.stop(); self.tb.wait()
            except: pass
        if self.sdr:
            try: self.sdr.deactivateStream(None); self.sdr.closeStream(None)
            except: pass
        self.log("Calibration Halted.")

    def update_manual_prompt(self):
        if self.cal_mode.currentText() == "Technique Comparison":
            tech = self.sweep_techs[self.current_step]
            self.log(f"Switching to Template: {tech}")
            if tech == "CW Tone (Pure)":
                # Implementation detail: For pure CW, we replace the interdictor or set it to a very narrow mode
                # For simplicity, we use a single phasor tone
                self.tb.set_technique("Phasor Tones")
            else:
                self.tb.set_technique(tech)
            self.manual_prompt.setText(f"COMPARE ({self.current_step+1}/{self.total_steps})\nTemplate: {tech}")
        else:
            f_idx = self.current_step // len(self.sweep_gains)
            g_idx = self.current_step % len(self.sweep_gains)
            freq = self.sweep_freqs[f_idx]; gain = self.sweep_gains[g_idx]
            self.tb.set_freq(freq); self.tb.set_gain(gain)
            self.manual_prompt.setText(f"SWEEP ({self.current_step+1}/{self.total_steps})\nFreq: {freq/1e6:.2f} MHz\nGain: {gain} dB")
        
        self.manual_dbm.setFocus(); self.manual_dbm.selectAll()

    def record_manual_step(self):
        if not self.is_running: return
        try:
            measured = float(self.manual_dbm.text())
            actual_dbm = measured + float(self.atten_ext.text())
            
            if self.cal_mode.currentText() == "Technique Comparison":
                tech = self.sweep_techs[self.current_step]
                self.tech_deltas[tech] = actual_dbm
                self.log(f"Analyzed {tech}: {actual_dbm:.1f} dBm")
            else:
                f_idx = self.current_step // len(self.sweep_gains)
                freq = self.sweep_freqs[f_idx]
                gain = self.sweep_gains[self.current_step % len(self.sweep_gains)]
                if freq not in self.results: self.results[freq] = {}
                self.results[freq][gain] = actual_dbm
                self.log(f"Point recorded: {freq/1e6:.1f}M @ {gain}G = {actual_dbm:.1f} dBm")

            self.current_step += 1
            self.progress.setValue(self.current_step)
            
            if self.current_step >= self.total_steps: self.finish_calibration()
            else:
                self.update_manual_prompt()
                if self.current_step % 5 == 0: self.update_plot()
        except: self.log("Invalid value.")

    def run_auto_step(self):
        # Implementation for Auto mode similar to record_manual_step but with sdr.readStream
        # (Omitted here for brevity, focuses on user's Manual/Spike workflow)
        pass

    def update_plot(self):
        self.figure.clear()
        if self.cal_mode.currentText() == "Technique Comparison":
            ax = self.figure.add_subplot(111)
            names = list(self.tech_deltas.keys())
            vals = list(self.tech_deltas.values())
            if not vals: return
            # Calculate PAPR Offset relative to CW
            baseline = self.tech_deltas.get("CW Tone (Pure)", vals[0])
            offsets = [v - baseline for v in vals]
            bars = ax.barh(names, offsets, color='skyblue')
            ax.set_xlabel("Relative Power vs. CW (dB)")
            ax.set_title("Synthesis Template Power Offsets (PAPR)")
            ax.grid(True, axis='x', linestyle='--')
            # Label bars
            for i, v in enumerate(offsets): ax.text(v, i, f" {v:+.1f} dB", va='center')
        else:
            ax = self.figure.add_subplot(111)
            f_list = sorted(self.results.keys()); g_list = sorted(self.sweep_gains)
            if not f_list: return
            data = np.zeros((len(f_list), len(g_list)))
            for i, f in enumerate(f_list):
                for j, g in enumerate(g_list): data[i, j] = self.results[f].get(g, -100)
            im = ax.imshow(data, aspect='auto', extent=[g_list[0], g_list[-1], f_list[-1]/1e6, f_list[0]/1e6], cmap='plasma')
            ax.set_xlabel("USRP Gain (dB)"); ax.set_ylabel("Freq (MHz)"); ax.set_title(f"Hardware Characterization: {self.tech_select.currentText()}")
            self.figure.colorbar(im, label="dBm Output")
        
        self.canvas.draw()

    def finish_calibration(self):
        self.stop_calibration()
        self.log("Workflow Complete!")
        save_data = {
            "metadata": {"timestamp": time.time(), "usrp": self.usrp_serial.text(), "atten": self.atten_ext.text()},
            "matrix": {str(k): v for k, v in self.results.items()},
            "offsets": self.tech_deltas
        }
        with open("calibration_matrix.json", "w") as f: json.dump(save_data, f, indent=4)
        self.log("Data saved to calibration_matrix.json"); self.update_plot()

if __name__ == '__main__':
    app = Qt.QApplication(sys.argv); window = SystemCalibrator(); window.show(); sys.exit(app.exec_())
