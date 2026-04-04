#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import os

class SidekiqSngGui:
    def __init__(self, root):
        self.root = root
        self.root.title("Sidekiq-SNG Tactical Controller v2.2")
        self.root.geometry("900x750")
        
        # --- State ---
        self.process = None
        self.is_streaming = False
        
        self.setup_ui()
        self.update_params()

    def setup_ui(self):
        # Main Layout
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 1. Header & Diagnostics
        header_frame = ttk.LabelFrame(main_frame, text="Hardware Diagnostics", padding="5")
        header_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(header_frame, text="Probe Ports", command=self.probe_ports).pack(side=tk.LEFT, padx=5)
        ttk.Button(header_frame, text="Test Port 0 (Blink)", command=lambda: self.test_port(0)).pack(side=tk.LEFT, padx=5)
        ttk.Button(header_frame, text="Test Port 1 (Blink)", command=lambda: self.test_port(1)).pack(side=tk.LEFT, padx=5)

        # 2. Global RF Settings
        rf_frame = ttk.LabelFrame(main_frame, text="Radio Settings", padding="5")
        rf_frame.pack(fill=tk.X, pady=5)
        
        settings = [
            ("Center Freq (Hz):", "freq", "2412e6"),
            ("Sample Rate (Hz):", "rate", "2e6"),
            ("Bandwidth (Hz):", "bw", "1e6"),
            ("TX Gain (dB):", "gain", "15"),
            ("Channels (e.g. 0,1):", "chan", "0"),
            ("Amplitude (0-1):", "amp", "0.2")
        ]
        
        self.vars = {}
        for i, (label, key, default) in enumerate(settings):
            ttk.Label(rf_frame, text=label).grid(row=i//3, column=(i%3)*2, sticky=tk.W, padx=5)
            var = tk.StringVar(value=default)
            self.vars[key] = var
            ttk.Entry(rf_frame, textvariable=var, width=15).grid(row=i//3, column=(i%3)*2+1, padx=5, pady=2)

        # 3. Technique Selector
        tech_frame = ttk.LabelFrame(main_frame, text="Technique Selection", padding="5")
        tech_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(tech_frame, text="Select Technique:").pack(side=tk.LEFT, padx=5)
        self.tech_var = tk.StringVar(value="noise")
        self.tech_combo = ttk.Combobox(tech_frame, textvariable=self.tech_var, state="readonly")
        self.tech_combo['values'] = [
            "noise", "phase-noise", "comb", "chirp", "ofdm", 
            "fhss", "confusion", "noise-tones", "chunked-noise", "rrc", "fm-cosine"
        ]
        self.tech_combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.tech_combo.bind("<<ComboboxSelected>>", self.update_params)

        # 4. Technique Parameters
        self.param_frame = ttk.LabelFrame(main_frame, text="Technique Parameters", padding="5")
        self.param_frame.pack(fill=tk.X, pady=5)
        self.param_vars = {}

        # 5. Output Console
        console_frame = ttk.LabelFrame(main_frame, text="Console Output", padding="5")
        console_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.console = tk.Text(console_frame, height=10, bg="black", fg="lightgreen", font=("monospace", 10))
        self.console.pack(fill=tk.BOTH, expand=True)

        # 6. Action Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.stream_btn = ttk.Button(btn_frame, text="START STREAMING", command=self.toggle_stream)
        self.stream_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Button(btn_frame, text="Generate to File", command=self.generate_to_file).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(btn_frame, text="Stop / Kill", command=self.stop_process).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def update_params(self, event=None):
        # Clear existing
        for widget in self.param_frame.winfo_children():
            widget.destroy()
        self.param_vars = {}
        
        tech = self.tech_var.get()
        params = []
        
        if tech == "fhss":
            params = [("Hops (Hz):", "hops", "-200k 0 200k"), ("Hop Dur (s):", "hop-dur", "0.01")]
        elif tech == "comb":
            params = [("Spike Spacing (Hz):", "spacing", "30000"), ("Spike Count:", "spikes", "10")]
        elif tech == "phase-noise":
            params = [("Phase Shift (deg):", "shift", "180"), ("Shift Rate (Hz):", "shift-rate", "1000")]
        elif tech == "fm-cosine":
            params = [("Mod Rate (Hz):", "mod-rate", "1000")]
        elif tech == "chunked-noise":
            params = [("Sweep Rate (Hz/s):", "sweep-rate", "1000"), ("Chunks:", "spikes", "10")]
        elif tech == "rrc":
            params = [("Rolloff:", "rolloff", "0.35")]
        elif tech == "confusion":
            params = [("Pulse Gap (ms):", "pulse-gap", "10"), ("Mode:", "mode", "both")]
        elif tech == "noise-tones":
            params = [("Freqs (Hz):", "hops", "-1M 0 1M")]
            
        for i, (label, key, default) in enumerate(params):
            ttk.Label(self.param_frame, text=label).grid(row=i//2, column=(i%2)*2, sticky=tk.W, padx=5)
            var = tk.StringVar(value=default)
            self.param_vars[key] = var
            ttk.Entry(self.param_frame, textvariable=var, width=20).grid(row=i//2, column=(i%2)*2+1, padx=5, pady=2)

    def log(self, text):
        self.console.insert(tk.END, text + "\n")
        self.console.see(tk.END)

    def get_args(self):
        cmd = ["./sng", "--tech", self.tech_var.get()]
        for k, v in self.vars.items():
            cmd.extend([f"--{k}", v.get()])
        for k, v in self.param_vars.items():
            cmd.extend([f"--{k}", v.get()])
        return cmd

    def run_cmd(self, cmd):
        self.log(f"Running: {' '.join(cmd)}")
        try:
            self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            threading.Thread(target=self.read_output, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def read_output(self):
        for line in iter(self.process.stdout.readline, ''):
            self.root.after(0, self.log, line.strip())
        self.process.wait()
        self.root.after(0, self.on_process_finish)

    def on_process_finish(self):
        self.is_streaming = False
        self.stream_btn.config(text="START STREAMING")
        self.log("--- Process Finished ---")

    def toggle_stream(self):
        if self.is_streaming:
            self.stop_process()
        else:
            cmd = self.get_args()
            cmd.append("--stream")
            self.is_streaming = True
            self.stream_btn.config(text="STOP STREAMING")
            self.run_cmd(cmd)

    def stop_process(self):
        if self.process:
            self.process.terminate()
            self.log("--- Process Terminated ---")

    def generate_to_file(self):
        cmd = self.get_args()
        self.run_cmd(cmd)

    def probe_ports(self):
        self.run_cmd(["./sng", "--probe"])

    def test_port(self, index):
        cmd = ["./sng", "--tech", "noise", "--chan", str(index), "--bw", "1e6", "--rate", "2e6", "--amp", "0.2", "--stream"]
        self.log(f"--- Blinking Port {index} ---")
        self.run_cmd(cmd)

if __name__ == "__main__":
    root = tk.Tk()
    app = SidekiqSngGui(root)
    root.mainloop()
