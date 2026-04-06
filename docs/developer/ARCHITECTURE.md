# Architecture

## System Overview

TechniqueMaker is a **dual-engine DSP architecture** for real-time RF interdiction:

```
┌─────────────────────────────────────────────────────────────────┐
│                        TechniqueMaker Suite                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────┐    ┌──────────────────────────────┐    │
│  │  Predator Console   │    │  Sidekiq SNG (C++)          │    │
│  │  (PyQt5 + GNU Radio)│    │  (Standalone, high-bandwidth)│    │
│  └─────────┬───────────┘    └──────────────┬───────────────┘    │
│            │                               │                     │
│  ┌─────────▼───────────┐    ┌──────────────▼───────────────┐    │
│  │  Interdictor Blocks  │    │  WaveformEngine (C++)        │    │
│  │  (C++ OOT / Python)  │    │  Direct SoapySDR DMA         │    │
│  └─────────┬───────────┘    └──────────────┬───────────────┘    │
│            │                               │                     │
│  ┌─────────▼───────────┐                   │                     │
│  │  BaseWaveforms.py   │◄── Parity Test ───┘                    │
│  │  (NumPy Golden Set) │                                        │
│  └─────────┬───────────┘                                        │
│            │                                                     │
│  ┌─────────▼───────────────────────────────────────────────┐    │
│  │                    Hardware Layer                        │    │
│  │  USRP (UHD) │ Signal Hound (Soapy) │ Sidekiq S4/X4      │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. BaseWaveforms.py (Python/NumPy — "Golden Set")
- **Purpose**: Reference implementation of all 15+ waveform techniques
- **Location**: `gr-techniquemaker/python/techniquemaker/BaseWaveforms.py`
- **Why**: Mathematical validation, rapid prototyping, CI testing
- **Techniques**: Noise, Chirps, OFDM, FHSS, Combs, Tones, WiFi preambles, Songs...
- **No external deps**: Only numpy + scipy

### 2. Interdictor Blocks (C++ OOT Module)
- **Purpose**: Real-time reactive DSP integrated into GNU Radio flowgraph
- **Location**: `gr-techniquemaker/lib/interdictor_cpp_impl.cc`
- **Features**: FFT detection, multi-target synthesis, sticky denial, PRNG tracking
- **Integration**: Python bindings via pybind11, used by PredatorJammer.py

### 3. Sidekiq SNG (C++ Standalone Engine)
- **Purpose**: Direct DMA to Sidekiq hardware, bypass GNU Radio for max throughput
- **Location**: `sidekiq-sng/`
- **Features**: 200+ MSPS via spectral stitching, strict DMA alignment, multi-channel
- **Build**: `make soapy` on target (air-gapped, no -dev packages needed)

### 4. Predator Console (PyQt5 Application)
- **Purpose**: Primary operator interface — real-time waterfall, controls, monitoring
- **Location**: `apps/PredatorJammer.py`
- **Features**: Hardware discovery, dual-SDR, presets, calibration, simulation mode
- **Architecture**: GNU Radio gr.top_block + Qt.QWidget (dual inheritance)

### 5. System Calibrator
- **Purpose**: Automated RF power and frequency calibration
- **Location**: `apps/SystemCalibrator.py`
- **Output**: `config/calibration_matrix.json` (Gain → dBm mapping)

## Data Flow

```
RF IN ──► USRP RX ──► FFT Detection ──► Target Identification
                                              │
                                              ▼
                                    Waveform Synthesis
                                      (match BW, freq)
                                              │
                                              ▼
                                    USRP TX ──► RF OUT
                                              │
                                    Waterfall Display
                                    Session Recording
                                    Detection Logging
```

## Configuration

- `config/system_config.json` — Hardware serials, defaults, logging
- `config/predator_presets.json` — Tactical profiles (saved from GUI)
- `config/calibration_matrix.json` — RF calibration data
- `config/calibrator_presets.json` — Calibration session presets

## Test Strategy

| Layer | Tests | Requirements |
|---|---|---|
| Waveform Engine | `test_waveform_engine.py` (40+ tests) | numpy + scipy only |
| Parity | `test_waveform_parity.py` | Compiled OOT module |
| DSP | `test_advanced_dsp.py` | GNU Radio + matplotlib |
| Hardware | Manual / virtual mode | Physical SDR or sim source |

## Hardware Layer

| Device | Interface | Driver | Detection |
|---|---|---|---|
| Ettus USRP (B205, B210, N-Series) | USB 3.0 | UHD (`uhd_find_devices`) | `lsusb` |
| Signal Hound (VSG60A) | USB 2.0 | libvsg60 via SoapySDR | `lsusb` |
| Sidekiq S4 | PCIe /dev node | SoapySidekiq, `/dev/sidekiq0` | `/dev/sidekiq0` |
| Sidekiq X4 | PCIe x4 | SoapySidekiq | `lspci` + `SoapySDRUtil --find` |

### Sidekiq X4 Architecture Notes
- **PCIe only** -- no `/dev/node` like S4, uses kernel-space DMA
- **4 TX/4 RX channels** -- each mapped to physical SMA ports (J1, J7, J8, J9)
- **Spectral Stitching** -- SNG v2.5 splits bandwidth across channels, applies frequency offsets, and pads to strict MTU boundaries
- **Antenna routing** -- `setAntenna()` with last item from `listAntennas()` required for secondary ports
- **PA enable** -- `TX_EN=true` write required on each channel before streaming
- **Firmware loading** -- automatic on driver module load, no manual step
- **Driver requirement** -- Epiq PCIe driver + SoapySidekiq plugin must be installed on target (not bundled, from Epiq SDK)

### Air-Gap Deployment Architecture
