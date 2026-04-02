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
    std::cout << "Sidekiq-Native Generator (SNG) v1.2" << std::endl;
    std::cout << "Usage: ./sng --tech <name> --bw <hz> --rate <hz> [options]" << std::endl;
    std::cout << "\nAvailable Techniques:" << std::endl;
    std::cout << "  noise, phase-noise, comb, chirp, ofdm" << std::endl;
    std::cout << "\nOptions:" << std::endl;
    std::cout << "  --stream           Stream directly to hardware (requires SoapySDR)" << std::endl;
    std::cout << "  --gain <db>        Hardware TX Gain (Safety Limit: 0-30dB, default 0)" << std::endl;
    std::cout << "  --freq <hz>        Center Frequency for streaming" << std::endl;
    std::cout << "  --len <s>          Duration (Min: 0.001, default 0.01)" << std::endl;
    std::cout << "  --shift <deg>      Phase Shift (for phase-noise)" << std::endl;
    std::cout << "  --sc16             Save output as 16-bit complex integer (SC16) instead of 32-bit float" << std::endl;
    std::cout << "  --amp <val>        Digital amplitude scaling (0.0 - 1.0, default 0.5)" << std::endl;
    std::cout << "  --out <file>       Output binary file (default: technique.bin)" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { print_help(); return 1; }

    std::string tech = "noise";
    double bw = 1e6;
    double rate = 2e6;
    double len = 0.01;
    double freq = 2412e6;
    double gain = 0.0;
    double shift = 180.0;
    double amp = 0.5;
    bool do_stream = false;
    bool format_sc16 = false;
    std::string out_file = "technique.bin";

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--tech" && i + 1 < argc) tech = argv[++i];
        else if (arg == "--bw" && i + 1 < argc) bw = std::stod(argv[++i]);
        else if (arg == "--rate" && i + 1 < argc) rate = std::stod(argv[++i]);
        else if (arg == "--len" && i + 1 < argc) len = std::stod(argv[++i]);
        else if (arg == "--freq" && i + 1 < argc) freq = std::stod(argv[++i]);
        else if (arg == "--gain" && i + 1 < argc) gain = std::stod(argv[++i]);
        else if (arg == "--shift" && i + 1 < argc) shift = std::stod(argv[++i]);
        else if (arg == "--amp" && i + 1 < argc) amp = std::stod(argv[++i]);
        else if (arg == "--stream") do_stream = true;
        else if (arg == "--sc16") format_sc16 = true;
        else if (arg == "--out" && i + 1 < argc) out_file = argv[++i];
    }

    // Safety Checks
    if (gain > 30.0) gain = 30.0;
    if (amp > 1.0) amp = 1.0;
    if (len < 0.001) len = 0.001;

    std::cout << "Generating " << tech << "..." << std::endl;
    std::vector<std::complex<float>> wf;

    float famp = static_cast<float>(amp);
    if (tech == "noise") wf = WaveformEngine::narrowbandNoise(bw, rate, len, "complex", famp);
    else if (tech == "phase-noise") wf = WaveformEngine::phaseShiftedNoise(bw, rate, len, shift, 1000.0, famp);
    else if (tech == "comb") wf = WaveformEngine::differentialComb(bw/10, 10, rate, len, famp);
    else if (tech == "chirp") wf = WaveformEngine::lfmChirp(-bw/2, bw/2, rate, len, famp);
    else if (tech == "ofdm") wf = WaveformEngine::ofdmShapedNoise(64, 48, 16, rate, len, famp);
    else { std::cerr << "Unknown technique: " << tech << std::endl; return 1; }

    if (wf.empty()) { std::cerr << "Error: Generated waveform is empty." << std::endl; return 1; }

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
            while (true) {
                size_t total_written = 0;
                while (total_written < wf.size()) {
                    const void *buffs[] = {wf.data() + total_written};
                    int ret = device->writeStream(txStream, buffs, wf.size() - total_written, 0);
                    if (ret < 0) {
                        std::cerr << "\nWrite error: " << ret << std::endl;
                        goto end_stream;
                    }
                    total_written += ret;
                }
            }
end_stream:
            
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
        if (format_sc16) {
            std::vector<int16_t> sc16_data(wf.size() * 2);
            for (size_t i = 0; i < wf.size(); ++i) {
                sc16_data[i*2] = static_cast<int16_t>(wf[i].real() * 32767.0f);
                sc16_data[i*2+1] = static_cast<int16_t>(wf[i].imag() * 32767.0f);
            }
            out.write(reinterpret_cast<const char*>(sc16_data.data()), sc16_data.size() * sizeof(int16_t));
        } else {
            out.write(reinterpret_cast<const char*>(wf.data()), wf.size() * sizeof(std::complex<float>));
        }
        out.close();
        std::cout << "Done." << std::endl;
    }

    return 0;
}
