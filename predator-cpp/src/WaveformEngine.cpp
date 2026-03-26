#include "WaveformEngine.hpp"
#include <random>
#include <cmath>
#include <algorithm>
#include <numeric>
#include <sstream>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// Existing method
std::vector<std::complex<float>> WaveformEngine::generateNarrowbandNoise(double sample_rate, double bw, double duration) {
    return narrowbandNoise(bw, sample_rate, duration);
}

// Helpers
std::vector<double> WaveformEngine::createTimeArray(double sample_rate_hz, double technique_length_seconds) {
    size_t num_samples = static_cast<size_t>(std::floor(sample_rate_hz * technique_length_seconds));
    if (num_samples == 0) return {};
    std::vector<double> time(num_samples);
    for (size_t i = 0; i < num_samples; ++i) {
        time[i] = static_cast<double>(i) / sample_rate_hz;
    }
    return time;
}

void WaveformEngine::normalizeSignal(std::vector<std::complex<float>>& samples, float target_value, std::string normalization_type) {
    if (target_value <= 0 || samples.empty()) return;
    if (normalization_type == "peak") {
        float max_val = 0;
        for (const auto& s : samples) {
            max_val = std::max(max_val, std::abs(s));
        }
        if (max_val > 0) {
            float scale = target_value / max_val;
            for (auto& s : samples) s *= scale;
        }
    } else if (normalization_type == "rms") {
        double sum_sq = 0;
        for (const auto& s : samples) {
            sum_sq += std::norm(s);
        }
        float rms_val = std::sqrt(static_cast<float>(sum_sq / samples.size()));
        if (rms_val > 0) {
            float scale = target_value / rms_val;
            for (auto& s : samples) s *= scale;
        }
    }
}

void WaveformEngine::applySpectralShaping(std::vector<std::complex<float>>& samples, double bandwidth_hz, double sample_rate_hz, std::string filter_type, double rolloff) {
    if (filter_type == "none" || samples.empty()) return;
    // Filter design (firwin, lfilter) bypassed in this native port.
    // Core signal synthesis is prioritized over spectral shaping.
}

std::vector<double> WaveformEngine::rootRaisedCosineFilter(double symbol_rate_hz, double sample_rate_hz, double rolloff, int num_taps) {
    if (num_taps % 2 == 0) num_taps++;
    double Ts = 1.0 / symbol_rate_hz;
    std::vector<double> h(num_taps);
    int mid = num_taps / 2;
    for (int i = 0; i < num_taps; ++i) {
        double t = static_cast<double>(i - mid) / sample_rate_hz;
        double ti_norm = t / Ts;
        if (std::abs(t) < 1e-12) {
            h[i] = (1.0 / Ts) * (1.0 - rolloff + (4.0 * rolloff / M_PI));
        } else if (std::abs(std::abs(ti_norm) - 1.0 / (4.0 * rolloff)) < 1e-12) {
            h[i] = (rolloff / (std::sqrt(2.0) * Ts)) * (
                (1.0 + 2.0 / M_PI) * std::sin(M_PI / (4.0 * rolloff)) +
                (1.0 - 2.0 / M_PI) * std::cos(M_PI / (4.0 * rolloff))
            );
        } else {
            double numerator = std::sin(M_PI * ti_norm * (1.0 - rolloff)) +
                               4.0 * rolloff * ti_norm * std::cos(M_PI * ti_norm * (1.0 + rolloff));
            double denominator = M_PI * ti_norm * (1.0 - std::pow(4.0 * rolloff * ti_norm, 2));
            h[i] = (1.0 / Ts) * (numerator / denominator);
        }
    }
    double sum_sq = 0;
    for (double val : h) sum_sq += val * val;
    if (sum_sq > 1e-9) {
        double norm = std::sqrt(sum_sq);
        for (double& val : h) val /= norm;
    }
    return h;
}

// Waveform Generation Methods

std::vector<std::complex<float>> WaveformEngine::correlatorConfusion(
    double bandwidth_hz,
    double sample_rate_hz,
    double technique_length_seconds,
    double pulse_interval_ms,
    std::string confusion_mode,
    float target_value,
    std::string normalization_type,
    std::string filter_type
) {
    size_t total_samples = static_cast<size_t>(std::floor(sample_rate_hz * technique_length_seconds));
    std::vector<std::complex<float>> out(total_samples, std::complex<float>(0, 0));
    
    int N_zc = 127;
    int root = 1;
    std::vector<std::complex<float>> zc(N_zc);
    for (int n = 0; n < N_zc; ++n) {
        float phase = -static_cast<float>(M_PI * root * n * (n + 1) / N_zc);
        zc[n] = std::exp(std::complex<float>(0, phase));
    }
    
    int sps = std::max(1, static_cast<int>(sample_rate_hz / bandwidth_hz));
    std::vector<std::complex<float>> zc_pulsed(N_zc * sps, std::complex<float>(0, 0));
    for (int i = 0; i < N_zc; ++i) {
        zc_pulsed[i * sps] = zc[i];
    }
    
    // FIR filtering (firwin, lfilter) bypassed. Using raw ZC pulse.
    std::vector<std::complex<float>> zc_final = zc_pulsed;
    
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> rand_val(0.0, 1.0);
    
    size_t curr_ptr = 0;
    int interval_samps = static_cast<int>(pulse_interval_ms * sample_rate_hz / 1000.0);
    
    while (curr_ptr + zc_final.size() < total_samples) {
        std::vector<std::complex<float>> p_val = zc_final;
        if (confusion_mode == "phase_flip" || confusion_mode == "both") {
            if (rand_val(gen) > 0.5f) {
                for (auto& s : p_val) s *= -1.0f;
            }
        }
        for (size_t i = 0; i < p_val.size(); ++i) {
            out[curr_ptr + i] = p_val[i];
        }
        
        int jitter = 0;
        if (confusion_mode == "timing_jitter" || confusion_mode == "both") {
            std::uniform_int_distribution<int> jit_dist(-static_cast<int>(interval_samps * 0.2), static_cast<int>(interval_samps * 0.2));
            jitter = jit_dist(gen);
        }
        curr_ptr += std::max(zc_final.size(), static_cast<size_t>(std::max(1, interval_samps + jitter)));
    }
    
    applySpectralShaping(out, bandwidth_hz, sample_rate_hz, filter_type);
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::narrowbandNoise(
    double bandwidth_hz,
    double sample_rate_hz,
    double technique_length_seconds,
    std::string interference_type,
    float target_value,
    std::string normalization_type,
    std::string filter_type
) {
    size_t total_samples = static_cast<size_t>(std::floor(sample_rate_hz * technique_length_seconds));
    std::vector<std::complex<float>> out(total_samples);
    
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0, 1.0);
    
    // FFT/IFFT is bypassed here as per requirement.
    // Returning base white noise instead of narrowband.
    for (size_t i = 0; i < total_samples; ++i) {
        if (interference_type == "complex") {
            out[i] = std::complex<float>(dist(gen), dist(gen));
        } else {
            out[i] = std::complex<float>(dist(gen), 0.0f);
        }
    }
    
    applySpectralShaping(out, bandwidth_hz, sample_rate_hz, filter_type);
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::rrcModulatedNoise(
    double symbol_rate_hz,
    double sample_rate_hz,
    double rolloff,
    double technique_length_seconds,
    float target_value,
    std::string normalization_type,
    std::string filter_type
) {
    size_t total_samples = static_cast<size_t>(std::floor(sample_rate_hz * technique_length_seconds));
    std::vector<std::complex<float>> out(total_samples);
    
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0, 1.0);
    
    // Generating noise. Filter (lfilter) is bypassed.
    for (size_t i = 0; i < total_samples; ++i) {
        out[i] = std::complex<float>(dist(gen), 0.0f);
    }
    
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::sweptNoise(
    double sweep_hz,
    double bandwidth_hz,
    double sample_rate_hz,
    double technique_length_seconds,
    std::string sweep_type,
    double sweep_rate_hz_s,
    std::string interference_type,
    float target_value,
    std::string normalization_type,
    std::string filter_type
) {
    double effective_duration = (sweep_rate_hz_s > 0) ? (sweep_hz / sweep_rate_hz_s) : technique_length_seconds;
    std::vector<std::complex<float>> noise = narrowbandNoise(bandwidth_hz, sample_rate_hz, technique_length_seconds, interference_type, 1.0f, "peak", filter_type);
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    
    std::vector<std::complex<float>> out(time.size());
    double phase_acc = 0;
    for (size_t i = 0; i < time.size(); ++i) {
        double t_mod = std::fmod(time[i], effective_duration);
        double freq;
        if (sweep_type == "triangle") {
            freq = (2.0 * sweep_hz / effective_duration) * std::abs(t_mod - effective_duration / 2.0) - (sweep_hz / 2.0);
        } else {
            freq = (sweep_hz / effective_duration) * t_mod - (sweep_hz / 2.0);
        }
        phase_acc += 2.0 * M_PI * freq / sample_rate_hz;
        out[i] = noise[i] * std::exp(std::complex<float>(0, static_cast<float>(phase_acc)));
    }
    
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::chunkedNoise(
    double technique_width_hz,
    int chunks,
    double sample_rate_hz,
    double technique_length_seconds,
    std::string interference_type,
    float target_value,
    std::string normalization_type,
    std::string filter_type
) {
    if (chunks <= 0) return {};
    double bw = technique_width_hz / chunks;
    std::vector<std::complex<float>> noise = narrowbandNoise(bw, sample_rate_hz, technique_length_seconds, interference_type, 1.0f, "peak", filter_type);
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    
    std::vector<double> centers(chunks);
    for (int i = 0; i < chunks; ++i) {
        centers[i] = -technique_width_hz / 2.0 + bw / 2.0 + i * bw;
    }
    
    std::vector<int> order(chunks);
    std::iota(order.begin(), order.end(), 0);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::shuffle(order.begin(), order.end(), gen);
    
    std::vector<std::complex<float>> out(time.size());
    for (size_t i = 0; i < time.size(); ++i) {
        int idx = static_cast<int>(std::floor(time[i] / technique_length_seconds * chunks));
        idx = std::max(0, std::min(chunks - 1, idx));
        double freq = centers[order[idx]];
        float phase = static_cast<float>(2.0 * M_PI * freq * time[i]);
        out[i] = noise[i] * std::exp(std::complex<float>(0, phase));
    }
    
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::noiseTones(
    std::string frequencies_str,
    double bandwidth_hz,
    double sample_rate_hz,
    double technique_length_seconds,
    std::string interference_type,
    float target_value,
    std::string normalization_type,
    std::string filter_type
) {
    std::vector<double> freqs;
    std::stringstream ss(frequencies_str);
    double f;
    while (ss >> f) freqs.push_back(f);
    
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> base = narrowbandNoise(bandwidth_hz, sample_rate_hz, technique_length_seconds, interference_type, 1.0f, "peak", filter_type);
    
    std::vector<std::complex<float>> out(time.size(), std::complex<float>(0, 0));
    for (double freq : freqs) {
        for (size_t i = 0; i < time.size(); ++i) {
            float phase = static_cast<float>(2.0 * M_PI * freq * time[i]);
            out[i] += base[i] * std::exp(std::complex<float>(0, phase));
        }
    }
    
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::cosineTones(
    std::string frequencies_str,
    double sample_rate_hz,
    double technique_length_seconds,
    float target_value,
    std::string normalization_type,
    std::string filter_type
) {
    std::vector<double> freqs;
    std::stringstream ss(frequencies_str);
    double f;
    while (ss >> f) freqs.push_back(f);
    
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> out(time.size(), std::complex<float>(0, 0));
    for (double freq : freqs) {
        for (size_t i = 0; i < time.size(); ++i) {
            out[i] += std::complex<float>(static_cast<float>(std::cos(2.0 * M_PI * freq * time[i])), 0.0f);
        }
    }
    
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::phasorTones(
    std::string frequencies_str,
    double sample_rate_hz,
    double technique_length_seconds,
    float target_value,
    std::string normalization_type,
    std::string filter_type
) {
    std::vector<double> freqs;
    std::stringstream ss(frequencies_str);
    double f;
    while (ss >> f) freqs.push_back(f);
    
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> out(time.size(), std::complex<float>(0, 0));
    for (double freq : freqs) {
        for (size_t i = 0; i < time.size(); ++i) {
            float phase = static_cast<float>(2.0 * M_PI * freq * time[i]);
            out[i] += std::exp(std::complex<float>(0, phase));
        }
    }
    
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::sweptPhasors(
    double sweep_hz,
    int tones,
    double sample_rate_hz,
    double technique_length_seconds,
    float target_value,
    std::string normalization_type,
    std::string filter_type
) {
    if (tones <= 0) return {};
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> out(time.size(), std::complex<float>(0, 0));
    
    double m_sw = sweep_hz / tones;
    for (int k = 0; k < tones; ++k) {
        double f0 = -sweep_hz / 2.0 + k * (sweep_hz / tones);
        double phase_acc = 0;
        for (size_t i = 0; i < time.size(); ++i) {
            double freq = (m_sw / technique_length_seconds) * time[i] + f0;
            phase_acc += 2.0 * M_PI * freq / sample_rate_hz;
            out[i] += std::exp(std::complex<float>(0, static_cast<float>(phase_acc)));
        }
    }
    
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::sweptCosines(
    double sweep_hz,
    int tones,
    double sample_rate_hz,
    double technique_length_seconds,
    float target_value,
    std::string normalization_type,
    std::string filter_type
) {
    if (tones <= 0) return {};
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> out(time.size(), std::complex<float>(0, 0));
    
    double m_sw = sweep_hz / tones;
    for (int k = 0; k < tones; ++k) {
        double f0 = -sweep_hz / 2.0 + k * (sweep_hz / tones);
        double phase_acc = 0;
        for (size_t i = 0; i < time.size(); ++i) {
            double freq = (m_sw / technique_length_seconds) * time[i] + f0;
            phase_acc += 2.0 * M_PI * freq / sample_rate_hz;
            out[i] += std::complex<float>(static_cast<float>(std::cos(phase_acc)), 0.0f);
        }
    }
    
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::fmCosine(
    double sweep_range_hz,
    double modulated_frequency,
    double sample_rate_hz,
    double technique_length_seconds,
    float target_value,
    std::string normalization_type,
    std::string filter_type
) {
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> out(time.size());
    double phase_acc = 0;
    for (size_t i = 0; i < time.size(); ++i) {
        double dev = 0.5 * sweep_range_hz * std::cos(2.0 * M_PI * modulated_frequency * time[i]);
        phase_acc += 2.0 * M_PI * dev / sample_rate_hz;
        out[i] = std::exp(std::complex<float>(0, static_cast<float>(phase_acc)));
    }
    
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::lfmChirp(
    double start_freq_hz,
    double end_freq_hz,
    double sample_rate_hz,
    double technique_length_seconds,
    float target_value,
    std::string normalization_type,
    std::string filter_type
) {
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> out(time.size());
    for (size_t i = 0; i < time.size(); ++i) {
        double t = time[i];
        double phase = 2.0 * M_PI * (start_freq_hz * t + 0.5 * (end_freq_hz - start_freq_hz) * t * t / technique_length_seconds);
        out[i] = std::exp(std::complex<float>(0, static_cast<float>(phase)));
    }
    
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::fhssNoise(
    std::string hop_frequencies_str,
    double hop_duration_seconds,
    double bandwidth_hz,
    double sample_rate_hz,
    double technique_length_seconds,
    std::string interference_type,
    float target_value,
    std::string normalization_type,
    std::string filter_type
) {
    std::vector<double> freqs;
    std::stringstream ss(hop_frequencies_str);
    double f;
    while (ss >> f) freqs.push_back(f);
    if (freqs.empty()) return {};
    
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> base = narrowbandNoise(bandwidth_hz, sample_rate_hz, technique_length_seconds, interference_type, 1.0f, "peak", filter_type);
    
    std::vector<std::complex<float>> out(time.size());
    size_t sph = static_cast<size_t>(std::max(1.0, std::floor(sample_rate_hz * hop_duration_seconds)));
    
    for (size_t i = 0; i < time.size(); ++i) {
        size_t hop_idx = (i / sph) % freqs.size();
        float phase = static_cast<float>(2.0 * M_PI * freqs[hop_idx] * time[i]);
        out[i] = base[i] * std::exp(std::complex<float>(0, phase));
    }
    
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::ofdmShapedNoise(
    int fft_size,
    int num_subcarriers,
    int cp_length,
    double sample_rate_hz,
    double technique_length_seconds,
    float target_value,
    std::string normalization_type,
    std::string filter_type
) {
    size_t total_samples = static_cast<size_t>(std::floor(sample_rate_hz * technique_length_seconds));
    std::vector<std::complex<float>> out(total_samples);
    
    // IFFT is bypassed as per requirement.
    // Returning noise as a base waveform.
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0, 1.0);
    for (size_t i = 0; i < total_samples; ++i) {
        out[i] = std::complex<float>(dist(gen), dist(gen));
    }
    
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::songMaker(
    std::string songName,
    double bandwidth_hz,
    double sample_rate_hz,
    float target_value,
    std::string normalization_type,
    std::string filter_type
) {
    // SongMaker is bypassed and returning placeholder noise.
    size_t total_samples = static_cast<size_t>(std::floor(sample_rate_hz * 0.1)); 
    std::vector<std::complex<float>> out(total_samples);
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0, 1.0);
    for (size_t i = 0; i < total_samples; ++i) {
        out[i] = std::complex<float>(dist(gen), dist(gen));
    }
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::differentialComb(
    double spike_spacing_hz,
    int spike_count,
    double sample_rate_hz,
    double technique_length_seconds,
    float target_value,
    std::string normalization_type,
    std::string filter_type
) {
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> out(time.size(), std::complex<float>(0, 0));
    
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_real_distribution<float> phase_dist(0.0, 2.0f * static_cast<float>(M_PI));
    
    int K = spike_count / 2;
    for (int k = -K; k <= K; ++k) {
        double freq = k * spike_spacing_hz;
        float phase_offset = phase_dist(gen);
        for (size_t i = 0; i < time.size(); ++i) {
            float phase = static_cast<float>(2.0 * M_PI * freq * time[i] + phase_offset);
            out[i] += std::exp(std::complex<float>(0, phase));
        }
    }
    
    applySpectralShaping(out, spike_spacing_hz * spike_count, sample_rate_hz, filter_type);
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<WaveformEngine::Technique> WaveformEngine::getTechniques() {
    std::vector<Technique> techs;

    auto add_universal = [](Technique& t) {
        t.parameters.push_back({"filter_type", "Filter Type", "options", "none", {"none", "rectangular", "rrc"}});
        t.parameters.push_back({"target_value", "Amplitude (0-1)", "entry", "1.0", {}});
        t.parameters.push_back({"normalization_type", "Norm Type", "options", "peak", {"peak", "rms"}});
    };

    // Narrowband Noise
    Technique nn = {"Narrowband Noise", {
        {"bandwidth_hz", "Bandwidth (Hz)", "entry", "100000", {}},
        {"technique_length_seconds", "Length (s)", "entry", "0.1", {}},
        {"interference_type", "Type", "options", "complex", {"complex", "real", "sinc"}}
    }};
    add_universal(nn);
    techs.push_back(nn);

    // Differential Comb
    Technique dc = {"Differential Comb", {
        {"spike_spacing_hz", "Spacing (Hz)", "entry", "30000", {}},
        {"spike_count", "Spike Count", "entry", "10", {}},
        {"technique_length_seconds", "Length (s)", "entry", "0.1", {}}
    }};
    add_universal(dc);
    techs.push_back(dc);

    // RRC Modulated Noise
    Technique rrc = {"RRC Modulated Noise", {
        {"symbol_rate_hz", "Symbol Rate (Hz)", "entry", "50000", {}},
        {"rolloff", "Rolloff", "entry", "0.35", {}},
        {"technique_length_seconds", "Length (s)", "entry", "0.1", {}}
    }};
    add_universal(rrc);
    techs.push_back(rrc);

    // Swept Noise
    Technique sn = {"Swept Noise", {
        {"sweep_hz", "Sweep Range (Hz)", "entry", "500000", {}},
        {"bandwidth_hz", "BW (Hz)", "entry", "50000", {}},
        {"technique_length_seconds", "Duration (s)", "entry", "0.1", {}},
        {"sweep_type", "Sweep Type", "options", "sawtooth", {"sawtooth", "triangle"}},
        {"sweep_rate_hz_s", "Sweep Rate (Hz/s)", "entry", "0", {}},
        {"interference_type", "Type", "options", "complex", {"complex", "real", "sinc"}}
    }};
    add_universal(sn);
    techs.push_back(sn);

    // Chunked Noise
    Technique cn = {"Chunked Noise", {
        {"technique_width_hz", "Width (Hz)", "entry", "1000000", {}},
        {"chunks", "Chunks", "entry", "10", {}},
        {"technique_length_seconds", "Length (s)", "entry", "0.1", {}},
        {"interference_type", "Type", "options", "complex", {"complex", "real", "sinc"}}
    }};
    add_universal(cn);
    techs.push_back(cn);

    // Noise Tones
    Technique nt = {"Noise Tones", {
        {"frequencies_str", "Freqs (Hz)", "entry", "-100000 0 100000", {}},
        {"bandwidth_hz", "BW (Hz)", "entry", "10000", {}},
        {"technique_length_seconds", "Length (s)", "entry", "0.1", {}},
        {"interference_type", "Type", "options", "complex", {"complex", "real", "sinc"}}
    }};
    add_universal(nt);
    techs.push_back(nt);

    // Cosine Tones
    Technique ct = {"Cosine Tones", {
        {"frequencies_str", "Freqs (Hz)", "entry", "10000 50000 100000", {}},
        {"technique_length_seconds", "Length (s)", "entry", "0.1", {}}
    }};
    add_universal(ct);
    techs.push_back(ct);

    // Phasor Tones
    Technique pt = {"Phasor Tones", {
        {"frequencies_str", "Freqs (Hz)", "entry", "10000 50000 100000", {}},
        {"technique_length_seconds", "Length (s)", "entry", "0.1", {}}
    }};
    add_universal(pt);
    techs.push_back(pt);

    // Swept Phasors
    Technique sph = {"Swept Phasors", {
        {"sweep_hz", "Sweep (Hz)", "entry", "500000", {}},
        {"tones", "Tones", "entry", "5", {}},
        {"technique_length_seconds", "Length (s)", "entry", "0.1", {}}
    }};
    add_universal(sph);
    techs.push_back(sph);

    // Swept Cosines
    Technique sc = {"Swept Cosines", {
        {"sweep_hz", "Sweep (Hz)", "entry", "500000", {}},
        {"tones", "Tones", "entry", "5", {}},
        {"technique_length_seconds", "Length (s)", "entry", "0.1", {}}
    }};
    add_universal(sc);
    techs.push_back(sc);

    // FM Cosine
    Technique fmc = {"FM Cosine", {
        {"sweep_range_hz", "Sweep (Hz)", "entry", "100000", {}},
        {"modulated_frequency", "Mod Freq (Hz)", "entry", "1000", {}},
        {"technique_length_seconds", "Length (s)", "entry", "0.1", {}}
    }};
    add_universal(fmc);
    techs.push_back(fmc);

    // LFM Chirp
    Technique lfm = {"LFM Chirp", {
        {"start_freq_hz", "Start (Hz)", "entry", "-500000", {}},
        {"end_freq_hz", "End (Hz)", "entry", "500000", {}},
        {"technique_length_seconds", "Length (s)", "entry", "0.1", {}}
    }};
    add_universal(lfm);
    techs.push_back(lfm);

    // FHSS Noise
    Technique fhss = {"FHSS Noise", {
        {"hop_frequencies_str", "Hops (Hz)", "entry", "-200000 0 200000", {}},
        {"hop_duration_seconds", "Duration (s)", "entry", "0.01", {}},
        {"bandwidth_hz", "BW (Hz)", "entry", "50000", {}},
        {"technique_length_seconds", "Length (s)", "entry", "0.1", {}},
        {"interference_type", "Type", "options", "complex", {"complex", "real", "sinc"}}
    }};
    add_universal(fhss);
    techs.push_back(fhss);

    // OFDM-Shaped Noise
    Technique ofdm = {"OFDM-Shaped Noise", {
        {"fft_size", "FFT Size", "entry", "64", {}},
        {"num_subcarriers", "Subcarriers", "entry", "48", {}},
        {"cp_length", "CP Length", "entry", "16", {}},
        {"technique_length_seconds", "Length (s)", "entry", "0.1", {}}
    }};
    add_universal(ofdm);
    techs.push_back(ofdm);

    // Song Maker
    Technique sm = {"Song Maker", {
        {"songName", "Song", "options", "Star Wars", {"Air Force Song", "Anchors Away", "Marine Hymn", "Army Song", "Baby Shark", "Star Wars", "Pink Panther", "Mission Impossible", "Annoying Tone"}},
        {"bandwidth_hz", "BW (Hz)", "entry", "100000", {}}
    }};
    add_universal(sm);
    techs.push_back(sm);

    // Correlator Confusion
    Technique ccf = {"Correlator Confusion", {
        {"bandwidth_hz", "Target BW (Hz)", "entry", "1000000", {}},
        {"pulse_interval_ms", "Pulse Gap (ms)", "entry", "10.0", {}},
        {"confusion_mode", "Mode", "options", "both", {"phase_flip", "timing_jitter", "both"}}
    }};
    add_universal(ccf);
    techs.push_back(ccf);

    return techs;
}

