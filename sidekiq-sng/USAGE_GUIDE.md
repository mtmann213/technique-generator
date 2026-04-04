# Sidekiq-Native Generator (SNG) Tactical Manual v2.5

This tool is designed for high-performance interdiction on the Epiq Sidekiq S4/X4. It supports **Spectral Stitching** to cover bandwidths exceeding 200 MSPS.

## 🚀 General Usage
```bash
./sng --tech <name> --bw <hz> --rate <hz> --chan <c1,c2> [options]
```

### 🛰️ Multi-Channel Array support
The Sidekiq X4 has 4 physical antennas. SNG v2.5 can utilize multiple antennas to "stitch" together a massive bandwidth.
*   **Example:** To cover **400 MHz** using channels 1 and 2:
```bash
./sng --tech noise --bw 400000000 --rate 200000000 --chan 1,2 --freq 2400000000 --stream
```
*   **Safety:** Only the channels you list in `--chan` will be powered. This protects unconnected ports from reflected power.

---

## 🛠️ Tactical Templates

### 1. Wideband Noise Blanket (400 MHz)
Uses two channels to create a seamless 400MHz wall of noise.
```bash
./sng --tech noise --bw 400000000 --rate 200000000 --chan 1,2 --freq 2400000000 --stream --gain 10
```

### 2. Surgical Triple-Target (Single Port)
Hits three discrete frequencies on one specific antenna.
```bash
./sng --tech noise-tones --hops "-20M 0 20M" --bw 1M --rate 50M --chan 0 --freq 915M --stream
```

---

## 🔧 Air-Gap Operations

### 0. Probe Hardware (Deep Probe)
Use this command to see the mapping between **Software Index** and **Physical Labels** (J1, J7, etc.):
```bash
# Requires SoapySDR support
./sng --probe
```
**Example Result:**
* Software Index [0]: Hardware Label: J1 (TRX)
* Software Index [1]: Hardware Label: J7 (TX1)

### 1. Compilation
We provide an automated build script for air-gapped target machines:
```bash
cd sidekiq-sng
# Clean and compile with streaming support:
make clean
./build_on_target.sh
```

### 2. TUI / GUI Tactical Consoles
Launch the intuitive interface for rapid RF reconfiguration and hardware "Blink Testing":
```bash
# TUI Console (Air-Gapped environments without Tkinter)
python3 sng_console.py

# Full Graphical Console (Requires Tkinter)
python3 sng_gui.py
```

---

## ⚠️ Safety & PA Management
1.  **PA Port Safety:** Double check your `--chan` list matches your physical connections.
2.  **Digital Headroom:** Default `--amp 0.5` provides 6dB of safety margin.
