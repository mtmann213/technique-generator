import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# 1. Add the OOT module to the path so we can import the latest BaseWaveforms
sys.path.append(os.path.abspath("./gr-techniquemaker/python/techniquemaker"))
import BaseWaveforms as bw

def plot_technique(samples, sample_rate, title):
    """Utility to plot time and freq domain."""
    num_samples = len(samples)
    time = np.arange(num_samples) / sample_rate
    
    plt.figure(figsize=(12, 6))
    
    # Time Domain (Real part)
    plt.subplot(2, 1, 1)
    plt.plot(time * 1000, np.real(samples))
    plt.title(f"{title} - Time Domain (Real)")
    plt.xlabel("Time (ms)")
    plt.ylabel("Amplitude")
    plt.grid(True)
    
    # Frequency Domain (PSD)
    plt.subplot(2, 1, 2)
    plt.psd(samples, NFFT=1024, Fs=sample_rate/1e3, color='r')
    plt.title(f"{title} - Power Spectral Density")
    plt.xlabel("Frequency (kHz)")
    plt.ylabel("dB/Hz")
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    samp_rate = 1e6
    duration = 0.05 # 50ms for a quick look
    
    print("Generating LFM Chirp (-200kHz to 200kHz)...")
    lfm = bw.lfm_chirp(-200e3, 200e3, samp_rate, duration)
    plot_technique(lfm, samp_rate, "LFM Chirp")
    
    print("Generating FHSS Noise (Hops: -300k, 0, 300k)...")
    fhss = bw.fhss_noise("-300000 0 300000", 0.01, 50e3, samp_rate, duration)
    plot_technique(fhss, samp_rate, "FHSS Noise")
