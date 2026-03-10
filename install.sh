#!/bin/bash

# TechniqueMaker GNU Radio OOT Module Installer
# This script builds and installs the gr-techniquemaker module.

set -e # Exit on any error

echo "--- Starting TechniqueMaker OOT Module Installation ---"

# 1. Check for dependencies
if ! command -v gnuradio-config-info &> /dev/null; then
    echo "Error: GNU Radio is not installed or not in your PATH."
    exit 1
fi

# 2. Navigate to the module directory
cd gr-techniquemaker

# 3. Create and enter the build directory
echo "--- Configuring build ---"
mkdir -p build
cd build

# 4. Run CMake
cmake ..

# 5. Compile the module
echo "--- Compiling module ---"
make -j$(nproc)

# 6. Install the module (requires sudo)
echo "--- Installing module (sudo required) ---"
sudo make install
sudo ldconfig

echo "--- Installation Complete! ---"
echo ""
echo "Important Note:"
echo "If this is your first time installing an OOT module, you may need to add"
echo "the installation path to your PYTHONPATH. Usually, this is:"
echo 'export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3/dist-packages'
echo "or"
echo 'export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3.12/site-packages'
echo ""
echo "You can verify the block is available by searching for 'Technique PDU Generator'"
echo "in GNU Radio Companion."
