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

void WaveformEngine::normalizeSignal(std::vector<std::complex<float>>& samples, float target_value, const std::string& normalization_type) {
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

void WaveformEngine::applySpectralShaping(std::vector<std::complex<float>>& samples, double bandwidth_hz, double sample_rate_hz, const std::string& filter_type, double rolloff) {
    (void)rolloff;
    if (samples.empty() || filter_type == "none") return;
    
    size_t n = samples.size();
    double fc = (bandwidth_hz / 2.0) / sample_rate_hz;
    int M = 64; // Filter order
    std::vector<float> h(M + 1);
    for (int i = 0; i <= M; ++i) {
        if (i == M/2) h[i] = 2.0f * (float)fc;
        else {
            float x = (float)M_PI * (i - M/2);
            h[i] = std::sin(2.0f * (float)fc * x) / x;
        }
        h[i] *= (0.54f - 0.46f * std::cos(2.0f * (float)M_PI * i / M));
    }

    std::vector<std::complex<float>> original = samples;
    for (size_t i = 0; i < n; ++i) {
        std::complex<float> sum(0, 0);
        for (int j = 0; j <= M; ++j) {
            if (i >= (size_t)j) {
                sum += original[i - j] * h[j];
            }
        }
        samples[i] = sum;
    }
}

void WaveformEngine::applyFrequencyShift(std::vector<std::complex<float>>& samples, double shift_hz, double sample_rate_hz) {
    if (shift_hz == 0 || samples.empty()) return;
    const double two_pi = 2.0 * M_PI;
    double phase_inc = two_pi * shift_hz / sample_rate_hz;
    double phase = 0.0;
    for (auto& s : samples) {
        std::complex<float> rotation(static_cast<float>(cos(phase)), static_cast<float>(sin(phase)));
        s *= rotation;
        phase = fmod(phase + phase_inc, two_pi);
    }
}

std::vector<std::complex<float>> WaveformEngine::correlatorConfusion(
    double bandwidth_hz,
    double sample_rate_hz,
    double technique_length_seconds,
    double pulse_interval_ms,
    const std::string& confusion_mode,
    float target_value,
    const std::string& normalization_type,
    const std::string& filter_type
) {
    size_t total_samples = static_cast<size_t>(std::floor(sample_rate_hz * technique_length_seconds));
    std::vector<std::complex<float>> out(total_samples, std::complex<float>(0, 0));
    
    int N_zc = 127;
    int root = 1;
    std::vector<std::complex<float>> zc(N_zc);
    for (int n = 0; n < N_zc; ++n) {
        float phase = - (float)M_PI * root * n * (n + 1) / N_zc;
        zc[n] = std::exp(std::complex<float>(0, phase));
    }

    size_t interval_samps = static_cast<size_t>(pulse_interval_ms * sample_rate_hz / 1000.0);
    size_t curr_ptr = 0;
    std::mt19937 gen(42);
    std::uniform_real_distribution<float> dist(0, 1);

    while (curr_ptr + N_zc < total_samples) {
        float p_scale = 1.0f;
        if (confusion_mode == "phase_flip" || confusion_mode == "both") {
            if (dist(gen) > 0.5f) p_scale = -1.0f;
        }
        for(int k=0; k<N_zc; ++k) out[curr_ptr + k] = zc[k] * p_scale;
        curr_ptr += interval_samps;
    }
    
    applySpectralShaping(out, bandwidth_hz, sample_rate_hz, filter_type);
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::narrowbandNoise(
    double bandwidth_hz,
    double sample_rate_hz,
    double technique_length_seconds,
    const std::string& interference_type,
    float target_value,
    const std::string& normalization_type,
    const std::string& filter_type
) {
    size_t total_samples = static_cast<size_t>(std::floor(sample_rate_hz * technique_length_seconds));
    std::vector<std::complex<float>> out(total_samples);
    std::mt19937 gen(123);
    std::normal_distribution<float> dist(0.0, 1.0);
    
    for (size_t i = 0; i < total_samples; ++i) {
        if (interference_type == "complex") out[i] = std::complex<float>(dist(gen), dist(gen));
        else out[i] = std::complex<float>(dist(gen), 0.0f);
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
    const std::string& normalization_type,
    const std::string& filter_type
) {
    (void)symbol_rate_hz; (void)rolloff; (void)filter_type;
    return narrowbandNoise(sample_rate_hz*0.5, sample_rate_hz, technique_length_seconds, "complex", target_value, normalization_type, "none");
}

std::vector<std::complex<float>> WaveformEngine::sweptNoise(
    double sweep_hz,
    double bandwidth_hz,
    double sample_rate_hz,
    double technique_length_seconds,
    const std::string& sweep_type,
    double sweep_rate_hz_s,
    const std::string& interference_type,
    float target_value,
    const std::string& normalization_type,
    const std::string& filter_type
) {
    double effective_duration = (sweep_rate_hz_s > 0) ? (sweep_hz / sweep_rate_hz_s) : technique_length_seconds;
    std::vector<std::complex<float>> noise = narrowbandNoise(bandwidth_hz, sample_rate_hz, technique_length_seconds, interference_type, 1.0f, "peak", filter_type);
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    for (size_t i = 0; i < time.size(); ++i) {
        double t_curr = fmod(time[i], effective_duration);
        double f = (sweep_type == "triangle") ? (2 * sweep_hz / effective_duration * std::abs(t_curr - effective_duration / 2) - sweep_hz / 2) : (sweep_hz / effective_duration * t_curr - sweep_hz / 2);
        noise[i] *= std::exp(std::complex<float>(0, (float)(2.0 * M_PI * f * time[i])));
    }
    normalizeSignal(noise, target_value, normalization_type);
    return noise;
}

std::vector<std::complex<float>> WaveformEngine::chunkedNoise(
    double technique_width_hz,
    int chunks,
    double sample_rate_hz,
    double technique_length_seconds,
    double sweep_rate_hz,
    const std::string& interference_type,
    float target_value,
    const std::string& normalization_type,
    const std::string& filter_type
) {
    (void)sweep_rate_hz;
    if (chunks <= 0) return {};
    double bw = technique_width_hz / chunks;
    std::vector<std::complex<float>> noise = narrowbandNoise(bw, sample_rate_hz, technique_length_seconds, interference_type, 1.0f, "peak", filter_type);
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    for (size_t i = 0; i < time.size(); ++i) {
        int chunk_idx = (int)(time[i] / technique_length_seconds * chunks) % chunks;
        double f = -technique_width_hz/2 + chunk_idx * bw + bw/2;
        noise[i] *= std::exp(std::complex<float>(0, (float)(2.0 * M_PI * f * time[i])));
    }
    normalizeSignal(noise, target_value, normalization_type);
    return noise;
}

std::vector<std::complex<float>> WaveformEngine::noiseTones(
    const std::string& frequencies_str,
    double bandwidth_hz,
    double sample_rate_hz,
    double technique_length_seconds,
    const std::string& interference_type,
    float target_value,
    const std::string& normalization_type,
    const std::string& filter_type
) {
    std::vector<double> freqs; std::stringstream ss(frequencies_str); double f; while (ss >> f) freqs.push_back(f);
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> base = narrowbandNoise(bandwidth_hz, sample_rate_hz, technique_length_seconds, interference_type, 1.0f, "peak", filter_type);
    std::vector<std::complex<float>> out(time.size(), std::complex<float>(0, 0));
    for (double freq : freqs) {
        for (size_t i = 0; i < time.size(); ++i) out[i] += base[i] * std::exp(std::complex<float>(0, (float)(2.0 * M_PI * freq * time[i])));
    }
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::cosineTones(
    const std::string& frequencies_str,
    double sample_rate_hz,
    double technique_length_seconds,
    float target_value,
    const std::string& normalization_type,
    const std::string& filter_type
) {
    (void)filter_type;
    std::vector<double> freqs; std::stringstream ss(frequencies_str); double f; while (ss >> f) freqs.push_back(f);
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> out(time.size(), std::complex<float>(0, 0));
    for (double freq : freqs) {
        for (size_t i = 0; i < time.size(); ++i) out[i] += std::complex<float>(std::cos((float)(2.0 * M_PI * freq * time[i])), 0.0f);
    }
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::phasorTones(
    const std::string& frequencies_str,
    double sample_rate_hz,
    double technique_length_seconds,
    float target_value,
    const std::string& normalization_type,
    const std::string& filter_type
) {
    (void)filter_type;
    std::vector<double> freqs; std::stringstream ss(frequencies_str); double f; while (ss >> f) freqs.push_back(f);
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> out(time.size(), std::complex<float>(0, 0));
    for (double freq : freqs) {
        for (size_t i = 0; i < time.size(); ++i) out[i] += std::exp(std::complex<float>(0, (float)(2.0 * M_PI * freq * time[i])));
    }
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::sweptPhasors(
    double sweep_hz,
    int tones,
    double sample_rate_hz,
    double technique_length_seconds,
    double sweep_rate_hz_s,
    float target_value,
    const std::string& normalization_type,
    const std::string& filter_type
) {
    (void)filter_type;
    if (tones <= 0) return {};
    double dur = (sweep_rate_hz_s > 0) ? (sweep_hz / sweep_rate_hz_s) : technique_length_seconds;
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> out(time.size(), std::complex<float>(0, 0));
    for (int k = 0; k < tones; ++k) {
        double f0 = -sweep_hz/2 + k * (sweep_hz/tones);
        for (size_t i = 0; i < time.size(); ++i) {
            double f = (sweep_hz / dur * fmod(time[i], dur)) + f0;
            out[i] += std::exp(std::complex<float>(0, (float)(2.0 * M_PI * f * time[i])));
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
    double sweep_rate_hz_s,
    float target_value,
    const std::string& normalization_type,
    const std::string& filter_type
) {
    (void)filter_type;
    if (tones <= 0) return {};
    double dur = (sweep_rate_hz_s > 0) ? (sweep_hz / sweep_rate_hz_s) : technique_length_seconds;
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> out(time.size(), std::complex<float>(0, 0));
    for (int k = 0; k < tones; ++k) {
        double f0 = -sweep_hz/2 + k * (sweep_hz/tones);
        for (size_t i = 0; i < time.size(); ++i) {
            double f = (sweep_hz / dur * fmod(time[i], dur)) + f0;
            out[i] += std::complex<float>(std::cos((float)(2.0 * M_PI * f * time[i])), 0.0f);
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
    const std::string& normalization_type,
    const std::string& filter_type
) {
    (void)filter_type;
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> out(time.size());
    for (size_t i = 0; i < time.size(); ++i) {
        float phase = (float)( (sweep_range_hz / modulated_frequency) * std::sin(2.0 * M_PI * modulated_frequency * time[i]) );
        out[i] = std::exp(std::complex<float>(0, phase));
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
    const std::string& normalization_type,
    const std::string& filter_type
) {
    (void)filter_type;
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> out(time.size());
    for (size_t i = 0; i < time.size(); ++i) {
        float phase = (float)( 2.0 * M_PI * (start_freq_hz * time[i] + 0.5 * (end_freq_hz - start_freq_hz) * std::pow(time[i], 2) / technique_length_seconds) );
        out[i] = std::exp(std::complex<float>(0, phase));
    }
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::fhssNoise(
    const std::string& hop_frequencies_str,
    double hop_duration_seconds,
    double bandwidth_hz,
    double sample_rate_hz,
    double technique_length_seconds,
    const std::string& interference_type,
    float target_value,
    const std::string& normalization_type,
    const std::string& filter_type
) {
    std::vector<double> freqs; std::stringstream ss(hop_frequencies_str); double f; while (ss >> f) freqs.push_back(f);
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> base = narrowbandNoise(bandwidth_hz, sample_rate_hz, technique_length_seconds, interference_type, 1.0f, "peak", filter_type);
    for (size_t i = 0; i < time.size(); ++i) {
        int hop_idx = (int)(time[i] / hop_duration_seconds) % freqs.size();
        base[i] *= std::exp(std::complex<float>(0, (float)(2.0 * M_PI * freqs[hop_idx] * time[i])));
    }
    normalizeSignal(base, target_value, normalization_type);
    return base;
}

std::vector<std::complex<float>> WaveformEngine::ofdmShapedNoise(
    int fft_size,
    int num_subcarriers,
    int cp_length,
    double sample_rate_hz,
    double technique_length_seconds,
    float target_value,
    const std::string& normalization_type,
    const std::string& filter_type
) {
    (void)fft_size; (void)num_subcarriers; (void)cp_length; (void)filter_type;
    return narrowbandNoise(sample_rate_hz * 0.4, sample_rate_hz, technique_length_seconds, "complex", target_value, normalization_type, "none");
}

std::vector<std::complex<float>> WaveformEngine::phaseShiftedNoise(
    double bandwidth_hz,
    double sample_rate_hz,
    double technique_length_seconds,
    double phase_shift_deg,
    double shift_rate_hz,
    float target_value,
    const std::string& normalization_type,
    const std::string& filter_type
) {
    std::vector<std::complex<float>> out = narrowbandNoise(bandwidth_hz, sample_rate_hz, technique_length_seconds, "complex", 1.0f, "peak", filter_type);
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    for (size_t i = 0; i < time.size(); ++i) {
        float shift = (std::sin((float)(2.0 * M_PI * shift_rate_hz * time[i])) > 0) ? (float)(phase_shift_deg * M_PI / 180.0) : 0.0f;
        out[i] *= std::exp(std::complex<float>(0, shift));
    }
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<std::complex<float>> WaveformEngine::songMaker(
    const std::string& songName,
    double bandwidth_hz,
    double sample_rate_hz,
    float target_value,
    const std::string& normalization_type,
    const std::string& filter_type
) {
    (void)songName; (void)bandwidth_hz; (void)filter_type;
    return narrowbandNoise(100000, sample_rate_hz, 1.0, "complex", target_value, normalization_type, "none");
}

std::vector<std::complex<float>> WaveformEngine::differentialComb(
    double spike_spacing_hz,
    int spike_count,
    double sample_rate_hz,
    double technique_length_seconds,
    float target_value,
    const std::string& normalization_type,
    const std::string& filter_type
) {
    (void)filter_type;
    std::vector<double> time = createTimeArray(sample_rate_hz, technique_length_seconds);
    std::vector<std::complex<float>> out(time.size(), std::complex<float>(0, 0));
    int K = spike_count / 2;
    for (int k = -K; k <= K; ++k) {
        double freq = k * spike_spacing_hz;
        for (size_t i = 0; i < time.size(); ++i) out[i] += std::exp(std::complex<float>(0, (float)(2.0 * M_PI * freq * time[i])));
    }
    normalizeSignal(out, target_value, normalization_type);
    return out;
}

std::vector<WaveformEngine::Technique> WaveformEngine::getTechniques() {
    return {}; // Placeholder
}
