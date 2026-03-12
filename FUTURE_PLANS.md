# TechniqueMaker: Future Development Roadmap

## 🎯 High-Level Vision
To transform TechniqueMaker into an intelligent, adaptive RF Analysis suite capable of autonomous signal identification and pre-emptive interdiction against modern tactical links.

---

## 1. Tactical Portability & Deployment
- [x] **Dockerization:** Create a unified `Dockerfile` containing the entire GNU Radio/UHD environment to ensure "one-command" setup on any machine.
- [x] **USB/X11 Passthrough:** Implement automated scripts to handle SDR hardware mounting and GUI forwarding from within the container.
- [x] **Air-Gap Support:** Create an "Offline Bundle" script that exports the Docker environment into a single portable `.tar` file for deployment on non-networked field laptops.

## 2. Protocol-Aware Interdiction (Hardcore)
- [ ] **Differential Subcarrier "Erasure" (Comb Attack):** Implement a high-precision multi-tone template that places spikes exactly on every other OFDM subcarrier to destroy differential references.
- [ ] **Cyclic Prefix "Echo" (Multipath Spoof):** Add a delay-and-replay template that mimics a perfect multipath reflection slightly longer than the target's CP to force Inter-Symbol Interference (ISI).
- [ ] **Adaptive "Stutter" Tuning:** Automatically detect the target's frame duration and stability requirements to optimize the stutter cycle.

## 3. Intelligence & Machine Learning
- [ ] **Predictive Pattern Engine:** Upgrade the tracker to solve hop sequences (PRNG cracking) and jump to the next frequency *before* the target arrives.
- [ ] **On-Device CNN Classifier:** Integrate a real-time signal classifier to automatically label signals (WiFi, LFM, DF-OFDM) on the waterfall.

## 4. Advanced User Interface
- [ ] **Audio "Sonar" Feedback:** Play real-time audio pings that change pitch based on target frequency offsets for hands-free situational awareness.
- [ ] **Integrated Constellation Sink:** Add a demodulation window to the console to measure EVM and visually confirm interdiction impact.

---

## ✅ Completed Milestones
- [x] **Adaptive Bandwidth Sculpting:** Automatic -10dB occupied bandwidth measurement and template resizing.
- [x] **Preamble Sabotage:** Timing-precise interdiction targeting only the synchronization window (Invisible Mode).
- [x] **Clock-Pull Drift:** Linear frequency ramping to drag target tracking loops out of lock.
- [x] **Stability Frame Stutter:** Periodic interdiction designed to reset receiver stability counters.
- [x] **Multi-Target Hydra:** Simultaneous tracking and interdiction of up to 8 targets.
- [x] **Named Preset Manager:** Persistent scenario storage and rapid switching.
