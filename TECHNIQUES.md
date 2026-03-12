# TechniqueMaker: Signal Synthesis Reference Guide

This guide explains the 15 signal generation techniques available in TechniqueMaker, their mathematical foundations, and their primary use cases in Signal Intelligence (SIGINT) and communication system stress-testing.

---

## 1. Narrowband Noise
*   **Description:** Generates a flat block of White Gaussian Noise (WGN) centered at DC (0 Hz) with a specific bandwidth.
*   **How it works:** Creates noise in the frequency domain, masks it to the desired bandwidth, and uses an IFFT to return to the time domain.
*   **Use Case:** Basic Barrage Interference simulation or testing receiver sensitivity across a specific channel.

## 2. RRC Modulated Noise
*   **Description:** Noise passed through a Root-Raised Cosine (RRC) filter.
*   **How it works:** Uses a pulse-shaping filter to limit the bandwidth while maintaining "Nyquist" properties.
*   **Use Case:** Simulating the spectral footprint of modern digital communications (like QAM or PSK) without the complexity of actual data.

## 3. Swept Noise
*   **Description:** A narrowband noise column that "slides" across the spectrum.
*   **How it works:** Generates narrowband noise and multiplies it by a complex phasor whose frequency changes linearly over time (Sawtooth or Triangle).
*   **Use Case:** Simulating dynamic interferers which attempt to disrupt frequency-hopping targets by covering a wide range quickly.

## 4. Chunked Noise
*   **Description:** Divides a wide bandwidth into "chunks" and activates them in a randomized order.
*   **How it works:** Shifts a narrowband noise block to different center frequencies at regular intervals.
*   **Use Case:** Simulating coordinated narrowband interference or "Spot Jamming" on multiple channels.

## 5. Noise Tones
*   **Description:** Multiple narrowband noise signals placed at specific user-defined frequencies.
*   **How it works:** A sum of frequency-shifted noise blocks.
*   **Use Case:** Testing multi-carrier receivers or simulating interference on specific sub-bands.

## 6. Cosine / Phasor Tones
*   **Description:** Pure CW (Continuous Wave) tones. Cosine is real-valued; Phasor is complex ($e^{j \omega t}$).
*   **Use Case:** Basic carrier injection, LO (Local Oscillator) leakage simulation, or simple tone-interference.

## 7. Swept Cosines / Phasors
*   **Description:** Pure tones that ramp up or down in frequency.
*   **Use Case:** Simulating radar "Chirps" or testing the tracking speed of a Phase-Locked Loop (PLL).

## 8. FM Cosine
*   **Description:** A tone whose frequency is modulated by another lower-frequency cosine.
*   **How it works:** Standard Frequency Modulation (FM) math: $\cos(2\pi f_c t + \beta \sin(2\pi f_m t))$.
*   **Use Case:** Simulating analog FM voice communications or vibrato effects in audio.

## 9. LFM Chirp
*   **Description:** Linear Frequency Modulation (LFM).
*   **How it works:** The frequency increases linearly from a "Start" to an "End" frequency over the duration of the burst.
*   **Use Case:** The standard radar pulse. Used for pulse compression and range resolution testing.

## 10. FHSS Noise
*   **Description:** Frequency Hopping Spread Spectrum (FHSS) noise bursts.
*   **How it works:** Randomly (or sequentially) hops a narrowband noise signal between a list of frequencies.
*   **Use Case:** Simulating Bluetooth, WiFi, or tactical radios that use frequency hopping to avoid detection.

## 11. OFDM-Shaped Noise
*   **Description:** Noise that perfectly mimics the spectral shape of an OFDM signal.
*   **How it works:** Populates specific subcarriers in the frequency domain and adds a Cyclic Prefix (CP) in the time domain.
*   **Use Case:** Testing 4G/5G or WiFi receivers against "Smart Interference" that matches the signal's own structure.

## 12. Song Maker
*   **Description:** Converts a musical melody into a sequence of narrowband noise bursts.
*   **How it works:** Maps musical notes to frequencies and durations, generating a filtered noise burst for each note.
*   **Use Case:** Verification of receiver frequency alignment by generating a recognizable audio-visual signature on the waterfall.

## 13. Correlator Confusion
*   **Description:** Generates Zadoff-Chu synchronization pulses with randomized phase and timing.
*   **How it works:** Synthesizes LTE/5G-style sync sequences but introduces random phase inversions and timing jitter to trigger false detection events in C++ correlators.
*   **Use Case:** Stress-testing Software Defined Timing Scanners and depacketizers against non-stationary preamble signals.

---

## Pro-Tip: Spectral Shaping
Always enable **Spectral Shaping (Rectangular)** if you are using high-power noise. It cleans up "Spectral Regrowth" (splatter) at the edges of your bandwidth, making your simulation much more realistic and preventing interference with adjacent channels.
