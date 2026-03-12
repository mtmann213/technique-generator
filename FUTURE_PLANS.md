# TechniqueMaker: Future Development Roadmap

## 🎯 High-Level Vision
To transform TechniqueMaker into an intelligent, adaptive RF Analysis suite capable of autonomous signal identification and pre-emptive interdiction against modern tactical links.

---

## 1. Protocol-Aware Interdiction (Hardcore)
- [ ] **Differential Subcarrier "Erasure" (Comb Attack):** Implement a high-precision multi-tone template that places spikes exactly on every other OFDM subcarrier to destroy differential references.
- [ ] **Cyclic Prefix "Echo" (Multipath Spoof):** Add a delay-and-replay template that mimics a perfect multipath reflection slightly longer than the target's CP to force Inter-Symbol Interference (ISI).
- [ ] **Adaptive "Stutter" Tuning:** Automatically detect the target's frame duration and stability requirements to optimize the stutter cycle for maximum disruption with minimum power.

## 2. Intelligence & Machine Learning
- [ ] **Predictive Pattern Engine:** Upgrade the tracker to solve hop sequences (PRNG cracking) and jump to the next frequency *before* the target arrives.
- [ ] **On-Device CNN Classifier:** Integrate a real-time signal classifier to automatically label signals (WiFi, LFM, DF-OFDM) on the waterfall.
- [ ] **Signal Fingerprinting:** Identify specific radio hardware based on subtle spectral artifacts (IQ imbalance, phase noise).

## 3. Advanced User Interface
- [ ] **Audio "Sonar" Feedback:** Play real-time audio pings that change pitch based on target frequency offsets for hands-free situational awareness.
- [ ] **Headless Web Command Center:** Replace the PyQt5 GUI with a WebSocket-based HTML5 dashboard for remote deployment on embedded Linux devices.
- [ ] **Integrated Constellation Sink:** Add a demodulation window to the console to measure EVM and visually confirm interdiction impact on constellation points.

---

## ✅ Completed Milestones
- [x] **Adaptive Bandwidth Sculpting:** Automatic -10dB occupied bandwidth measurement and template resizing.
- [x] **Preamble Sabotage:** Timing-precise interdiction targeting only the synchronization window (Invisible Mode).
- [x] **Clock-Pull Drift:** Linear frequency ramping to drag target tracking loops out of lock.
- [x] **Stability Frame Stutter:** Periodic interdiction designed to reset receiver stability counters.
- [x] **Multi-Target Hydra:** Simultaneous tracking and interdiction of up to 8 targets.
- [x] **Correlator Confusion:** Zadoff-Chu based synchronization-stressing synthesis.
- [x] **Named Preset Manager:** Persistent scenario storage and rapid switching.
