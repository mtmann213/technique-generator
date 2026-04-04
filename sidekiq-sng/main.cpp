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

    // Technique params
    std::string hops = "-200000 0 200000";
    double hop_dur = 0.01;
    double shift = 180.0;
    double shift_rate = 1000.0;
    double mod_rate = 1000.0;
    double sweep_rate = 0.0;
    double rolloff = 0.35;
    double spacing = 30000.0;
    double pulse_gap = 10.0;
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
        else if (arg == "--amp" && i + 1 < argc) amp = std::stod(argv[++i]);
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
                
                auto info = device->getChannelInfo(SOAPY_SDR_TX, i);
                if (info.count("label")) std::cout << "  Hardware Label: " << info.at("label") << std::endl;
                
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

    std::vector<size_t> channels;
    std::stringstream ss(chan_str);
    std::string item;
    while (std::getline(ss, item, ',')) channels.push_back(std::stoul(item));

    if (amp > 1.0) amp = 1.0;
    if (len < 0.001) len = 0.001;

    (void)freq;

    std::cout << "--- SNG v2.1 Multi-Channel Setup ---" << std::endl;
    std::cout << "Targeting Channels: ";
    for (auto c : channels) std::cout << c << " ";
    std::cout << "\nTotal Bandwidth: " << bw/1e6 << " MHz" << std::endl;

    std::vector<std::vector<std::complex<float>>> channel_data;
    double sub_bw = bw / channels.size();
    float famp = static_cast<float>(amp);

    for (size_t i = 0; i < channels.size(); ++i) {
        std::cout << "  Generating segment " << i << " for Channel " << channels[i] << "..." << std::endl;
        std::vector<std::complex<float>> wf;
        
        if (tech == "noise") wf = WaveformEngine::narrowbandNoise(sub_bw, rate, len, "complex", famp);
        else if (tech == "phase-noise") wf = WaveformEngine::phaseShiftedNoise(sub_bw, rate, len, shift, shift_rate, famp);
        else if (tech == "comb") wf = WaveformEngine::differentialComb(spacing, spikes, rate, len, famp);
        else if (tech == "chirp") wf = WaveformEngine::lfmChirp(-sub_bw/2, sub_bw/2, rate, len, famp);
        else if (tech == "ofdm") {
            double spacing_hz = rate / 64.0;
            int num_subcarriers = static_cast<int>(sub_bw / spacing_hz);
            if (num_subcarriers > 52) num_subcarriers = 52; 
            if (num_subcarriers < 1) num_subcarriers = 1;
            wf = WaveformEngine::ofdmShapedNoise(64, num_subcarriers, 16, rate, len, famp);
        }
        else if (tech == "fhss") wf = WaveformEngine::fhssNoise(hops, hop_dur, sub_bw, rate, len, "complex", famp);
        else if (tech == "confusion") wf = WaveformEngine::correlatorConfusion(sub_bw, rate, len, pulse_gap, mode, famp);
        else if (tech == "noise-tones") wf = WaveformEngine::noiseTones(hops, sub_bw, rate, len, "complex", famp);
        else if (tech == "cosine-tones") wf = WaveformEngine::cosineTones(hops, rate, len, famp);
        else if (tech == "phasor-tones") wf = WaveformEngine::phasorTones(hops, rate, len, famp);
        else if (tech == "chunked-noise") wf = WaveformEngine::chunkedNoise(sub_bw, spikes, rate, len, sweep_rate, "complex", famp);
        else if (tech == "rrc") wf = WaveformEngine::rrcModulatedNoise(sub_bw, rate, rolloff, len, famp);
        else if (tech == "fm-cosine") wf = WaveformEngine::fmCosine(sub_bw, mod_rate, rate, len, famp);
        else { std::cerr << "Unknown technique: " << tech << std::endl; return 1; }

        double stitch_offset = (static_cast<double>(i) - (static_cast<double>(channels.size()) - 1.0) / 2.0) * sub_bw;
        if (stitch_offset != 0.0) WaveformEngine::applyFrequencyShift(wf, stitch_offset, rate);
        if (offset != 0.0) WaveformEngine::applyFrequencyShift(wf, offset, rate);
        
        channel_data.push_back(wf);
    }

    if (do_stream) {
#ifdef USE_SOAPY
        std::cout << "--- SNG v2.3 [STRICT DMA MODE] ---" << std::endl;
        SoapySDR::Device *device = SoapySDR::Device::make("driver=sidekiq");
        if (!device) { std::cerr << "Error: Sidekiq card not found." << std::endl; return 1; }
        
        for (auto c : channels) {
            std::cout << "[TUNE] Channel " << c << " -> " << freq/1e6 << " MHz" << std::endl;
            device->setSampleRate(SOAPY_SDR_TX, c, rate);
            device->setFrequency(SOAPY_SDR_TX, c, freq);
            device->setGain(SOAPY_SDR_TX, c, gain);
            
            // Critical: Force Antenna Selection for Port Switching
            std::vector<std::string> ants = device->listAntennas(SOAPY_SDR_TX, c);
            if (!ants.empty()) {
                std::string target_ant = ants.back(); 
                std::cout << "[TUNE] Channel " << c << " Antenna: " << target_ant << " (of " << ants.size() << " available)" << std::endl;
                device->setAntenna(SOAPY_SDR_TX, c, target_ant);
            }
            
            // MASTER ENABLE: Some Sidekiq cards require individual activation per channel
            // to power up the internal amplifiers (PA).
            std::cout << "[TUNE] Activating TX Path for Channel " << c << "..." << std::endl;
            device->writeSetting(SOAPY_SDR_TX, c, "TX_EN", "true");
        }
        std::cout << "[TUNE] Waiting for synthesizers to settle..." << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(500));

        SoapySDR::Stream *txStream = device->setupStream(SOAPY_SDR_TX, SOAPY_SDR_CF32, channels);
        size_t mtu = device->getStreamMTU(txStream);
        std::cout << "[DMA] Hardware MTU: " << mtu << " samples." << std::endl;
        
        // Pad all buffers to be a multiple of MTU
        for (auto& wf : channel_data) {
            size_t remainder = wf.size() % mtu;
            if (remainder != 0) {
                wf.insert(wf.end(), mtu - remainder, std::complex<float>(0, 0));
            }
        }
        
        device->activateStream(txStream);
        std::vector<const void*> buffs(channels.size());
        size_t total_aligned = channel_data[0].size();
        int flags = 0;
        long timeout_us = 1000000;
        int num_elems = (int)mtu;
        
        int loop_count = 0;
        std::cout << "[DMA] Streaming started. Press Ctrl+C to stop." << std::endl;
        
        while (true) {
            size_t sent = 0;
            while (sent < total_aligned) {
                for (size_t i = 0; i < channels.size(); ++i) buffs[i] = channel_data[i].data() + sent;
                
                int ret = device->writeStream(txStream, buffs.data(), num_elems, flags, timeout_us);
                if (ret == num_elems) {
                    sent += ret;
                    if (++loop_count % 100 == 0) {
                        std::cout << "." << std::flush;
                    }
                } else if (ret >= 0) {
                    std::cout << "T" << std::flush;
                    continue; // Timeout
                } else {
                    std::cerr << "\nDMA Write Error: " << ret << std::endl;
                    goto end_stream;
                }
            }
        }
        end_stream:
        device->deactivateStream(txStream); device->closeStream(txStream); SoapySDR::Device::unmake(device);
#endif
    } else {
        std::ofstream out(out_file, std::ios::binary);
        if (format_sc16) {
            std::vector<int16_t> sc16_data(channel_data[0].size() * 2);
            for (size_t i = 0; i < channel_data[0].size(); ++i) {
                sc16_data[i*2] = static_cast<int16_t>(channel_data[0][i].real() * 32767.0f);
                sc16_data[i*2+1] = static_cast<int16_t>(channel_data[0][i].imag() * 32767.0f);
            }
            out.write(reinterpret_cast<const char*>(sc16_data.data()), sc16_data.size() * sizeof(int16_t));
        } else {
            out.write(reinterpret_cast<const char*>(channel_data[0].data()), channel_data[0].size() * sizeof(std::complex<float>));
        }
    }
    return 0;
}
