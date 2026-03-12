# TechniqueMaker: Signal Synthesis & Interdiction Reference

This guide provides the mathematical and tactical foundations for the signal templates and interdiction strategies available in the TechniqueMaker suite.

---

## 🛰️ Signal Synthesis Templates
These algorithms generate the raw "payload" of an interdiction signal.

### 1. Narrowband Noise
*   **Math:** White Gaussian Noise (WGN) filtered to a specific bandwidth.
*   **Tactical Use:** Basic barrage interference across a fixed channel.

### 2. RRC Modulated Noise
*   **Math:** Noise shaped by a Root-Raised Cosine filter.
*   **Tactical Use:** Mimics the spectral footprint of digital comms (PSK/QAM) to test filter resilience.

### 3. Swept Noise / Phasors
*   **Math:** A narrowband source multiplied by a linear frequency ramp ($e^{j \pi k t^2}$).
*   **Tactical Use:** Disruption of frequency-hopping targets by covering a wide span rapidly.

### 4. LFM Chirp
*   **Math:** A pure tone with linear frequency modulation.
*   **Tactical Use:** Standard radar pulse simulation; used for range resolution stress-testing.

### 5. OFDM-Shaped Noise
*   **Math:** Frequency-domain subcarrier population with Cyclic Prefix (CP) insertion.
*   **Tactical Use:** Protocol-matched interference for 4G/5G and WiFi systems.

### 6. Correlator Confusion
*   **Math:** Randomized Zadoff-Chu sequences with phase inversions and timing jitter.
*   **Tactical Use:** Triggers false "Start of Burst" events in C++ correlators, causing depacketizer buffer overflows or misalignment.

---

## 🦅 Advanced Interdiction Strategies
These logic-based modes control **when** and **how** the templates are applied to dismantle complex digital links.

### 1. Preamble Sabotage (Invisible Mode)
*   **Mechanism:** High-precision timing gating.
*   **Logic:** Once a target is detected, the interdiction is active only for the first **10–20ms** of the burst.
*   **Impact:** Destroys the **Synchronization Sequence** (Preamble). Without a clean preamble, the receiver fails to perform Time/Frequency Acquisition and FFT window alignment. The link dies while the spectrum appears 95% clean.

### 2. Clock-Pull Drift (Tracking Loop Attack)
*   **Mechanism:** Frequency-domain ramping.
*   **Logic:** After locking onto a target, the Predator introduces a linear frequency drift (e.g., +5 kHz/s).
*   **Impact:** Attacks the receiver's **Phase-Locked Loop (PLL)**. The tracking loop "latches" onto the interdiction signal and is pulled away from the real carrier frequency, causing constellation rotation and eventual loss of synchronization.

### 3. Stability Frame Stutter (State-Machine Attack)
*   **Mechanism:** Periodic frame erasure.
*   **Logic:** Allows $X$ frames to pass through cleanly (**Clean Frames**), then pulses a burst to destroy the next $Y$ frames (**Burst Frames**).
*   **Randomization:** If enabled, the number of clean frames is randomized between 1 and $X$ for each cycle, preventing the receiver's AGC or FEC logic from adapting to a fixed pattern.
*   **Impact:** Targets the **Link Layer State Machine**. Tactical links require $N$ consecutive clean frames to declare a "Stable" link. By resetting the stability counter to zero every few frames, the link stays in a perpetual acquisition state.

### 4. Adaptive Bandwidth Sculpting
*   **Mechanism:** Real-time spectral edge detection.
*   **Logic:** Measures the **-10dB Occupied Bandwidth** of the detected signal and resizes the FIR filter of the template to match.
*   **Impact:** Concentrates 100% of the SDR's transmit power exactly within the target's channel, maximizing **Power Spectral Density** and defeating wideband filtering.

### 5. Hydra Multi-Targeting
*   **Mechanism:** Windowed FFT peak suppression.
*   **Logic:** Identifies up to 8 simultaneous signal peaks and synthesizes a composite interdiction signal.
*   **Impact:** Prevents link diversity and disrupts mesh networks by interdicting multiple frequencies or "hops" simultaneously.
