#!/usr/bin/env python3
import numpy as np
from gnuradio import gr, uhd, analog, blocks
import sys
import json
import time
import os
import traceback
import csv
from PyQt5 import Qt, QtCore, QtWidgets
import matplotlib
matplotlib.use('Qt5Agg')
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

class TableWindow(Qt.QWidget):
    def __init__(self, f_list, p_targets, gain_matrix):
        super().__init__()
        self.setWindowTitle("Operational Gain Table")
        self.resize(800, 600)
        layout = Qt.QVBoxLayout(self)
        self.table = Qt.QTableWidget()
        self.table.setRowCount(len(f_list)); self.table.setColumnCount(len(p_targets))
        self.table.setHorizontalHeaderLabels([f"{p} dBm" for p in p_targets])
        self.table.setVerticalHeaderLabels([f"{f/1e6:.2f} MHz" for f in f_list])
        for i, f in enumerate(f_list):
            for j, p in enumerate(p_targets):
                val = gain_matrix[i, j]
                item = Qt.QTableWidgetItem(f"{val:.2f}" if not np.isnan(val) else "N/A")
                if np.isnan(val): item.setBackground(Qt.QColor(100, 0, 0))
                self.table.setItem(i, j, item)
        layout.addWidget(self.table)
        btn = Qt.QPushButton("Close"); btn.clicked.connect(self.close); layout.addWidget(btn)

class TransmitBlock(gr.top_block):
    def __init__(self, serial="3457480", samp_rate=2e6, freq=915e6, gain=50, technique="Narrowband Noise"):
        gr.top_block.__init__(self, "Calibration Transmitter")
        self.sink = uhd.usrp_sink(",".join(("", f"serial={serial}")), uhd.stream_args(cpu_format="fc32", args='', channels=list(range(1))))
        self.sink.set_samp_rate(samp_rate); self.sink.set_center_freq(freq, 0); self.sink.set_gain(gain, 0)
        self.src = techniquepdu(technique=technique, sample_rate_hz=samp_rate, bandwidth_hz=100e3, output_mode='Continuous (Stream)')
        self.connect(self.src, self.sink)
    def set_freq(self, freq): self.sink.set_center_freq(freq, 0)
    def set_gain(self, gain): self.sink.set_gain(gain, 0)
    def set_technique(self, tech): self.src.set_technique(tech)

class ReceiveBlock(gr.top_block):
    def __init__(self, serial="3457464", samp_rate=2e6, freq=915e6, gain=40):
        gr.top_block.__init__(self, "Calibration Receiver")
        self.source = uhd.usrp_source(",".join(("", f"serial={serial}")), uhd.stream_args(cpu_format="fc32", args='', channels=list(range(1))))
        self.source.set_samp_rate(samp_rate); self.source.set_center_freq(freq, 0); self.source.set_gain(gain, 0)
        self.snk = blocks.vector_sink_c(); self.connect(self.source, self.snk)
    def set_freq(self, freq): self.source.set_center_freq(freq, 0)
    def get_data(self, num_samples=1024):
        all_data = self.snk.data()
        if len(all_data) < num_samples: return None
        return np.array(all_data[-num_samples:])

class SystemCalibrator(Qt.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TechniqueMaker: RF System Calibrator")
        self.resize(1300, 950)
        self.results = {}; self.is_running = False; self.tb = None; self.rb = None; self.sdr = None
        self.presets = {}; self.preset_file = "calibrator_presets.json"
        
        # --- UI Layout ---
        self.layout = Qt.QHBoxLayout(self)
        self.left_panel = Qt.QVBoxLayout()
        self.scroll = QtWidgets.QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll_content = Qt.QWidget(); self.scroll_layout = Qt.QVBoxLayout(self.scroll_content)
        self.scroll.setWidget(self.scroll_content); self.left_panel.addWidget(self.scroll)

        # Presets
        preset_box = Qt.QGroupBox("Session Presets")
        preset_grid = Qt.QGridLayout(); preset_box.setLayout(preset_grid)
        self.preset_combo = Qt.QComboBox(); self.preset_combo.currentTextChanged.connect(self.load_selected_preset)
        preset_grid.addWidget(Qt.QLabel("Preset:"), 0, 0); preset_grid.addWidget(self.preset_combo, 0, 1)
        self.save_btn = Qt.QPushButton("Save New"); self.save_btn.clicked.connect(self.save_current_preset); preset_grid.addWidget(self.save_btn, 1, 0)
        self.del_btn = Qt.QPushButton("Delete"); self.del_btn.clicked.connect(self.delete_current_preset); preset_grid.addWidget(self.del_btn, 1, 1)
        self.scroll_layout.addWidget(preset_box)

        # Hardware & Sweep
        hw_box = Qt.QGroupBox("Hardware & Sweep Setup")
        hw_layout = Qt.QFormLayout(); hw_box.setLayout(hw_layout)
        self.tx_serial = Qt.QLineEdit("3457480"); hw_layout.addRow("TX Serial:", self.tx_serial)
        self.rx_mode = Qt.QComboBox(); self.rx_mode.addItems(["USRP (UHD)", "Signal Hound (Soapy)", "Manual Entry (Spike)"]); hw_layout.addRow("Receiver:", self.rx_mode)
        self.rx_serial = Qt.QLineEdit("3457464"); hw_layout.addRow("RX Serial:", self.rx_serial)
        self.atten_ext = Qt.QLineEdit("30"); hw_layout.addRow("Ext Atten (dB):", self.atten_ext)
        self.f_start = Qt.QLineEdit("900e6"); self.f_stop = Qt.QLineEdit("930e6"); self.f_step = Qt.QLineEdit("5e6")
        hw_layout.addRow("Freq Start:", self.f_start); hw_layout.addRow("Freq Stop:", self.f_stop); hw_layout.addRow("Freq Step:", self.f_step)
        self.g_start = Qt.QLineEdit("30"); self.g_stop = Qt.QLineEdit("70"); self.g_step = Qt.QLineEdit("5")
        hw_layout.addRow("TX Gain Start:", self.g_start); hw_layout.addRow("TX Gain Stop:", self.g_stop); hw_layout.addRow("TX Gain Step:", self.g_step)
        self.scroll_layout.addWidget(hw_box)

        # Operational View Config
        ana_box = Qt.QGroupBox("Operational Table Settings")
        ana_layout = Qt.QFormLayout(); ana_box.setLayout(ana_layout)
        self.p_start = Qt.QLineEdit("-20"); self.p_stop = Qt.QLineEdit("30"); self.p_step = Qt.QLineEdit("5")
        ana_layout.addRow("Target Min dBm:", self.p_start); ana_layout.addRow("Target Max dBm:", self.p_stop); ana_layout.addRow("Target Step dB:", self.p_step)
        self.view_select = Qt.QComboBox(); self.view_select.addItems(["Measurement View", "Operational View"]); self.view_select.currentIndexChanged.connect(self.update_plot)
        ana_layout.addRow("View Type:", self.view_select)
        self.scroll_layout.addWidget(ana_box)

        # Analysis Tools
        data_box = Qt.QGroupBox("Analysis Tools")
        data_layout = Qt.QVBoxLayout(); data_box.setLayout(data_layout)
        self.table_btn = Qt.QPushButton("OPEN DATA TABLE"); self.table_btn.clicked.connect(self.show_table_window); data_layout.addWidget(self.table_btn)
        self.csv_btn = Qt.QPushButton("EXPORT CSV"); self.csv_btn.clicked.connect(self.export_csv); data_layout.addWidget(self.csv_btn)
        self.scroll_layout.addWidget(data_box)

        self.start_btn = Qt.QPushButton("START CALIBRATION"); self.start_btn.setStyleSheet("background-color: #050; color: white; font-weight: bold; height: 40px;"); self.start_btn.clicked.connect(self.toggle_calibration); self.left_panel.addWidget(self.start_btn)
        self.status_label = Qt.QLabel("Status: READY"); self.status_label.setStyleSheet("font-family: monospace; background: black; color: #0F0; padding: 5px;"); self.left_panel.addWidget(self.status_label)
        self.progress = Qt.QProgressBar(); self.left_panel.addWidget(self.progress)
        self.log_area = Qt.QTextEdit(); self.log_area.setReadOnly(True); self.log_area.setStyleSheet("background: #111; color: white; font-family: monospace;"); self.left_panel.addWidget(self.log_area)
        self.layout.addLayout(self.left_panel, stretch=1)
        
        self.figure = plt.figure(figsize=(10, 12)); self.canvas = FigureCanvas(self.figure); self.layout.addWidget(self.canvas, stretch=2)
        self.timer = QtCore.QTimer(); self.timer.timeout.connect(self.run_auto_step)
        self.load_presets_from_file()

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
                "tx_serial": self.tx_serial.text(), "rx_mode": self.rx_mode.currentText(), "rx_serial": self.rx_serial.text(),
                "f_start": self.f_start.text(), "f_stop": self.f_stop.text(), "f_step": self.f_step.text(),
                "g_start": self.g_start.text(), "g_stop": self.g_stop.text(), "g_step": self.g_step.text(),
                "atten": self.atten_ext.text(), "p_start": self.p_start.text(), "p_stop": self.p_stop.text(), "p_step": self.p_step.text()
            }
            with open(self.preset_file, 'w') as f: json.dump(self.presets, f, indent=4)
            self.load_presets_from_file(); self.preset_combo.setCurrentText(name)

    def delete_current_preset(self):
        name = self.preset_combo.currentText()
        if name in self.presets: del self.presets[name]; json.dump(self.presets, open(self.preset_file, 'w'), indent=4); self.load_presets_from_file()

    def load_selected_preset(self, name):
        if name in self.presets:
            p = self.presets[name]
            self.tx_serial.setText(p.get("tx_serial", "")); self.rx_mode.setCurrentText(p.get("rx_mode", "USRP (UHD)"))
            self.rx_serial.setText(p.get("rx_serial", "")); self.atten_ext.setText(p.get("atten", "30"))
            self.f_start.setText(p.get("f_start", "")); self.f_stop.setText(p.get("f_stop", "")); self.f_step.setText(p.get("f_step", ""))
            self.g_start.setText(p.get("g_start", "")); self.g_stop.setText(p.get("g_stop", "")); self.g_step.setText(p.get("g_step", ""))
            self.p_start.setText(p.get("p_start", "-20")); self.p_stop.setText(p.get("p_stop", "30")); self.p_step.setText(p.get("p_step", "5"))

    def log(self, msg): self.log_area.append(f"[{time.strftime('%H:%M:%S')}] {msg}")

    def toggle_calibration(self):
        if self.is_running: self.stop_calibration()
        else: self.start_calibration()

    def start_calibration(self):
        try:
            self.sweep_freqs = np.arange(float(eval(self.f_start.text())), float(eval(self.f_stop.text())) + 1, float(eval(self.f_step.text())))
            self.sweep_gains = np.arange(float(self.g_start.text()), float(self.g_stop.text()) + 1, float(self.g_step.text()))
            self.current_step = 0; self.results = {}
            self.tb = TransmitBlock(serial=self.tx_serial.text()); self.tb.start()
            if self.rx_mode.currentText() == "USRP (UHD)":
                self.rb = ReceiveBlock(serial=self.rx_serial.text()); self.rb.start(); self.timer.start(800)
            self.is_running = True; self.start_btn.setText("STOP"); self.progress.setMaximum(len(self.sweep_freqs) * len(self.sweep_gains))
        except Exception as e: self.log(f"ERROR: {e}"); traceback.print_exc(); self.stop_calibration()

    def stop_calibration(self):
        self.is_running = False; self.timer.stop(); self.start_btn.setText("START"); self.start_btn.setStyleSheet("background-color: #050; color: white;")
        try:
            if self.tb: self.tb.stop(); self.tb.wait(); self.tb = None
            if self.rb: self.rb.stop(); self.rb.wait(); self.rb = None
        except: pass

    def run_auto_step(self):
        if not self.is_running: return
        f_idx = self.current_step // len(self.sweep_gains); g_idx = self.current_step % len(self.sweep_gains)
        if f_idx >= len(self.sweep_freqs): self.finish_calibration(); return
        freq = self.sweep_freqs[f_idx]; gain = self.sweep_gains[g_idx]
        self.tb.set_freq(freq); self.tb.set_gain(gain)
        measured_db = -100
        if self.rb:
            self.rb.set_freq(freq); time.sleep(0.3); samples = self.rb.get_data()
            if samples is not None: measured_db = 10 * np.log10(np.abs(np.fft.fft(samples))**2 / len(samples) + 1e-12).max()
        actual_dbm = measured_db + float(self.atten_ext.text())
        if freq not in self.results: self.results[freq] = {}
        self.results[freq][gain] = actual_dbm
        self.log(f"F: {freq/1e6:.1f}M | G: {gain} | P: {actual_dbm:.1f} dBm")
        self.current_step += 1; self.progress.setValue(self.current_step)
        if self.current_step % 10 == 0: self.update_plot()

    def get_operational_data(self):
        f_list = sorted(self.results.keys()); g_sweep = sorted(self.sweep_gains)
        p_targets = np.arange(float(self.p_start.text()), float(self.p_stop.text()) + 1, float(self.p_step.text()))
        gain_matrix = np.zeros((len(f_list), len(p_targets)))
        for i, f in enumerate(f_list):
            measured_powers = [self.results[f][g] for g in g_sweep]
            gain_matrix[i, :] = np.interp(p_targets, measured_powers, g_sweep, left=np.nan, right=np.nan)
        return f_list, p_targets, gain_matrix

    def update_plot(self):
        self.figure.clear()
        if not self.results: return
        ax = self.figure.add_subplot(111)
        if "Operational" in self.view_select.currentText():
            f_list, p_targets, gain_matrix = self.get_operational_data()
            im = ax.imshow(gain_matrix, aspect='auto', extent=[p_targets[0], p_targets[-1], f_list[-1]/1e6, f_list[0]/1e6], cmap='gnuplot2')
            ax.set_xlabel("Target Power (dBm)"); self.figure.colorbar(im, label="Required Gain (dB)")
        else:
            f_list = sorted(self.results.keys()); g_sweep = sorted(self.sweep_gains); data = np.zeros((len(f_list), len(g_sweep)))
            for i, f in enumerate(f_list):
                for j, g in enumerate(g_sweep): data[i, j] = self.results[f].get(g, -100)
            im = ax.imshow(data, aspect='auto', extent=[g_sweep[0], g_sweep[-1], f_list[-1]/1e6, f_list[0]/1e6], cmap='plasma')
            ax.set_xlabel("USRP Gain (dB)"); self.figure.colorbar(im, label="Measured dBm")
        ax.set_ylabel("Frequency (MHz)"); self.canvas.draw()

    def show_table_window(self):
        if not self.results: return
        f_list, p_targets, gain_matrix = self.get_operational_data()
        self.table_win = TableWindow(f_list, p_targets, gain_matrix); self.table_win.show()

    def export_csv(self):
        if not self.results: return
        f_list, p_targets, gain_matrix = self.get_operational_data()
        path, _ = Qt.QFileDialog.getSaveFileName(self, "Export Table", "calibration_table.csv", "CSV Files (*.csv)")
        if path:
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f); writer.writerow(["Freq (MHz) \\ Target dBm"] + [f"{p} dBm" for p in p_targets])
                for i, freq in enumerate(f_list): writer.writerow([f"{freq/1e6:.2f}"] + list(gain_matrix[i, :]))
            self.log(f"CSV Exported: {path}")

    def finish_calibration(self):
        self.stop_calibration(); save_data = {"matrix": {str(k): v for k, v in self.results.items()}, "p_range": [float(self.p_start.text()), float(self.p_stop.text()), float(self.p_step.text())]}
        with open("calibration_matrix.json", "w") as f: json.dump(save_data, f, indent=4)
        self.log("Complete!"); self.update_plot()

if __name__ == '__main__':
    app = Qt.QApplication(sys.argv); window = SystemCalibrator(); window.show(); sys.exit(app.exec_())
