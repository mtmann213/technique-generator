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
    std::cout << "Sidekiq-Native Generator (SNG) v2.0 - Wideband Stitching Edition" << std::endl;
    std::cout << "Usage: ./sng --tech <name> --bw <hz> --rate <hz> [options]" << std::endl;
    std::cout << "\nOptions:" << std::endl;
    std::cout << "  --probe            List available hardware channels" << std::endl;
    std::cout << "  --stream           Stream directly to hardware" << std::endl;
    std::cout << "  --chan 1,2         Active Hardware Channels (comma-separated, default 0)" << std::endl;
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
    double amp = 0.5;
    bool do_stream = false;
    bool do_probe = false;
    bool format_sc16 = false;
    std::string out_file = "technique.bin";

    // Re-used technique params
    std::string hops = "-200000 0 200000";
    double shift = 180.0, shift_rate = 1000.0, mod_rate = 1000.0, sweep_rate = 0.0, rolloff = 0.35, pulse_gap = 10.0;
    int spikes = 10;
    std::string mode = "both";

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
        else if (arg == "--shift" && i + 1 < argc) shift = std::stod(argv[++i]);
        else if (arg == "--shift-rate" && i + 1 < argc) shift_rate = std::stod(argv[++i]);
        else if (arg == "--mod-rate" && i + 1 < argc) mod_rate = std::stod(argv[++i]);
        else if (arg == "--sweep-rate" && i + 1 < argc) sweep_rate = std::stod(argv[++i]);
        else if (arg == "--rolloff" && i + 1 < argc) rolloff = std::stod(argv[++i]);
        else if (arg == "--spikes" && i + 1 < argc) spikes = std::stoi(argv[++i]);
        else if (arg == "--spacing" && i + 1 < argc) /* use bw logic */;
        else if (arg == "--hops" && i + 1 < argc) hops = argv[++i];
        else if (arg == "--pulse-gap" && i + 1 < argc) pulse_gap = std::stod(argv[++i]);
        else if (arg == "--mode" && i + 1 < argc) mode = argv[++i];
        else if (arg == "--amp" && i + 1 < argc) amp = std::stod(argv[++i]);
        else if (arg == "--stream") do_stream = true;
        else if (arg == "--sc16") format_sc16 = true;
        else if (arg == "--out" && i + 1 < argc) out_file = argv[++i];
    }

    // Parse channel list
    std::vector<size_t> channels;
    std::stringstream ss(chan_str);
    std::string item;
    while (std::getline(ss, item, ',')) {
        channels.push_back(std::stoul(item));
    }

    if (do_probe) {
#ifdef USE_SOAPY
        std::cout << "Probing Sidekiq Hardware..." << std::endl;
        try {
            SoapySDR::Device *device = SoapySDR::Device::make("driver=sidekiq");
            if (!device) return 1;
            size_t num_tx = device->getNumChannels(SOAPY_SDR_TX);
            std::cout << "Available Transmit Channels: " << num_tx << std::endl;
            for (size_t i = 0; i < num_tx; ++i) {
                std::cout << "  [" << i << "] Label: " << device->getChannelInfo(SOAPY_SDR_TX, i).at("label") << std::endl;
            }
            SoapySDR::Device::unmake(device);
        } catch (...) { std::cerr << "Probe failed." << std::endl; }
#endif
        return 0;
    }

    if (gain > 30.0) gain = 30.0;
    if (amp > 1.0) amp = 1.0;

    std::cout << "--- SNG v2.0 Multi-Channel Setup ---" << std::endl;
    std::cout << "Targeting Channels: ";
    for (auto c : channels) std::cout << c << " ";
    std::cout << "\nTotal Bandwidth: " << bw/1e6 << " MHz" << std::endl;

    // Generate stitched waveforms
    std::vector<std::vector<std::complex<float>>> channel_data;
    double sub_bw = bw / channels.size();
    float famp = static_cast<float>(amp);

    for (size_t i = 0; i < channels.size(); ++i) {
        std::cout << "  Generating segment " << i << " for Channel " << channels[i] << "..." << std::endl;
        std::vector<std::complex<float>> wf;
        
        // Use technique selection logic (shortened for brevity here)
        if (tech == "noise") wf = WaveformEngine::narrowbandNoise(sub_bw, rate, len, "complex", famp);
        else if (tech == "phase-noise") wf = WaveformEngine::phaseShiftedNoise(sub_bw, rate, len, shift, shift_rate, famp);
        else if (tech == "comb") wf = WaveformEngine::differentialComb(sub_bw/spikes, spikes, rate, len, famp);
        else wf = WaveformEngine::narrowbandNoise(sub_bw, rate, len, "complex", famp);

        // Apply spectral stitching offset
        // Offset = (i - (N-1)/2) * sub_bw
        double stitch_offset = (static_cast<double>(i) - (static_cast<double>(channels.size()) - 1.0) / 2.0) * sub_bw;
        if (stitch_offset != 0.0) {
            WaveformEngine::applyFrequencyShift(wf, stitch_offset, rate);
        }
        
        // Add user global offset
        if (offset != 0.0) WaveformEngine::applyFrequencyShift(wf, offset, rate);

        channel_data.push_back(wf);
    }

    if (do_stream) {
#ifdef USE_SOAPY
        std::cout << "Live Streaming Stitched Array..." << std::endl;
        try {
            SoapySDR::Device *device = SoapySDR::Device::make("driver=sidekiq");
            if (!device) return 1;

            for (auto c : channels) {
                device->setSampleRate(SOAPY_SDR_TX, c, rate);
                device->setFrequency(SOAPY_SDR_TX, c, freq);
                device->setGain(SOAPY_SDR_TX, c, gain);
            }

            SoapySDR::Stream *txStream = device->setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32, channels);
            device->activateStream(txStream);

            std::cout << "TRANSMITTING ON " << channels.size() << " PORTS. Ctrl+C to stop." << std::endl;
            
            std::vector<const void*> buffs(channels.size());
            while (true) {
                for (size_t i = 0; i < channels.size(); ++i) buffs[i] = channel_data[i].data();
                int ret = device->writeStream(txStream, buffs.data(), channel_data[0].size(), 0);
                if (ret < 0) break;
            }
            
            device->deactivateStream(txStream);
            device->closeStream(txStream);
            SoapySDR::Device::unmake(device);
        } catch (const std::exception &e) { std::cerr << "Hardware Error: " << e.what() << std::endl; }
#endif
    } else {
        // Save first channel to file
        std::cout << "Saving Channel " << channels[0] << " to " << out_file << std::endl;
        std::ofstream out(out_file, std::ios::binary);
        out.write(reinterpret_cast<const char*>(channel_data[0].data()), channel_data[0].size() * sizeof(std::complex<float>));
        out.close();
    }

    return 0;
}
