# Sidekiq-Native Generator (SNG) Tactical Manual v1.12

This tool provides high-performance C++ waveform generation for the Epiq Sidekiq S4/X4. It is designed for air-gapped deployment and high-power interdiction (50W PA safety).

## 🚀 General Usage
```bash
./sng --tech <name> --bw <hz> --rate <hz> --len <s> [options]
```

### 🎛️ Universal Flags (Apply to ALL techniques)
*   **`--len <s>`**: Total duration of the generated signal (default 0.01s).
*   **`--amp <0.0-1.0>`**: Digital scaling (default 0.5). Lower this if you see DAC clipping.
*   **`--sc16`**: Formats the output for native Sidekiq S4/X4 playback.
*   **`--out <file>`**: Name of the output binary file.

### 📡 Hardware Flags (Only for `--stream` mode)
*   **`--freq <hz>`**: Sets the Sidekiq center frequency.
*   **`--gain <db>`**: Sets TX gain (Capped at 30dB for 50W PA safety).
*   **`--stream`**: Transmit directly to hardware instead of saving a file.

---

## 🛠️ Available Techniques & Templates

### 1. Narrowband Noise (`noise`)
Standard broadband interference.
```bash
./sng --tech noise --bw 1000000 --rate 2000000 --len 0.1 --sc16 --out surgical_noise.bin
```

### 2. Phase-Shifted Noise (`phase-noise`)
Breaks correlation-based receivers (DSSS/DAPS).
```bash
./sng --tech phase-noise --bw 5000000 --rate 20000000 --len 0.1 --shift 180 --shift-rate 10000 --sc16 --out daps_crusher.bin
```

### 3. Differential Comb (`comb`)
Concentrates power into high-energy spectral spikes.
```bash
./sng --tech comb --spikes 10 --spacing 100000 --rate 5000000 --len 0.1 --sc16 --out channel_trap.bin
```

### 4. LFM Chirp (`chirp`)
Linear frequency sweep to break protocol synchronization.
```bash
./sng --tech chirp --bw 10000000 --rate 25000000 --len 0.01 --sc16 --out protocol_sweep.bin
```

### 5. OFDM-Shaped Noise (`ofdm`)
Stealthy noise that mimics Wi-Fi/LTE spectral signatures.
```bash
./sng --tech ofdm --bw 16600000 --rate 20000000 --len 0.04 --sc16 --out wifi_mimic.bin
```

### 6. FHSS Noise (`fhss`)
Fast frequency hopper barrage.
```bash
./sng --tech fhss --hops "-1M 0 1M" --hop-dur 0.01 --bw 500k --rate 10M --len 0.1 --sc16 --out fast_hopper.bin
```

### 7. Correlator Confusion (`confusion`)
Injects timing/phase jitter into DSSS receivers.
```bash
./sng --tech confusion --bw 11000000 --rate 25000000 --len 0.1 --pulse-gap 10 --sc16 --out daps_unlocker.bin
```

### 8. Noise Tones (`noise-tones`)
Surgical noise clouds at specific discrete frequencies.
```bash
./sng --tech noise-tones --hops "-500k 500k" --bw 25000 --rate 5M --len 0.1 --sc16 --out tone_clouds.bin
```

### 9. Chunked Noise (`chunked-noise`)
Spectral shredder with dynamic re-shuffling.
```bash
./sng --tech chunked-noise --bw 20M --spikes 10 --sweep-rate 500 --rate 40M --len 0.1 --sc16 --out shredder.bin
```

### 10. RRC Modulated Noise (`rrc`)
Protocol-matched noise for single-carrier digital links.
```bash
./sng --tech rrc --bw 1M --rolloff 0.35 --rate 5M --len 0.1 --sc16 --out rrc_match.bin
```

### 11. FM Cosine (`fm-cosine`)
Frequency-modulated "wobbler" interference.
```bash
./sng --tech fm-cosine --bw 100000 --mod-rate 1000 --rate 2000000 --len 0.1 --sc16 --out fm_wobble.bin
```

---

## ⚠️ Safety & Power Management
1.  **Gain Limit:** enforced 30dB cap.
2.  **Digital Scaling:** Default is 0.5.
3.  **Procedure:** Start at `--gain 0` and increase slowly.
