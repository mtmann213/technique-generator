# Sidekiq-Native Generator (SNG) Tactical Manual v1.16

This tool provides high-performance C++ waveform generation for the Epiq Sidekiq S4/X4. It is designed for air-gapped deployment and high-power interdiction (50W PA safety).

## 🚀 Quick Launch
```bash
./sng --tech <name> --bw <hz> --rate <hz> --len <s> [options]
```

### 🎛️ Universal Flags
*   **`--len <s>`**: Total duration (default 0.01s).
*   **`--amp <0.0-1.0>`**: Digital scaling (default 0.5). Use 1.0 for max power.
*   **`--offset <hz>`**: Software frequency offset (shifts baseband signal).
*   **`--sc16`**: Formats for native Sidekiq playback (16-bit complex int).
*   **`--out <file>`**: Filename (default: technique.bin).

### 📡 Hardware Flags (Streaming Mode)
*   **`--freq <hz>`**: Center frequency.
*   **`--chan <0-3>`**: **X4 only**. Selects physical TX channel (default 0).
*   **`--gain <db>`**: TX gain (Enforced 30dB cap).
*   **`--stream`**: Direct hardware transmission.
*   **`--probe`**: List all available hardware channels and exit.

---

## 🛠️ Tactical Protocol Templates (Quick-Start)

| Target Link | Technique | BW Arg | Rate Arg | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Wi-Fi 2.4GHz** | `ofdm` | `--bw 16600000` | `--rate 20000000` | Mimics 802.11 sync |
| **Bluetooth (Fast)** | `fhss` | `--bw 1000000` | `--rate 10000000` | Use multiple hops |
| **DSSS / DAPS** | `confusion`| `--bw 11000000` | `--rate 25000000` | Break synchronization |
| **LTE (Narrow)** | `rrc` | `--bw 1400000` | `--rate 5000000` | Match pulse shaping |
| **Generic Denial** | `noise` | `--bw 5000000` | `--rate 10000000` | Brute force jam |

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
# Break a link with 180-deg inversions occurring at 10kHz
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
# Jump between 3 channels every 10ms (100 hops/sec)
./sng --tech fhss --hops "-1000000 0 1000000" --hop-dur 0.01 --bw 500000 --rate 10000000 --sc16 --out fast_hopper.bin
```

### 7. Correlator Confusion (`confusion`)
Injects timing/phase jitter into DSSS receivers.
```bash
# Attack a DSSS link with timing jitter and phase flips every 10ms
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

## 🔧 Air-Gap Troubleshooting & Contingencies

### 0. Check Hardware Channels (Probe)
Run the probe command to see available antennas and their names (e.g., TX1, TRX):
```bash
# Requires SoapySDR support
./sng --probe
```

### 1. "Shared Library Not Found" (Missing Drivers)
If you have the Sidekiq .so file on a USB, copy it to the local folder and run:
```bash
LD_LIBRARY_PATH=. ./sng [args]
```

### 2. "Resource Busy / Device in Use"
If another program is locking the Sidekiq hardware:
```bash
# Find and kill the process using the radio
fuser -k /dev/sidekiq* 
```

### 3. "Underflow / UUUU" (Sample Drops)
If you see 'U's in the console, your CPU is too slow for the requested sample rate.
* Fix: Lower the --rate (e.g., from 40M to 20M).
* Fix: Generate to a file first (--out), then use a dedicated player.

---

## ⚠️ Safety & Power Management
1. PA Protection: Tool enforces a 30dB gain cap.
2. Digital Scaling: Default is 0.5. Use --amp 1.0 for max power.
3. Procedure: Start at --gain 0 and increase slowly.

## 💾 Compilation
```bash
cd sidekiq-sng
# Standard build:
make
# Build with streaming support:
make soapy
```
