# Sidekiq-Native Generator (SNG) Tactical Manual v1.7

This tool provides high-performance C++ waveform generation for the Epiq Sidekiq S4/X4. It is designed for air-gapped deployment and high-power interdiction (50W PA safety).

## 🚀 General Usage
```bash
./sng --tech <name> --bw <hz> --rate <hz> [options]
```

### 🗄️ File Output Options
* By default, SNG saves waveforms as **32-bit Complex Floats (CF32)** in `technique.bin`.
* If your playback tool requires **16-bit Complex Integers (SC16)**, add the `--sc16` flag.

### 🎛️ Hardware & Tuning Flags
*   **`--freq <hz>`**: **Only used with `--stream`**. Sets the Sidekiq center frequency.
*   **`--gain <db>`**: **Only used with `--stream`**. Sets TX gain (Capped at 30dB for 50W PA safety).
*   **`--amp <0.0-1.0>`**: Sets digital scaling (default 0.5 for safety).

---

## 🛠️ Available Techniques & Templates

### 1. Narrowband Noise (`noise`)
Standard broadband interference. Best for basic denial of service.
```bash
./sng --tech noise --bw 1000000 --rate 2000000 --len 0.1 --sc16 --out surgical_noise.bin
```

### 2. Phase-Shifted Noise (`phase-noise`)
Noise with periodic phase rotations. Designed to break correlation-based receivers (DSSS/DAPS).
```bash
# Break a link with 180-deg inversions occurring at 10kHz
./sng --tech phase-noise --bw 5000000 --rate 20000000 --shift 180 --shift-rate 10000 --sc16 --out daps_crusher.bin
```

### 3. Differential Comb (`comb`)
Generates multiple high-power spikes across the bandwidth. Efficient for multi-channel disruption.
```bash
./sng --tech comb --spikes 10 --spacing 100000 --rate 5000000 --len 0.1 --sc16 --out channel_trap.bin
```

### 4. LFM Chirp (`chirp`)
A linear frequency modulated sweep. Excellent for sweeping across a protocol's control channel.
```bash
./sng --tech chirp --bw 10000000 --rate 25000000 --len 0.01 --sc16 --out protocol_sweep.bin
```

### 5. OFDM-Shaped Noise (`ofdm`)
Generates noise that mimics the spectral shape of an 802.11 or LTE signal.
```bash
# Match a 20MHz Wi-Fi signal structure (16.6MHz occupied BW)
./sng --tech ofdm --bw 16600000 --rate 20000000 --len 0.04 --sc16 --out wifi_mimic.bin
```

### 6. FHSS Noise (`fhss`)
Simulates a fast frequency hopper. Best for barraging multiple channels or shadowing targets.
```bash
# Jump between 3 channels every 10ms (100 hops/sec)
./sng --tech fhss --hops "-1000000 0 1000000" --hop-dur 0.01 --bw 500000 --rate 10000000 --sc16 --out fast_hopper.bin
```

### 7. Correlator Confusion (`confusion`)
Defeats DSSS/CDMA by injecting phase-flipped "phantom" spreading codes.
```bash
# Attack a DSSS link with timing jitter and phase flips every 10ms
./sng --tech confusion --bw 11000000 --rate 25000000 --pulse-gap 10 --sc16 --out daps_unlocker.bin
```

### 8. Noise Tones (`noise-tones`)
Surgical interdiction of multiple specific frequencies using broadened noise clouds.
```bash
# Hit 3 specific control channels, each with a 25kHz wide noise cloud
./sng --tech noise-tones --hops "-500000 0 500000" --bw 25000 --rate 5000000 --sc16 --out multi_tone_cloud.bin
```

---

## ⚠️ Safety & Power Management
When using with a **50W Power Amplifier**:
1.  **Gain Limit:** The tool enforces a hard cap of **30 dB** on the `--gain` flag.
2.  **Digital Scaling:** All waveforms are pre-scaled to 0.5 amplitude by default. Use `--amp 1.0` only if the signal is too weak.
3.  **Startup:** Always start with `--gain 0` and increase in small increments while monitoring your SpecAn.

## 💾 Offline Compilation
On the target machine:
```bash
cd sidekiq-sng
make
```
