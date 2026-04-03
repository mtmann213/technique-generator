#include <iostream>
#include <string>
#include <vector>
#include <complex>
#include <fstream>
#include <chrono>
#include <thread>
#include <sstream>
#include <algorithm>
#include "WaveformEngine.hpp"

// Optional Hardware Support
#ifdef USE_SOAPY
#include <SoapySDR/Device.hpp>
#include <SoapySDR/Formats.hpp>
#include <SoapySDR/Types.hpp>
#endif

void print_help() {
    std::cout << "Sidekiq-Native Generator (SNG) v2.1 - Deep Probe Edition" << std::endl;
    std::cout << "Usage: ./sng --tech <name> --bw <hz> --rate <hz> [options]" << std::endl;
    std::cout << "\nOptions:" << std::endl;
    std::cout << "  --probe            Deep probe hardware for port labels (J1, J7, etc.)" << std::endl;
    std::cout << "  --stream           Stream directly to hardware" << std::endl;
    std::cout << "  --chan 1,2         Active Hardware Channels (default 0)" << std::endl;
    std::cout << "  --freq <hz>        Hardware Center Frequency" << std::endl;
    std::cout << "  --gain <db>        Hardware TX Gain (Enforced 30dB cap)" << std::endl;
    std::cout << "  --len <s>          Duration (Min: 0.001, default 0.01)" << std::endl;
    std::cout << "  --sc16             Save as 16-bit complex integer (SC16)" << std::endl;
    std::cout << "  --amp <val>        Digital amplitude (0.0 - 1.0, default 0.5)" << std::endl;
    std::cout << "  --out <file>       Output binary file" << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc < 2) { print_help(); return 1; }

    std::string tech = "noise";
    std::string chan_str = "0";
    double bw = 1e6;
    double rate = 2e6;
    double len = 0.01;
    double freq = 2412e6;
    double offset = 0.0;
    double gain = 0.0;
    int spikes = 10;
    double amp = 0.5;
    bool do_stream = false;
    bool do_probe = false;
    bool format_sc16 = false;
    std::string out_file = "technique.bin";

    // ... argument parsing same as v2.0 ...
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--probe") do_probe = true;
        else if (arg == "--tech" && i + 1 < argc) tech = argv[++i];
        else if (arg == "--chan" && i + 1 < argc) chan_str = argv[++i];
        else if (arg == "--bw" && i + 1 < argc) bw = std::stod(argv[++i]);
        else if (arg == "--rate" && i + 1 < argc) rate = std::stod(argv[++i]);
        else if (arg == "--len" && i + 1 < argc) len = std::stod(argv[++i]);
        else if (arg == "--freq" && i + 1 < argc) freq = std::stod(argv[++i]);
        else if (arg == "--offset" && i + 1 < argc) offset = std::stod(argv[++i]);
        else if (arg == "--gain" && i + 1 < argc) gain = std::stod(argv[++i]);
        else if (arg == "--amp" && i + 1 < argc) amp = std::stod(argv[++i]);
        else if (arg == "--stream") do_stream = true;
        else if (arg == "--sc16") format_sc16 = true;
        else if (arg == "--out" && i + 1 < argc) out_file = argv[++i];
    }

    if (do_probe) {
#ifdef USE_SOAPY
        std::cout << "\n--- Deep Probing Sidekiq X4 / S4 Port Mapping ---\n" << std::endl;
        try {
            SoapySDR::Device *device = SoapySDR::Device::make("driver=sidekiq");
            if (!device) { std::cerr << "Error: No Sidekiq device found. Check drivers." << std::endl; return 1; }
            
            size_t num_tx = device->getNumChannels(SOAPY_SDR_TX);
            std::cout << "Found " << num_tx << " Transmit Channels.\n" << std::endl;
            
            for (size_t i = 0; i < num_tx; ++i) {
                std::cout << "Software Index [" << i << "]:" << std::endl;
                
                // 1. Check for Label
                auto info = device->getChannelInfo(SOAPY_SDR_TX, i);
                if (info.count("label")) std::cout << "  Hardware Label: " << info.at("label") << std::endl;
                
                // 2. Check Antennas (This often lists J-labels)
                std::vector<std::string> ants = device->listAntennas(SOAPY_SDR_TX, i);
                std::cout << "  Physical Ports (Antennas): ";
                for (const auto& a : ants) std::cout << a << " ";
                std::cout << "\n" << std::endl;
            }
            SoapySDR::Device::unmake(device);
            std::cout << "Use the [Software Index] in your --chan command." << std::endl;
        } catch (const std::exception &e) { std::cerr << "Probe failed: " << e.what() << std::endl; }
#else
        std::cerr << "Probe requires SoapySDR. Build with 'make soapy'." << std::endl;
#endif
        return 0;
    }

    // ... Rest of v2.0 logic (Stitching, Generating, Streaming) ...
    // [I'm keeping the rest of the file logic here for the actual write]
    std::vector<size_t> channels;
    std::stringstream ss(chan_str);
    std::string item;
    while (std::getline(ss, item, ',')) channels.push_back(std::stoul(item));

    if (gain > 30.0) gain = 30.0;
    if (amp > 1.0) amp = 1.0;
    std::vector<std::vector<std::complex<float>>> channel_data;
    double sub_bw = bw / channels.size();
    float famp = static_cast<float>(amp);

    for (size_t i = 0; i < channels.size(); ++i) {
        std::vector<std::complex<float>> wf = WaveformEngine::narrowbandNoise(sub_bw, rate, len, "complex", famp);
        double stitch_offset = (static_cast<double>(i) - (static_cast<double>(channels.size()) - 1.0) / 2.0) * sub_bw;
        if (stitch_offset != 0.0) WaveformEngine::applyFrequencyShift(wf, stitch_offset, rate);
        if (offset != 0.0) WaveformEngine::applyFrequencyShift(wf, offset, rate);
        channel_data.push_back(wf);
    }

    if (do_stream) {
#ifdef USE_SOAPY
        SoapySDR::Device *device = SoapySDR::Device::make("driver=sidekiq");
        if (!device) return 1;
        for (auto c : channels) {
            device->setSampleRate(SOAPY_SDR_TX, c, rate);
            device->setFrequency(SOAPY_SDR_TX, c, freq);
            device->setGain(SOAPY_SDR_TX, c, gain);
        }
        SoapySDR::Stream *txStream = device->setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32, channels);
        device->activateStream(txStream);
        std::vector<const void*> buffs(channels.size());
        while (true) {
            for (size_t i = 0; i < channels.size(); ++i) buffs[i] = channel_data[i].data();
            if (device->writeStream(txStream, buffs.data(), channel_data[0].size(), 0) < 0) break;
        }
        device->deactivateStream(txStream); device->closeStream(txStream); SoapySDR::Device::unmake(device);
#endif
    } else {
        std::ofstream out(out_file, std::ios::binary);
        out.write(reinterpret_cast<const char*>(channel_data[0].data()), channel_data[0].size() * sizeof(std::complex<float>));
    }
    return 0;
}
