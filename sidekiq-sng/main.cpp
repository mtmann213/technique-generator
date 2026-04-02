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
    std::cout << "Sidekiq-Native Generator (SNG) v1.15" << std::endl;
    std::cout << "Usage: ./sng --tech <name> --bw <hz> --rate <hz> [options]" << std::endl;
    std::cout << "\nOptions:" << std::endl;
    std::cout << "  --stream           Stream directly to hardware" << std::endl;
    std::cout << "  --chan <0-3>       Physical Hardware Channel (default 0)" << std::endl;
    std::cout << "  --freq <hz>        Hardware Center Frequency" << std::endl;
    std::cout << "  --gain <db>        Hardware TX Gain (Enforced 30dB cap)" << std::endl;
    std::cout << "  --offset <hz>      Software Frequency Offset" << std::endl;
    std::cout << "  --sc16             Save as 16-bit complex integer (SC16)" << std::endl;
    std::cout << "  --amp <val>        Digital amplitude (0.0 - 1.0, default 0.5)" << std::endl;
    std::cout << "  --out <file>       Output binary file" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { print_help(); return 1; }

    std::string tech = "noise";
    std::string hops = "-200000 0 200000";
    double hop_dur = 0.01;
    double bw = 1e6;
    double rate = 2e6;
    double len = 0.01;
    double freq = 2412e6;
    double offset = 0.0;
    double gain = 0.0;
    int chan = 0;
    double shift = 180.0;
    double shift_rate = 1000.0;
    double mod_rate = 1000.0;
    double sweep_rate = 0.0;
    double rolloff = 0.35;
    int spikes = 10;
    double spacing = 30000.0;
    double pulse_gap = 10.0;
    std::string mode = "both";
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
        else if (arg == "--chan" && i + 1 < argc) chan = std::stoi(argv[++i]);
        else if (arg == "--offset" && i + 1 < argc) offset = std::stod(argv[++i]);
        else if (arg == "--gain" && i + 1 < argc) gain = std::stod(argv[++i]);
        else if (arg == "--shift" && i + 1 < argc) shift = std::stod(argv[++i]);
        else if (arg == "--shift-rate" && i + 1 < argc) shift_rate = std::stod(argv[++i]);
        else if (arg == "--mod-rate" && i + 1 < argc) mod_rate = std::stod(argv[++i]);
        else if (arg == "--sweep-rate" && i + 1 < argc) sweep_rate = std::stod(argv[++i]);
        else if (arg == "--rolloff" && i + 1 < argc) rolloff = std::stod(argv[++i]);
        else if (arg == "--spikes" && i + 1 < argc) spikes = std::stoi(argv[++i]);
        else if (arg == "--spacing" && i + 1 < argc) spacing = std::stod(argv[++i]);
        else if (arg == "--hops" && i + 1 < argc) hops = argv[++i];
        else if (arg == "--hop-dur" && i + 1 < argc) hop_dur = std::stod(argv[++i]);
        else if (arg == "--pulse-gap" && i + 1 < argc) pulse_gap = std::stod(argv[++i]);
        else if (arg == "--mode" && i + 1 < argc) mode = argv[++i];
        else if (arg == "--amp" && i + 1 < argc) amp = std::stod(argv[++i]);
        else if (arg == "--stream") do_stream = true;
        else if (arg == "--sc16") format_sc16 = true;
        else if (arg == "--out" && i + 1 < argc) out_file = argv[++i];
    }

    if (gain > 30.0) gain = 30.0;
    if (amp > 1.0) amp = 1.0;
    if (len < 0.001) len = 0.001;

    (void)freq; (void)chan; // Silence warnings

    std::cout << "Generating " << tech << "..." << std::endl;
    std::vector<std::complex<float>> wf;
    float famp = static_cast<float>(amp);

    if (tech == "noise") wf = WaveformEngine::narrowbandNoise(bw, rate, len, "complex", famp);
    else if (tech == "phase-noise") wf = WaveformEngine::phaseShiftedNoise(bw, rate, len, shift, shift_rate, famp);
    else if (tech == "comb") wf = WaveformEngine::differentialComb(spacing, spikes, rate, len, famp);
    else if (tech == "chirp") wf = WaveformEngine::lfmChirp(-bw/2, bw/2, rate, len, famp);
    else if (tech == "ofdm") {
        double spacing_hz = rate / 64.0;
        int num_subcarriers = static_cast<int>(bw / spacing_hz);
        if (num_subcarriers > 52) num_subcarriers = 52; 
        if (num_subcarriers < 1) num_subcarriers = 1;
        wf = WaveformEngine::ofdmShapedNoise(64, num_subcarriers, 16, rate, len, famp);
    }
    else if (tech == "fhss") wf = WaveformEngine::fhssNoise(hops, hop_dur, bw, rate, len, "complex", famp);
    else if (tech == "confusion") wf = WaveformEngine::correlatorConfusion(bw, rate, len, pulse_gap, mode, famp);
    else if (tech == "noise-tones") wf = WaveformEngine::noiseTones(hops, bw, rate, len, "complex", famp);
    else if (tech == "chunked-noise") wf = WaveformEngine::chunkedNoise(bw, spikes, rate, len, sweep_rate, "complex", famp);
    else if (tech == "rrc") wf = WaveformEngine::rrcModulatedNoise(bw, rate, rolloff, len, famp);
    else if (tech == "fm-cosine") wf = WaveformEngine::fmCosine(bw, mod_rate, rate, len, famp);
    else { std::cerr << "Unknown technique: " << tech << std::endl; return 1; }

    if (offset != 0.0) {
        std::cout << "  (Applying " << offset/1e3 << " kHz software offset)" << std::endl;
        WaveformEngine::applyFrequencyShift(wf, offset, rate);
    }

    if (wf.empty()) { std::cerr << "Error: Generated waveform is empty." << std::endl; return 1; }

    if (do_stream) {
#ifdef USE_SOAPY
        std::cout << "Streaming to Sidekiq Channel " << chan << "..." << std::endl;
        try {
            SoapySDR::Device *device = SoapySDR::Device::make("driver=sidekiq");
            if (!device) return 1;
            device->setSampleRate(SOAPY_SDR_TX, chan, rate);
            device->setFrequency(SOAPY_SDR_TX, chan, freq);
            device->setGain(SOAPY_SDR_TX, chan, gain);
            SoapySDR::Stream *txStream = device->setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32, {(size_t)chan});
            device->activateStream(txStream);
            std::cout << "TRANSMITTING. Press Ctrl+C to kill." << std::endl;
            while (true) {
                size_t total_written = 0;
                while (total_written < wf.size()) {
                    const void *buffs[] = {wf.data() + total_written};
                    int ret = device->writeStream(txStream, buffs, wf.size() - total_written, 0);
                    if (ret < 0) goto end_stream;
                    total_written += ret;
                }
            }
end_stream:
            device->deactivateStream(txStream);
            device->closeStream(txStream);
            SoapySDR::Device::unmake(device);
        } catch (...) {}
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
