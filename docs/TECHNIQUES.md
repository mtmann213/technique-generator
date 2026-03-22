# TechniqueMaker: Mathematical & Tactical Reference

This document provides the technical theory and tactical deployment guidelines for all synthesis algorithms and interdiction strategies within the suite.

---

## 1. Interdiction Strategies (The "Brains")

### 1.1 Hydra Auto-Surgical Comb (C++ Core)
The Hydra engine performs real-time spectral analysis using a high-speed windowed FFT pipeline in native C++.
*   **Detection:** Identifies "Energy Islands" crossing a user-defined power threshold (dB).
*   **Estimation:** Calculates the center frequency and -10dB bandwidth of every detected target.
*   **Synthesis:** Dynamically sums multiple interference "teeth" into a single output stream.
*   **Matched-Bandwidth Resampling:** Uses linear interpolation to scale the interference signal's width to perfectly match the target's spectral footprint, maximizing power-on-target efficiency.

### 1.2 Sticky Channel Denial (Persistent Trap)
Designed to counter frequency hoppers by "burning" their hopset one channel at a time.
*   **Persistent Latching:** Once a hopper hits a frequency, that channel is added to a persistent list and jammed continuously until manually reset.
*   **Gated Look-through:** Implements a duty-cycle (e.g., 90ms Jam / 10ms Silence). During the silence window, the C++ core scans for *new* hops without self-interference.

---

## 2. Signal Templates (The "Warheads")

### 2.1 Differential Comb
A high-precision technique that generates narrow spectral spikes at exact intervals.
*   **Theory:** $x(t) = \sum A \cdot e^{j(2\pi \cdot k \cdot \Delta f \cdot t + \phi_k)}$
*   **Tactical Use:** Disruption of specific subcarrier architectures (e.g., 15kHz or 30kHz) in OFDM-based datalinks.

### 2.2 Narrowband Noise
Band-limited white Gaussian noise (AWGN) filtered to match the target's bandwidth.
*   **Tactical Use:** General-purpose disruption of analog or simple digital modulations.

### 2.3 Correlator Confusion
Generates phase-inverted preamble sequences to trigger false correlations in C++ based receivers.
*   **Tactical Use:** Breaking the FFT window alignment in OFDM depacketizers.

---

## 3. High-Performance C++ Engine
The core interdiction logic is implemented in native C++ to bypass the Python Global Interpreter Lock (GIL).
*   **Supported Bandwidths:** Optimized for 20MHz+ real-time processing.
*   **Graceful Fallback:** Automatic detection of C++ binaries with seamless transition to Python-based math if needed.
