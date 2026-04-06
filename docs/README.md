# TechniqueMaker Documentation

> Advanced Reactive Interdiction Suite — protocol-aware RF testing and electronic warfare research.

## Quick Links

| Document | Purpose |
|---|---|
| [../README.md](../README.md) | Project overview, features, deployment |
| [TECHNIQUES.md](TECHNIQUES.md) | RF interdiction techniques reference |
| [FUTURE_PLANS.md](FUTURE_PLANS.md) | Roadmap and future operations |

## By Topic

### Developer
- [Developer Setup](developer/SETUP.md) — Getting the project running locally
- [Testing Guide](developer/TESTING.md) — Running and writing tests
- [Architecture](developer/ARCHITECTURE.md) — System design and component overview

### Hardware
- [Docker & Deployment](DOCKER_INSTRUCTIONS.md) -- Container build and air-gap transfer
- [Sidekiq SNG Manual](../sidekiq-sng/USAGE_GUIDE.md) -- Sidekiq-Native Generator tactical manual
- [Sidekiq X4 Setup](../README.md#-sidekiq-x4-setup-air-gapped) -- X4 driver, port mapping, and streaming guide
- [Hardware Pre-Flight Check](../check_hardware.sh) -- Run `./check_hardware.sh` on the target to verify all dependencies

### AI Integration
- [LLM Handover](../LLM_HANDOVER_DOCUMENT.md) — Air-gapped local AI setup and context passing
- [AI Assistant Guide](ai/LLM_GUIDE.md) — Working with the local coding assistant

## Project Structure

```
TechniqueMaker/
|-- TechniqueMaker.py          # Unified launcher (entry point)
|-- apps/                      # Python applications
|   |-- PredatorJammer.py      # Main tactical console (GUI)
|   |-- BaseGui.py             # Standalone GUI
|   |-- SystemCalibrator.py    # RF power/frequency calibration
|   |-- BatchGenerator.py      # AI dataset generator
|   `-- core_utils.py          # Config management, utilities
|-- config/                    # System configs, calibration data, presets
|-- gr-techniquemaker/         # GNU Radio OOT module (C++ DSP core + Python bindings)
|-- predator-cpp/              # Native C++ Qt console (alternative UI)
|-- sidekiq-sng/               # Sidekiq Native Generator (C++, standalone)
|-- sidekiq_ai_bundle/         # Local llama.cpp (air-gapped LLM, rebuild on target)
|-- tests/                     # Test suite
`-- docs/                      # This folder
```

## Key Concepts

- **TechniqueMaker** = the unified Python suite (GUI + DSP + calibration)
- **Predator Console** = the primary PyQt5 tactical console
- **SNG (Sidekiq-Native Generator)** = C++ engine for Epiq Sidekiq S4/X4 hardware
- **OOT Module** = GNU Radio Out-Of-Tree C++ DSP blocks
- **Dual-Engine DSP**: Python/NumPy "Golden Set" for validation, C++ for performance
