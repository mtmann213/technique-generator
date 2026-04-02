#include <iostream>
#include <string>
#include <vector>
#include <complex>
#include <fstream>
#include <chrono>
#include <thread>
#include "WaveformEngine.hpp"

// Optional Hardware Support
#ifdef USE_SOAPY
#include <SoapySDR/Device.hpp>
#include <SoapySDR/Formats.hpp>
#include <SoapySDR/Types.hpp>
#endif

void print_help() {
    std::cout << "Sidekiq-Native Generator (SNG) v1.1" << std::endl;
    std::cout << "Usage: ./sng --tech <name> --bw <hz> --rate <hz> [options]" << std::endl;
    std::cout << "\nAvailable Techniques:" << std::endl;
    std::cout << "  noise, phase-noise, comb, chirp, ofdm" << std::endl;
    std::cout << "\nOptions:" << std::endl;
    std::cout << "  --stream           Stream directly to hardware (requires SoapySDR)" << std::endl;
    std::cout << "  --gain <db>        Hardware TX Gain (Safety Limit: 0-30dB, default 0)" << std::endl;
    std::cout << "  --freq <hz>        Center Frequency for streaming" << std::endl;
    std::cout << "  --len <s>          Duration (default 0.5)" << std::endl;
    std::cout << "  --shift <deg>      Phase Shift (for phase-noise)" << std::endl;
    std::cout << "  --out <file>       Output binary file (default: technique.bin)" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { print_help(); return 1; }

    std::string tech = "noise";
    double bw = 1e6;
    double rate = 2e6;
    double len = 0.5;
    double freq = 2412e6;
    double gain = 0.0;
    double shift = 180.0;
    bool do_stream = false;
    std::string out_file = "technique.bin";

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--tech") tech = argv[++i];
        else if (arg == "--bw") bw = std::stod(argv[++i]);
        else if (arg == "--rate") rate = std::stod(argv[++i]);
        else if (arg == "--len") len = std::stod(argv[++i]);
        else if (arg == "--freq") freq = std::stod(argv[++i]);
        else if (arg == "--gain") gain = std::stod(argv[++i]);
        else if (arg == "--shift") shift = std::stod(argv[++i]);
        else if (arg == "--stream") do_stream = true;
        else if (arg == "--out") out_file = argv[++i];
    }

    // Safety Check: Max Gain for 50W Amp protection
    // S4 Max output is ~10dBm. 1W is 30dBm. 
    // We cap the 'gain' setting to 30 to be absolutely sure.
    if (gain > 30.0) {
        std::cerr << "!!! SAFETY ALERT: Gain " << gain << "dB exceeds safety limit for 50W Amp. Clipping to 30dB." << std::endl;
        gain = 30.0;
    }

    std::cout << "Generating " << tech << "..." << std::endl;
    std::vector<std::complex<float>> wf;

    // Use 0.5 amplitude for math safety (prevent digital clipping)
    if (tech == "noise") wf = WaveformEngine::narrowbandNoise(bw, rate, len, "complex", 0.5f);
    else if (tech == "phase-noise") wf = WaveformEngine::phaseShiftedNoise(bw, rate, len, shift, 1000.0, 0.5f);
    else if (tech == "comb") wf = WaveformEngine::differentialComb(bw/10, 10, rate, len, 0.5f);
    else if (tech == "chirp") wf = WaveformEngine::lfmChirp(-bw/2, bw/2, rate, len, 0.5f);
    else if (tech == "ofdm") wf = WaveformEngine::ofdmShapedNoise(64, 48, 16, rate, len, 0.5f);
    else { std::cerr << "Unknown technique: " << tech << std::endl; return 1; }

    if (do_stream) {
#ifdef USE_SOAPY
        std::cout << "Streaming to Sidekiq S4 at " << freq/1e6 << " MHz (Gain: " << gain << " dB)..." << std::endl;
        try {
            SoapySDR::Device *device = SoapySDR::Device::make("driver=sidekiq");
            if (device == nullptr) { std::cerr << "No Sidekiq found via SoapySDR!" << std::endl; return 1; }
            
            device->setSampleRate(SOAPY_SDR_TX, 0, rate);
            device->setFrequency(SOAPY_SDR_TX, 0, freq);
            device->setGain(SOAPY_SDR_TX, 0, gain);

            SoapySDR::Stream *txStream = device->setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32, {0});
            device->activateStream(txStream);

            std::cout << "TRANSMITTING. Press Ctrl+C to kill." << std::endl;
            const void *buffs[] = {wf.data()};
            while (true) {
                int ret = device->writeStream(txStream, buffs, wf.size(), 0);
                if (ret < 0) break;
            }
            
            device->deactivateStream(txStream);
            device->closeStream(txStream);
            SoapySDR::Device::unmake(device);
        } catch (const std::exception &ex) {
            std::cerr << "Hardware Error: " << ex.what() << std::endl;
        }
#else
        std::cerr << "Direct streaming requires SNG to be compiled with SoapySDR support (-DUSE_SOAPY)." << std::endl;
#endif
    } else {
        std::cout << "Saving " << wf.size() << " samples to " << out_file << "..." << std::endl;
        std::ofstream out(out_file, std::ios::binary);
        out.write(reinterpret_cast<const char*>(wf.data()), wf.size() * sizeof(std::complex<float>));
        out.close();
        std::cout << "Done." << std::endl;
    }

    return 0;
}
