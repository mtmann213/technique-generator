# Sidekiq-Native Generator (SNG) Tactical Manual

This tool provides high-performance C++ waveform generation for the Epiq Sidekiq S4. It is designed for air-gapped deployment and high-power interdiction (50W PA safety).

## 🚀 General Usage
```bash
./sng --tech <name> --bw <hz> --rate <hz> [options]
```

### 🗄️ File Output Options
* By default, SNG saves waveforms as **32-bit Complex Floats (CF32)** in `technique.bin`.
* If your playback tool requires **16-bit Complex Integers (SC16)**, add the `--sc16` flag.

---

## 🛠️ Available Techniques & Templates

### 1. Narrowband Noise (`noise`)
Standard broadband interference. Best for basic denial of service.
*   **Key Args:** `--bw`, `--rate`
*   **Example Template:**
```bash
./sng --tech noise --bw 1000000 --rate 2000000 --len 0.5 --freq 2412000000 --gain 10 --stream
```

### 2. Phase-Shifted Noise (`phase-noise`)
Noise with periodic phase rotations. Designed to break correlation-based receivers (DSSS/DAPS).
*   **Key Args:** `--bw`, `--rate`, `--shift`, `--shift-rate`
*   **Example Template:**
```bash
# Break a link with 180-deg inversions occurring at 10kHz
./sng --tech phase-noise --bw 5000000 --rate 20000000 --shift 180 --shift-rate 10000 --amp 0.6 --sc16 --out daps_crusher.bin
```

### 3. Differential Comb (`comb`)
Generates multiple high-power spikes across the bandwidth. Efficient for multi-channel disruption.
*   **Key Args:** `--bw` (Total span), `--rate`
*   **Example Template:**
```bash
./sng --tech comb --bw 2000000 --rate 5000000 --len 1.0 --freq 915000000 --gain 15 --stream
```

### 4. LFM Chirp (`chirp`)
A linear frequency modulated sweep. Excellent for sweeping across a protocol's control channel.
*   **Key Args:** `--bw` (Sweep range), `--rate`
*   **Example Template:**
```bash
./sng --tech chirp --bw 10000000 --rate 20000000 --freq 2437000000 --gain 10 --stream
```

### 5. OFDM-Shaped Noise (`ofdm`)
Generates noise that mimics the spectral shape of an 802.11 or LTE signal.
*   **Key Args:** `--rate`
*   **Example Template:**
```bash
./sng --tech ofdm --bw 20000000 --rate 40000000 --freq 5180000000 --gain 0 --stream
```

---

## ⚠️ Safety & Power Management
When using with a **50W Power Amplifier**:
1.  **Gain Limit:** The tool enforces a hard cap of **30 dB** on the `--gain` flag.
2.  **Digital Scaling:** All waveforms are pre-scaled to 0.5 amplitude to prevent DAC clipping.
3.  **Startup:** Always start with `--gain 0` and increase in small increments (e.g., 5dB) while monitoring your SpecAn.

## 💾 Offline Compilation
On the target machine:
```bash
cd sidekiq-sng
# For basic file generation:
make
# For direct S4 streaming (if SoapySDR is present):
make soapy
```
