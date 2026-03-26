cmake_minimum_required(VERSION 3.10)
project(PredatorNative LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

# Find Dependencies
find_package(Qt5 REQUIRED COMPONENTS Widgets Core Gui)
find_package(Gnuradio REQUIRED COMPONENTS runtime uhd qtgui fft filter blocks analog)
find_package(UHD REQUIRED)

# Include directories
include_directories(
    ${Qt5Widgets_INCLUDE_DIRS}
    ${Qt5Core_INCLUDE_DIRS}
    ${Qt5Gui_INCLUDE_DIRS}
    ${GNURADIO_RUNTIME_INCLUDE_DIRS}
    ${GNURADIO_UHD_INCLUDE_DIRS}
    ${GNURADIO_QTGUI_INCLUDE_DIRS}
    ${UHD_INCLUDE_DIRS}
    ${PROJECT_SOURCE_DIR}/../gr-techniquemaker/include
    ${PROJECT_SOURCE_DIR}/src
)

# Source Files
set(SOURCES
    src/main.cpp
    src/MainWindow.cpp
    src/InterdictionController.cpp
    src/WaveformEngine.cpp
    src/TelemetryModel.cpp
    # Local OOT Implementation
    ${PROJECT_SOURCE_DIR}/../gr-techniquemaker/lib/interdictor_cpp_impl.cc
)

add_executable(PredatorNative ${SOURCES})

target_link_libraries(PredatorNative
    Qt5::Widgets
    Qt5::Core
    Qt5::Gui
    gnuradio::gnuradio-runtime
    gnuradio::gnuradio-uhd
    gnuradio::gnuradio-qtgui
    gnuradio::gnuradio-fft
    gnuradio::gnuradio-filter
    gnuradio::gnuradio-blocks
    gnuradio::gnuradio-analog
    ${UHD_LIBRARIES}
)

# Enable optimization for DSP
target_compile_options(PredatorNative PRIVATE -O3 -march=native)
