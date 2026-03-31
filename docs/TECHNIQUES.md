# Predator Interdiction Techniques

## 1. Narrowband / Wideband Noise
Traditional "wash" jamming. Tunable from 100 kHz up to 56 MHz (SDR dependent).

## 2. Distributed Bandwidth Expansion (+BW)
Uses two separate SDRs (e.g., dual B205s) to "Spectral Stitch" a continuous 40 MHz tactical block. The secondary SDR is automatically offset by the sample rate to double the reactive coverage area.

## 3. WiFi Preamble Sabotage
Protocol-aware interdiction targeting 802.11b/g/n preambles.
- **Mechanics:** Injects 11-chip Barket code or OFDM pilots to "blind" the receiver's AGC and synchronization before payload delivery.
- **Timing:** Synchronized via the C++ native core to ensure sub-millisecond precision.

## 4. Differential Comb
A phase-inverted multi-tone attack designed to defeat frequency-hopping and noise-canceling counter-measures by creating high-density spectral "dead zones."
