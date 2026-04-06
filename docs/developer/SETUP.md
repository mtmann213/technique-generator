# Developer Setup

## Prerequisites

- Python 3.9+
- CMake + build tools (for GNU Radio OOT module)
- GNU Radio 3.10+ (for full functionality)

## Quick Start

### 1. Install Python Dependencies

```bash
# Core dependencies (waveform engine only, no GUI/GNU Radio)
pip install numpy scipy

# With dev tools
pip install -e ".[dev]"

# With GUI support
pip install -e ".[gui]"

# Full install (requires GNU Radio system packages)
pip install -e ".[gui,gnuradio,dev]"
```

### 2. Run Tests

```bash
# Waveform engine tests (no hardware, no GNU Radio needed)
pytest tests/test_waveform_engine.py -v

# Full test suite (requires compiled OOT module)
pytest tests/ -v
```

### 3. Build GNU Radio OOT Module

```bash
./install.sh
# or manually:
cd gr-techniquemaker && mkdir -p build && cd build
cmake .. && make -j$(nproc) && sudo make install && sudo ldconfig
```

### 4. Launch Applications

```bash
# Unified launcher
python TechniqueMaker.py predator     # Predator Jammer Console
python TechniqueMaker.py calibrate    # RF System Calibrator
python TechniqueMaker.py gui          # Standalone GUI
python TechniqueMaker.py batch        # AI Dataset Generator
python TechniqueMaker.py install      # Run OOT installer

# Or directly
python apps/PredatorJammer.py
python apps/SystemCalibrator.py
```

### 5. Hardware Verification (Before Connecting SDR)

```bash
# Full system check (OS, deps, hardware, Docker)
./check_hardware.sh

# Sidekiq S4/X4 focused
./check_hardware.sh --sidekiq

# USRP focused
./check_hardware.sh --usrp
```

### 6. Docker Deployment

```bash
# Build
docker build -t predator-jammer:latest .

# Export for air-gap transfer
docker save predator-jammer:latest | gzip > predator_image.tar.gz
```

## Development Workflow

1. Make changes to Python files — no rebuild needed
2. Run waveform tests: `pytest tests/test_waveform_engine.py -v`
3. For C++ changes: rebuild OOT module with `./install.sh`
4. Test with hardware: `python TechniqueMaker.py predator`

## Code Quality

```bash
# Format code
black .

# Lint
flake8 apps/ tests/
```
