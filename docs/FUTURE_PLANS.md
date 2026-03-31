# Roadmap & Future Operations

## 1. Sidekiq S4 4x4 MIMO
Expand the `init_blocks` logic to drive all four TX channels of the S4 simultaneously. This will allow for 4-sector spatial jamming or massive 160MHz+ spectral stitching.

## 2. Automated PRNG Cracker
Integration of the existing C++ PRNG cracker to predict the hopping sequence of the latest DAPS waveforms in real-time.

## 3. SigMF Data Replay
The ability to "Loop-Back" recorded captures (`.sigmf-meta`) through the interdiction engine for lab-based target analysis.

## 4. Remote Headless Node
A lightweight C++ daemon mode for the S4 machine that can be controlled via the Python GUI over a secure TUN/TAP tunnel.
