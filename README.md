# TechniqueMaker

**TechniqueMaker** is a modular signal and interference generator project designed for Software Defined Radio (SDR) and DSP testing. It includes a standalone GUI and a GNU Radio Out-Of-Tree (OOT) module for real-time signal processing.

## 🚀 Quick Start (GNU Radio Block)

If you've downloaded the repository and want to use the **Technique PDU Generator** in GNU Radio Companion (GRC), follow these steps:

### 1. Run the Installation Script
```bash
chmod +x install.sh
./install.sh
```
This script will build, compile, and install the `gr-techniquemaker` OOT module to your system (`/usr/local`).

### 2. Verify Installation
In GRC, search for the **Technique PDU Generator** block. If you cannot see it, ensure your `PYTHONPATH` includes the installation folder. Common paths:
```bash
# For most systems:
export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3/dist-packages
# For Ubuntu 24.04/etc (check your python version):
export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3.12/site-packages
```

### 3. Run the Test Flowgraph
Open and run the included test:
```bash
gnuradio-companion gr-techniquemaker/examples/test_techniquepdu.grc
```

---

## 🖥️ Using the GUI Generator

For a simple standalone tool to generate and save signal files (Raw Bin, SigMF, etc.), run:
```bash
python3 BaseGui.py
```
This tool uses `BaseWaveforms.py` to generate waveforms with the exact same math as the GNU Radio block.

---

## 🏗️ Project Structure
- `BaseGui.py`: Standalone Tkinter GUI for generating signal files.
- `BaseWaveforms.py`: The core DSP logic containing the signal techniques.
- `gr-techniquemaker/`: The GNU Radio Out-Of-Tree module.
- `FUTURE_PLANS.md`: Roadmap for upcoming features and optimizations.

## 🛠️ Requirements
- Python 3.10+
- GNU Radio 3.10+
- NumPy, SciPy
- Tkinter (for GUI)
