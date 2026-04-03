# Sidekiq-Native Generator (SNG) Tactical Manual v2.1

This tool is designed for high-performance interdiction on the Epiq Sidekiq S4/X4. It supports **Spectral Stitching** to cover bandwidths exceeding 200 MSPS.

## 🚀 General Usage
```bash
./sng --tech <name> --bw <hz> --rate <hz> --chan <c1,c2> [options]
```

### 🛰️ Multi-Channel Array support
The Sidekiq X4 has 4 physical antennas. SNG v2.1 can utilize multiple antennas to "stitch" together a massive bandwidth.
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

### 1. Local Drivers
Keep your `.so` files in the tool folder and run:
```bash
LD_LIBRARY_PATH=. ./sng [args]
```

---

## ⚠️ Safety & PA Management
1.  **PA Port Safety:** Double check your `--chan` list matches your physical connections.
2.  **Gain Limit:** enforced 30dB cap.
3.  **Digital Headroom:** Default `--amp 0.5` provides 6dB of safety margin.

## 💾 Compilation
```bash
cd sidekiq-sng
# Standard build:
make
# Build with streaming support:
make soapy
```
