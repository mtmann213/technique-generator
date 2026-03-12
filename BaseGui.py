import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from numpy.typing import NDArray
import json
import hashlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import BaseWaveforms

# --- File Writing Functions ---

def numpy_complex_to_binary_file(complex_array: NDArray, filename: str):
    """Saves a complex NumPy array to a raw binary file (cf32)."""
    np.asarray(complex_array, dtype=np.complex64).tofile(filename)
    print(f"Saved binary file: {filename}")

def numpy_complex_to_binary_file_int(complex_array: NDArray, filename: str):
    """Saves a complex NumPy array to an interleaved 16-bit signed integer binary file."""
    complex_array = np.asarray(complex_array, dtype=np.complex64)
    interleaved_data = np.stack((complex_array.real, complex_array.imag), axis=-1).flatten()
    max_val = np.max(np.abs(interleaved_data))
    if max_val == 0:
        interleaved_data = interleaved_data.astype(np.int16)
    else:
        interleaved_data = np.round(interleaved_data / max_val * 32000).astype(np.int16)
    interleaved_data.astype('>i2').tofile(filename)
    print(f"Saved integer binary file: {filename}")

def numpy_complex_to_sigmf_file(
    complex_array: NDArray,
    filename_prefix: str,
    sample_rate_hz: float,
    center_frequency_hz: float = 0.0,
    description: str = "Generated signal"
):
    """Writes a NumPy array to a SigMF compliant .sigmf-data and .sigmf-meta file pair."""
    data_filename = f"{filename_prefix}.sigmf-data"
    meta_filename = f"{filename_prefix}.sigmf-meta"
    np.asarray(complex_array, dtype=np.complex64).tofile(data_filename)
    sha512_hash = hashlib.sha512()
    with open(data_filename, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha512_hash.update(byte_block)
    data_sha512 = sha512_hash.hexdigest()
    metadata = {
        "global": {
            "core:datatype": "cf32",
            "core:sample_rate": sample_rate_hz,
            "core:version": "1.0.1",
            "core:sha512": data_sha512,
            "core:description": description
        },
        "captures": [
            {
                "core:sample_start": 0,
                "core:frequency": center_frequency_hz
            }
        ],
        "annotations": []
    }
    with open(meta_filename, 'w') as f:
        json.dump(metadata, f, indent=4)
    print(f"SigMF data written to '{data_filename}' and metadata to '{meta_filename}'.")

def infer_type_from_string(s: str):
    s = s.strip()
    if not s: return s
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s

# --- The GUI Application Class ---
class WaveformApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TechniqueMaker GUI")
        self.geometry("900x700") # Increased size for Preview window

        self.waveform_definitions = BaseWaveforms.waveform_definitions

        self.file_format_definitions = {
            "Raw Complex Binary (cf32)": {"func": numpy_complex_to_binary_file, "ext": ".bin"},
            "Scaled Integer Binary (i16)": {"func": numpy_complex_to_binary_file_int, "ext": ".WAVEFORM"},
            "SigMF (.sigmf-data)": {"func": numpy_complex_to_sigmf_file, "ext": ".sigmf-data"}
        }

        self.param_widgets = []
        self.param_vars = {}
        self.create_widgets()

    def create_widgets(self):
        # Left side: Parameters, Right side: Plot
        self.paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill="both", expand=True)

        # --- Left Panel: Controls ---
        left_container = ttk.Frame(self.paned_window)
        self.paned_window.add(left_container, weight=1)

        main_canvas = tk.Canvas(left_container)
        scrollbar = ttk.Scrollbar(left_container, orient="vertical", command=main_canvas.yview)
        self.scrollable_frame = ttk.Frame(main_canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 1. Selection
        wf_frame = ttk.LabelFrame(self.scrollable_frame, text="1. Select Technique", padding="10")
        wf_frame.pack(fill="x", pady=5, padx=10)
        self.waveform_combobox = ttk.Combobox(wf_frame, values=list(self.waveform_definitions.keys()), state="readonly")
        self.waveform_combobox.pack(fill="x")
        self.waveform_combobox.set(list(self.waveform_definitions.keys())[0])
        self.waveform_combobox.bind("<<ComboboxSelected>>", self.update_parameters)

        # 2. Parameters
        self.param_frame = ttk.LabelFrame(self.scrollable_frame, text="2. Parameters", padding="10")
        self.param_frame.pack(fill="x", pady=5, padx=10)
        self.update_parameters()

        # 3. Format
        fmt_frame = ttk.LabelFrame(self.scrollable_frame, text="3. Output Format", padding="10")
        fmt_frame.pack(fill="x", pady=5, padx=10)
        self.format_combobox = ttk.Combobox(fmt_frame, values=list(self.file_format_definitions.keys()), state="readonly")
        self.format_combobox.pack(fill="x")
        self.format_combobox.set(list(self.file_format_definitions.keys())[0])

        # 4. Actions
        btn_frame = ttk.Frame(self.scrollable_frame, padding=10)
        btn_frame.pack(fill="x")
        
        self.preview_btn = ttk.Button(btn_frame, text="Update Preview", command=self.update_preview)
        self.preview_btn.pack(side="top", fill="x", pady=2)
        
        self.save_btn = ttk.Button(btn_frame, text="Generate and Save File", command=self.generate_and_save)
        self.save_btn.pack(side="top", fill="x", pady=2)

        self.status_label = ttk.Label(self.scrollable_frame, text="Ready", relief="sunken", anchor="w")
        self.status_label.pack(side="bottom", fill="x", ipady=2)

        # --- Right Panel: Plot ---
        self.plot_container = ttk.Frame(self.paned_window, padding=10)
        self.paned_window.add(self.plot_container, weight=2)
        
        self.fig, (self.ax_time, self.ax_freq) = plt.subplots(2, 1, figsize=(5, 8))
        self.fig.tight_layout(pad=3.0)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_container)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def update_parameters(self, event=None):
        for widget in self.param_widgets: widget.destroy()
        self.param_widgets.clear()
        self.param_vars.clear()

        wf_name = self.waveform_combobox.get()
        wf_info = self.waveform_definitions[wf_name]
        
        for p in wf_info["params"]:
            f = ttk.Frame(self.param_frame); f.pack(fill="x", pady=2); self.param_widgets.append(f)
            ttk.Label(f, text=f"{p['title']}:").pack(side="left", padx=5)
            var = tk.StringVar(); self.param_vars[p['name']] = var
            if p['type'] == "options":
                cb = ttk.Combobox(f, textvariable=var, values=p['choices'], state="readonly")
                cb.pack(side="right", fill="x", expand=True); cb.set(p['choices'][0])
                self.param_widgets.append(cb)
            else:
                ent = ttk.Entry(f, textvariable=var); ent.pack(side="right", fill="x", expand=True)
                if p['name'] == 'sample_rate_hz': var.set("1000000")
                elif p['name'] == 'technique_length_seconds': var.set("0.1")
                elif p['name'] == 'target_value': var.set("1.0")
                elif p['name'] == 'bandwidth_hz': var.set("100000")
                self.param_widgets.append(ent)

    def update_preview(self):
        """Generates signal and updates the plot."""
        try:
            wf_name = self.waveform_combobox.get()
            wf_def = self.waveform_definitions[wf_name]
            params = {name: infer_type_from_string(var.get()) for name, var in self.param_vars.items()}
            
            samples = wf_def["func"](**params)
            fs = params.get('sample_rate_hz', 1e6)
            
            # Time Domain
            self.ax_time.clear()
            t = np.arange(len(samples)) / fs
            self.ax_time.plot(t * 1000, np.real(samples), label="Real")
            self.ax_time.set_title(f"Time Domain: {wf_name}")
            self.ax_time.set_xlabel("Time (ms)")
            self.ax_time.set_ylabel("Amplitude")
            self.ax_time.grid(True)
            
            # Freq Domain
            self.ax_freq.clear()
            self.ax_freq.psd(samples, NFFT=1024, Fs=fs/1e3, color='r')
            self.ax_freq.set_title("Power Spectral Density")
            self.ax_freq.set_xlabel("Frequency (kHz)")
            self.ax_freq.set_ylabel("dB/Hz")
            self.ax_freq.grid(True)
            
            self.fig.tight_layout(pad=3.0)
            self.canvas.draw()
            self.status_label.config(text="Preview updated.")
        except Exception as e:
            messagebox.showerror("Preview Error", str(e))

    def generate_and_save(self):
        self.status_label.config(text="Generating...")
        try:
            wf_name = self.waveform_combobox.get()
            fmt_name = self.format_combobox.get()
            wf_def = self.waveform_definitions[wf_name]
            fmt_def = self.file_format_definitions[fmt_name]

            params = {name: infer_type_from_string(var.get()) for name, var in self.param_vars.items()}
            filename = filedialog.asksaveasfilename(defaultextension=fmt_def["ext"])
            if not filename: return

            samples = wf_def["func"](**params)
            save_func = fmt_def["func"]
            
            if "SigMF" in fmt_name:
                save_func(samples, filename_prefix=filename.rsplit('.', 1)[0], 
                          sample_rate_hz=params.get('sample_rate_hz', 1e6),
                          description=f"TechniqueMaker: {wf_name}")
            else:
                save_func(samples, filename=filename)

            self.status_label.config(text=f"Saved to {filename}")
            messagebox.showinfo("Success", f"Generated {len(samples)} samples successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = WaveformApp()
    app.mainloop()
