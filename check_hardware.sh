#!/usr/bin/env bash
# check_hardware.sh: Pre-flight verification for TechniqueMaker on air-gapped targets.
#
# Checks:
#   1. OS architecture (must be x86_64 / Ubuntu 22.04)
#   2. GNU Radio installation
#   3. SoapySDR installation + Sidekiq driver
#   4. UHD (USRP) installation
#   5. Sidekiq S4 / X4 PCIe device detection
#   6. USB SDR devices (USRP, Signal Hound)
#   7. Python dependencies (numpy, scipy, PyQt5)
#   8. Docker availability + image loaded
#
# Usage: ./check_hardware.sh
#        ./check_hardware.sh --sidekiq    (Sidekiq X4/S4 focused check)
#        ./check_hardware.sh --usrp       (USRP focused check)

set -e
cd "$(dirname "$0")"

PASS=0
FAIL=0
WARN=0
SIDEX=""
ALL=true

for arg in "$@"; do
    case "$arg" in
        --sidekiq) SIDEX="sidekiq"; ALL=false ;;
        --usrp) SIDEX="usrp"; ALL=false ;;
    esac
done

green()  { echo -e "\033[32m[PASS]\033[0m $1"; ((PASS++)); }
red()    { echo -e "\033[31m[FAIL]\033[0m $1"; ((FAIL++)); }
yellow() { echo -e "\033[33m[WARN]\033[0m $1"; ((WARN++)); }
info()   { echo -e "\033[36m[INFO]\033[0m $1"; }

echo "============================================"
echo "  TechniqueMaker Hardware Pre-Flight Check"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================"

# --- 1. Architecture Check ---
ARCH=$(uname -m)
if [ "$ARCH" = "x86_64" ]; then
    green "Architecture: x86_64 (correct for this bundle)"
else
    red "Architecture: $ARCH (expected x86_64). Pre-built binaries will NOT work."
    info "You must build from source: run ./install.sh and cd sidekiq-sng && ./build_on_target.sh"
fi

# --- 2. Ubuntu Version ---
if [ -f /etc/os-release ]; then
    UBUNTU_VER=$(. /etc/os-release && echo "$VERSION_ID")
    if [[ "$UBUNTU_VER" == "22.04" ]]; then
        green "Ubuntu version: $UBUNTU_VER"
    else
        yellow "Ubuntu version: $UBUNTU_VER (bundle was built on 22.04)"
    fi
fi

# --- 3. GNU Radio ---
if [ "$ALL" = true ] || [ "$SIDEX" = "" ]; then
    if command -v gnuradio-config-info &> /dev/null; then
        GR_VER=$(gnuradio-config-info --version 2>/dev/null || echo "unknown")
        green "GNU Radio: installed ($GR_VER)"
    else
        red "GNU Radio: NOT installed (required for Predator Jammer)"
        info "Install: sudo apt install gnuradio"
    fi
fi

# --- 4. SoapySDR ---
if [ "$ALL" = true ] || [ "$SIDEX" = "sidekiq" ]; then
    if command -v SoapySDRUtil &> /dev/null; then
        green "SoapySDR: installed"
        # Check for Sidekiq driver
        SIDEKIQ_FOUND=false
        if SoapySDRUtil --probe="driver=sidekiq" 2>&1 | grep -q "Found"; then
            SIDEKIQ_FOUND=true
            green "Sidekiq SoapySDR driver: DETECTED"
        elif SoapySDRUtil --find 2>&1 | grep -qi "sidekiq"; then
            SIDEKIQ_FOUND=true
            green "Sidekiq SoapySDR driver: DETECTED"
        else
            yellow "Sidekiq SoapySDR driver: not detected"
            info "Install the Sidekiq PCIe driver + SoapySDR module from Epiq on the target machine."
            info "Then re-run this check."
        fi
    else
        red "SoapySDR: NOT installed (required for Sidekiq S4/X4)"
        info "Install: sudo apt install soapysdr-tools libsoapysdr-dev"
    fi

    # --- 5. Sidekiq PCIe Device ---
    if command -v lspci &> /dev/null; then
        PCI_COUNT=$(lspci | grep -i -c -e "epiq" -e "sidekiq" || true)
        if [ "$PCI_COUNT" -gt 0 ]; then
            green "Sidekiq PCIe device detected ($PCI_COUNT device(s))"
            lspci | grep -i -e "epiq" -e "sidekiq" | while read line; do
                info "  $line"
            done
        else
            if [ "$FAIL" -eq 0 ] && [ "$WARN" -eq 0 ] || [ "$SIDEKIQ_FOUND" = true ]; then
                yellow "No Sidekiq PCIe device found via lspci"
                info "The device may still be accessible via SoapySDR despite not showing in lspci."
                info "Try: SoapySDRUtil --probe=\"driver=sidekiq\""
            fi
        fi
    else
        yellow "lspci not available (install pciutils for PCIe detection)"
    fi

    # --- Sidekiq S4 /dev node ---
    if [ -c /dev/sidekiq0 ]; then
        green "Sidekiq S4 /dev/sidekiq0: present"
    else
        yellow "/dev/sidekiq0: not found (this is normal for Sidekiq X4)"
    fi
fi

# --- 6. UHD (USRP) ---
if [ "$ALL" = true ] || [ "$SIDEX" = "usrp" ]; then
    if command -v uhd_find_devices &> /dev/null; then
        green "UHD tools: installed"
    else
        yellow "UHD tools: not installed (optional, needed for USRP)"
        info "Install: sudo apt install uhd-host"
    fi

    if command -v uhd_find_devices &> /dev/null; then
        UHD_COUNT=$(uhd_find_devices 2>/dev/null | grep -c "B-Series\|X-Series\|USRP" || true)
        if [ "$UHD_COUNT" -gt 0 ]; then
            green "USRP device detected ($UHD_COUNT device(s))"
        else
            yellow "No USRP devices found (check USB 3.0 connection)"
            info "Tip: USB 3.0 (blue port) required for high sample rates"
        fi
    fi
fi

# --- 7. Signal Hound ---
if [ "$ALL" = true ]; then
    if lsusb 2>/dev/null | grep -qi -e "signal.hound" -e "1d52"; then
        green "Signal Hound USB device: detected"
    else
        yellow "No Signal Hound USB device detected (optional)"
    fi

    # Check for vendor library
    if [ -f /usr/lib/libvsg60.so ] || [ -f /usr/local/lib/libvsg60.so ] || \
       [ -f /usr/local/lib/predator_drivers/libvsg60.so ] 2>/dev/null; then
        green "Signal Hound SDK (libvsg60): found"
    else
        yellow "Signal Hound SDK (libvsg60): not found (needed for VSG60A)"
    fi
fi

# --- 8. Python Dependencies ---
if python3 -c "import numpy" 2>/dev/null; then
    green "Python: numpy"
else
    red "Python: numpy NOT installed"
    info "Install: pip3 install numpy"
fi

if python3 -c "import scipy" 2>/dev/null; then
    green "Python: scipy"
else
    red "Python: scipy NOT installed"
    info "Install: pip3 install scipy"
fi

if python3 -c "import PyQt5" 2>/dev/null; then
    green "Python: PyQt5"
else
    red "Python: PyQt5 NOT installed (required for GUI)"
    info "Install: sudo apt install python3-pyqt5"
fi

# --- 9. Docker ---
if command -v docker &> /dev/null; then
    green "Docker: installed"
    # Check for predator image
    if docker image inspect "predator-jammer:latest" &> /dev/null; then
        green "Docker image (predator-jammer:latest): loaded"
    else
        yellow "Docker image (predator-jammer:latest): not loaded"
        if [ -f "predator_image.tar.gz" ]; then
            SIZE=$(du -h predator_image.tar.gz | cut -f1)
            info "predator_image.tar.gz found ($SIZE). Load with: gunzip -c predator_image.tar.gz | docker load"
        else
            info "No predator_image.tar.gz found in this directory."
        fi
    fi
else
    yellow "Docker: not installed (optional, needed for container mode)"
    info "You can still run the Python apps directly without Docker."
fi

# --- 10. GNU Radio OOT Module ---
if python3 -c "from gnuradio import techniquemaker" 2>/dev/null; then
    green "GNU Radio OOT module (techniquemaker): installed"
elif python3 -c "from techniquemaker import BaseWaveforms" 2>/dev/null; then
    green "techniquemaker BaseWaveforms: importable from source"
    yellow "GNU Radio OOT module: not installed as system package"
    info "The Python bindings work from source. Run ./install.sh for full integration."
else
    red "techniquemaker Python module: not found"
    info "Build the OOT module: cd gr-techniquemaker && mkdir build && cd build && cmake .. && make -j\$(nproc) && sudo make install && sudo ldconfig"
fi

# --- Summary ---
echo ""
echo "============================================"
echo "  Results: $PASS passed, $FAIL failed, $WARN warnings"
echo "============================================"
if [ "$FAIL" -eq 0 ]; then
    echo "  System is ready to run TechniqueMaker."
else
    echo "  Fix the FAIL items above before proceeding."
fi
echo ""
