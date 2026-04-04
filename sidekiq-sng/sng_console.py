#!/usr/bin/env python3
import subprocess
import os
import sys

class SidekiqSngConsole:
    def __init__(self):
        self.settings = {
            "freq": "2412e6",
            "rate": "2e6",
            "bw": "1e6",
            "gain": "15",
            "chan": "0",
            "amp": "0.2",
            "len": "0.1"
        }
        self.tech = "noise"
        self.tech_params = {}

    def clear(self):
        os.system('clear' if os.name == 'posix' else 'cls')

    def header(self):
        print("="*60)
        print("  SIDEKIQ-SNG TACTICAL CONSOLE v2.2 (AIR-GAP EDITION)")
        print("="*60)

    def main_menu(self):
        while True:
            self.clear()
            self.header()
            print(f" [1] PROBE Hardware Ports")
            print(f" [2] TEST Port 0 (Blink)")
            print(f" [3] TEST Port 1 (Blink)")
            print(f" [4] TEST Port 2 (Blink)")
            print(f" [5] TEST Port 3 (Blink)")
            print("-" * 60)
            print(f" [R] RADIO SETTINGS (Freq:{self.settings['freq']}, Rate:{self.settings['rate']}, Chan:{self.settings['chan']})")
            print(f" [T] TECHNIQUE: {self.tech}")
            print("-" * 60)
            print(f" [S] START STREAMING")
            print(f" [G] Generate to File")
            print(f" [Q] Quit")
            print("="*60)
            
            choice = input("Select Option > ").lower()
            
            if choice == '1': self.run_cmd(["./sng", "--probe"])
            elif choice == '2': self.test_port(0)
            elif choice == '3': self.test_port(1)
            elif choice == '4': self.test_port(2)
            elif choice == '5': self.test_port(3)
            elif choice == 'r': self.configure_rf()
            elif choice == 't': self.configure_tech()
            elif choice == 's': self.execute(stream=True)
            elif choice == 'g': self.execute(stream=False)
            elif choice == 'q': break
            
            if choice in ['1', '2', '3', '4', '5', 's', 'g']:
                input("\nPress Enter to return to menu...")

    def configure_rf(self):
        self.clear()
        self.header()
        print("--- Global RF Configuration ---")
        for k, v in self.settings.items():
            new_val = input(f" {k} [{v}] > ")
            if new_val: self.settings[k] = new_val

    def configure_tech(self):
        self.clear()
        self.header()
        techs = ["noise", "phase-noise", "comb", "chirp", "ofdm", "fhss", "confusion", "noise-tones", "chunked-noise", "rrc", "fm-cosine"]
        print("Available Techniques:")
        for i, t in enumerate(techs): print(f" [{i}] {t}")
        
        idx = input("\nSelect Index > ")
        if idx.isdigit() and int(idx) < len(techs):
            self.tech = techs[int(idx)]
            self.update_tech_params()

    def update_tech_params(self):
        self.tech_params = {}
        t = self.tech
        params = []
        if t == "fhss": params = [("hops", "-200k 0 200k"), ("hop-dur", "0.01")]
        elif t == "comb": params = [("spacing", "30000"), ("spikes", "10")]
        elif t == "phase-noise": params = [("shift", "180"), ("shift-rate", "1000")]
        elif t == "fm-cosine": params = [("mod-rate", "1000")]
        elif t == "chunked-noise": params = [("sweep-rate", "1000"), ("spikes", "10")]
        elif t == "rrc": params = [("rolloff", "0.35")]
        elif t == "confusion": params = [("pulse-gap", "10"), ("mode", "both")]
        elif t == "noise-tones": params = [("hops", "-1M 0 1M")]
        
        if params:
            print(f"\n--- {t.upper()} Parameters ---")
            for k, default in params:
                val = input(f" {k} [{default}] > ")
                self.tech_params[k] = val if val else default

    def execute(self, stream=False):
        cmd = ["./sng", "--tech", self.tech]
        for k, v in self.settings.items(): cmd.extend([f"--{k}", v])
        for k, v in self.tech_params.items(): cmd.extend([f"--{k}", v])
        if stream: cmd.append("--stream")
        self.run_cmd(cmd)

    def run_cmd(self, cmd):
        print(f"\nExecuting: {' '.join(cmd)}")
        print("-" * 60)
        try:
            # We use check_call for probe/test, and just Popen for streaming so user can Ctrl+C
            subprocess.check_call(cmd)
        except KeyboardInterrupt:
            print("\n[STOPPED] Transmission terminated by user.")
        except Exception as e:
            print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    if not os.path.exists("./sng"):
        print("Error: 'sng' binary not found. Run ./build_on_target.sh first.")
        sys.exit(1)
    SidekiqSngConsole().main_menu()
