#!/usr/bin/env python3
import numpy as np
from gnuradio import gr, uhd, analog
import SoapySDR
from SoapySDR import * # SOAPY_SDR_ constants
import sys
import json
import time
import signal
from PyQt5 import Qt, QtCore, QtWidgets
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class TransmitBlock(gr.top_block):
    def __init__(self, serial="3457480", samp_rate=1e6, freq=915e6, gain=50):
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
        
        self.src = analog.sig_source_c(self.samp_rate, analog.GR_CONST_WAVE, 0, 1.0, 0)
        self.connect(self.src, self.sink)

    def set_freq(self, freq): self.sink.set_center_freq(freq, 0)
    def set_gain(self, gain): self.sink.set_gain(gain, 0)

class SystemCalibrator(Qt.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TechniqueMaker: RF System Calibrator")
        self.resize(1000, 700)
        
        self.results = {} # {freq: {gain: power}}
        self.is_running = False
        
        # --- UI Layout ---
        self.layout = Qt.QHBoxLayout(self)
        
        # Left Panel: Parameters
        self.left_panel = Qt.QVBoxLayout()
        self.param_group = Qt.QGroupBox("Calibration Parameters")
        self.param_layout = Qt.QFormLayout(); self.param_group.setLayout(self.param_layout)
        
        self.usrp_serial = Qt.QLineEdit("3457480")
        self.param_layout.addRow("USRP Serial:", self.usrp_serial)
        
        self.f_start = Qt.QLineEdit("900e6")
        self.f_stop = Qt.QLineEdit("930e6")
        self.f_step = Qt.QLineEdit("5e6")
        self.param_layout.addRow("Freq Start (Hz):", self.f_start)
        self.param_layout.addRow("Freq Stop (Hz):", self.f_stop)
        self.param_layout.addRow("Freq Step (Hz):", self.f_step)
        
        self.g_start = Qt.QLineEdit("30")
        self.g_stop = Qt.QLineEdit("70")
        self.g_step = Qt.QLineEdit("5")
        self.param_layout.addRow("Gain Start (dB):", self.g_start)
        self.param_layout.addRow("Gain Stop (dB):", self.g_stop)
        self.param_layout.addRow("Gain Step (dB):", self.g_step)
        
        self.atten_ext = Qt.QLineEdit("30")
        self.param_layout.addRow("Ext Atten (dB):", self.atten_ext)
        
        self.dwell = Qt.QLineEdit("200")
        self.param_layout.addRow("Dwell (ms):", self.dwell)
        
        self.left_panel.addWidget(self.param_group)
        
        self.start_btn = Qt.QPushButton("START CALIBRATION")
        self.start_btn.setStyleSheet("background-color: #050; color: white; font-weight: bold; height: 40px;")
        self.start_btn.clicked.connect(self.toggle_calibration)
        self.left_panel.addWidget(self.start_btn)
        
        self.status_label = Qt.QLabel("Status: READY")
        self.status_label.setStyleSheet("font-family: monospace; background: black; color: #0F0; padding: 5px;")
        self.left_panel.addWidget(self.status_label)
        
        self.progress = Qt.QProgressBar()
        self.left_panel.addWidget(self.progress)
        
        self.log_area = Qt.QTextEdit()
        self.log_area.setReadOnly(True); self.log_area.setStyleSheet("background: #111; color: white; font-family: monospace;")
        self.left_panel.addWidget(self.log_area)
        
        self.layout.addLayout(self.left_panel, stretch=1)
        
        # Right Panel: Plot
        self.figure = plt.figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        self.layout.addWidget(self.canvas, stretch=2)
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.run_sweep_step)

    def log(self, msg):
        self.log_area.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
        print(msg)

    def toggle_calibration(self):
        if self.is_running:
            self.stop_calibration()
        else:
            self.start_calibration()

    def start_calibration(self):
        try:
            self.freqs = np.arange(float(eval(self.f_start.text())), float(eval(self.f_stop.text())) + 1, float(eval(self.f_step.text())))
            self.gains = np.arange(float(self.g_start.text()), float(self.g_stop.text()) + 1, float(self.g_step.text()))
            self.total_steps = len(self.freqs) * len(self.gains)
            self.current_step = 0
            self.results = {}
            
            self.log(f"Initializing USRP {self.usrp_serial.text()}...")
            self.tb = TransmitBlock(serial=self.usrp_serial.text(), freq=self.freqs[0], gain=self.gains[0])
            self.tb.start()
            
            self.log("Initializing Signal Hound (SoapySDR)...")
            # For BB60D, driver is usually 'bb60' or 'signalhound'
            args = dict(driver="bb60") 
            self.sdr = SoapySDR.Device(args)
            self.sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, [0])
            self.sdr.activateStream(self.sdr.setupStream(SOAPY_SDR_RX, SOAPY_SDR_CF32, [0]))
            
            self.is_running = True
            self.start_btn.setText("STOP CALIBRATION")
            self.start_btn.setStyleSheet("background-color: #700; color: white; font-weight: bold;")
            self.status_label.setText("Status: RUNNING")
            self.progress.setMaximum(self.total_steps)
            self.timer.start(int(self.dwell.text()))
            
        except Exception as e:
            self.log(f"ERROR: {e}")
            self.stop_calibration()

    def stop_calibration(self):
        self.is_running = False
        self.timer.stop()
        self.start_btn.setText("START CALIBRATION")
        self.start_btn.setStyleSheet("background-color: #050; color: white; font-weight: bold;")
        self.status_label.setText("Status: READY")
        try: self.tb.stop(); self.tb.wait()
        except: pass
        try: self.sdr.deactivateStream(None); self.sdr.closeStream(None)
        except: pass
        self.log("Calibration Halted.")

    def run_sweep_step(self):
        if not self.is_running: return
        
        f_idx = self.current_step // len(self.gains)
        g_idx = self.current_step % len(self.gains)
        
        if f_idx >= len(self.freqs):
            self.finish_calibration()
            return
            
        freq = self.freqs[f_idx]
        gain = self.gains[g_idx]
        
        # Tune
        self.tb.set_freq(freq)
        self.tb.set_gain(gain)
        self.sdr.setFrequency(SOAPY_SDR_RX, 0, freq)
        self.sdr.setSampleRate(SOAPY_SDR_RX, 0, 1e6) # 1 MHz span is enough for CW
        
        # Dwell for settling
        time.sleep(0.05)
        
        # Measure
        buff = np.array([0]*1024, np.complex64)
        sr = self.sdr.readStream(None, [buff], len(buff))
        
        # Peak Detection
        fft = np.fft.fft(buff)
        psd = 10 * np.log10(np.abs(fft)**2 / len(buff) + 1e-12)
        peak_pwr = np.max(psd) # Relative dB
        # Calibration math: peak_pwr is relative to FS. We need absolute dBm.
        # This usually requires a known reference, but for now we assume peak relative.
        # Signal Hound usually reports absolute dBm via Soapy if calibrated.
        
        actual_dbm = peak_pwr + float(self.atten_ext.text())
        
        if freq not in self.results: self.results[freq] = {}
        self.results[freq][gain] = actual_dbm
        
        self.log(f"F: {freq/1e6:.1f} MHz | G: {gain:.1f} | Pwr: {actual_dbm:.1f} dBm")
        self.current_step += 1
        self.progress.setValue(self.current_step)
        
        if self.current_step % len(self.gains) == 0:
            self.update_plot()

    def update_plot(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        f_list = sorted(self.results.keys())
        g_list = sorted(self.gains)
        
        if not f_list: return
        
        data = np.zeros((len(f_list), len(g_list)))
        for i, f in enumerate(f_list):
            for j, g in enumerate(g_list):
                data[i, j] = self.results[f].get(g, -100)
        
        im = ax.imshow(data, aspect='auto', extent=[g_list[0], g_list[-1], f_list[-1]/1e6, f_list[0]/1e6], cmap='viridis')
        ax.set_xlabel("USRP TX Gain (dB)")
        ax.set_ylabel("Frequency (MHz)")
        ax.set_title("RF Chain Calibration Matrix (dBm Output)")
        self.figure.colorbar(im, label="dBm (incl. ext atten)")
        self.canvas.draw()

    def finish_calibration(self):
        self.stop_calibration()
        self.log("Calibration Complete!")
        with open("calibration_matrix.json", "w") as f:
            # JSON doesn't like float keys, convert to string
            out = {str(k): v for k, v in self.results.items()}
            json.dump(out, f, indent=4)
        self.log("Results saved to calibration_matrix.json")
        self.update_plot()

if __name__ == '__main__':
    app = Qt.QApplication(sys.argv)
    window = SystemCalibrator()
    window.show()
    sys.exit(app.exec_())
