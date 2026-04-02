# Sidekiq-Native Generator (SNG) Tactical Manual v1.13

This tool provides high-performance C++ waveform generation for the Epiq Sidekiq S4/X4. It is designed for air-gapped deployment and high-power interdiction (50W PA safety).

## 🚀 Quick Launch
```bash
./sng --tech <name> --bw <hz> --rate <hz> --len <s> [options]
```

### 🎛️ Universal Flags
*   **`--len <s>`**: Total duration (default 0.01s).
*   **`--amp <0.0-1.0>`**: Digital scaling (default 0.5). Use 1.0 for max power.
*   **`--sc16`**: Formats for native Sidekiq playback (16-bit complex int).
*   **`--out <file>`**: Filename (default: technique.bin).

### 📡 Hardware Flags (Streaming Mode)
*   **`--freq <hz>`**: Center frequency.
*   **`--gain <db>`**: TX gain (Enforced 30dB cap).
*   **`--stream`**: Direct hardware transmission.

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

## 🔧 Air-Gap Troubleshooting & Contingencies

### 1. "Shared Library Not Found" (Missing Drivers)
If you have the Sidekiq `.so` file on a USB, copy it to the local folder and run:
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
*   **Fix:** Lower the `--rate` (e.g., from 40M to 20M).
*   **Fix:** Generate to a file first (`--out`), then use a dedicated player.

### 4. Verify Data (Sanity Check)
Run this to see if the generated file has data (should not be all zeros):
```bash
# Check the first few bytes of the output
hexdump -C technique.bin | head -n 10
```

---

## ⚠️ Safety & Power Management
1.  **PA Protection:** Tool enforces a 30dB gain cap.
2.  **Order of Ops:** Always run with `--gain 0` first. Watch your SpecAn.
3.  **Heat:** Sidekiq S4/X4 can get HOT during long streams. Ensure active cooling.

## 💾 Compilation
```bash
cd sidekiq-sng
# Standard build:
make
# Build with streaming support:
make soapy
```
