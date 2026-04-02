#ifndef WAVEFORM_ENGINE_H
#define WAVEFORM_ENGINE_H

#include <vector>
#include <complex>
#include <string>

#if defined(_WIN32)
    #if defined(WAVEFORM_ENGINE_EXPORT)
        #define WAVEFORM_ENGINE_API __declspec(dllexport)
    #else
        #define WAVEFORM_ENGINE_API __declspec(dllimport)
    #endif
#else
    #define WAVEFORM_ENGINE_API __attribute__((visibility("default")))
#endif

class WAVEFORM_ENGINE_API WaveformEngine {
public:
    struct Parameter {
        std::string name;
        std::string title;
        std::string type; // "entry" or "options"
        std::string default_val;
        std::vector<std::string> choices;
    };

    struct Technique {
        std::string name;
        std::vector<Parameter> parameters;
    };

    static std::vector<Technique> getTechniques();

    static std::vector<std::complex<float>> generateNarrowbandNoise(double sample_rate, double bw, double duration = 0.1);

    static std::vector<std::complex<float>> correlatorConfusion(
        double bandwidth_hz,
        double sample_rate_hz,
        double technique_length_seconds,
        double pulse_interval_ms = 10.0,
        std::string confusion_mode = "both",
        float target_value = 1.0,
        std::string normalization_type = "peak",
        std::string filter_type = "none"
    );

    static std::vector<std::complex<float>> narrowbandNoise(
        double bandwidth_hz,
        double sample_rate_hz,
        double technique_length_seconds,
        std::string interference_type = "complex",
        float target_value = 1.0,
        std::string normalization_type = "peak",
        std::string filter_type = "none"
    );

    static std::vector<std::complex<float>> rrcModulatedNoise(
        double symbol_rate_hz,
        double sample_rate_hz,
        double rolloff,
        double technique_length_seconds,
        float target_value = 1.0,
        std::string normalization_type = "peak",
        std::string filter_type = "none"
    );

    static std::vector<std::complex<float>> sweptNoise(
        double sweep_hz,
        double bandwidth_hz,
        double sample_rate_hz,
        double technique_length_seconds,
        std::string sweep_type = "sawtooth",
        double sweep_rate_hz_s = 0,
        std::string interference_type = "complex",
        float target_value = 1.0,
        std::string normalization_type = "peak",
        std::string filter_type = "none"
    );

    static std::vector<std::complex<float>> chunkedNoise(
        double technique_width_hz,
        int chunks,
        double sample_rate_hz,
        double technique_length_seconds,
        std::string interference_type = "complex",
        float target_value = 1.0,
        std::string normalization_type = "peak",
        std::string filter_type = "none"
    );

    static std::vector<std::complex<float>> noiseTones(
        std::string frequencies_str,
        double bandwidth_hz,
        double sample_rate_hz,
        double technique_length_seconds,
        std::string interference_type = "complex",
        float target_value = 1.0,
        std::string normalization_type = "peak",
        std::string filter_type = "none"
    );

    static std::vector<std::complex<float>> cosineTones(
        std::string frequencies_str,
        double sample_rate_hz,
        double technique_length_seconds,
        float target_value = 1.0,
        std::string normalization_type = "peak",
        std::string filter_type = "none"
    );

    static std::vector<std::complex<float>> phasorTones(
        std::string frequencies_str,
        double sample_rate_hz,
        double technique_length_seconds,
        float target_value = 1.0,
        std::string normalization_type = "peak",
        std::string filter_type = "none"
    );

    static std::vector<std::complex<float>> sweptPhasors(
        double sweep_hz,
        int tones,
        double sample_rate_hz,
        double technique_length_seconds,
        double sweep_rate_hz_s = 0,
        float target_value = 1.0,
        std::string normalization_type = "peak",
        std::string filter_type = "none"
    );

    static std::vector<std::complex<float>> sweptCosines(
        double sweep_hz,
        int tones,
        double sample_rate_hz,
        double technique_length_seconds,
        double sweep_rate_hz_s = 0,
        float target_value = 1.0,
        std::string normalization_type = "peak",
        std::string filter_type = "none"
    );

    static std::vector<std::complex<float>> fmCosine(
        double sweep_range_hz,
        double modulated_frequency,
        double sample_rate_hz,
        double technique_length_seconds,
        float target_value = 1.0,
        std::string normalization_type = "peak",
        std::string filter_type = "none"
    );

    static std::vector<std::complex<float>> lfmChirp(
        double start_freq_hz,
        double end_freq_hz,
        double sample_rate_hz,
        double technique_length_seconds,
        float target_value = 1.0,
        std::string normalization_type = "peak",
        std::string filter_type = "none"
    );

    static std::vector<std::complex<float>> fhssNoise(
        std::string hop_frequencies_str,
        double hop_duration_seconds,
        double bandwidth_hz,
        double sample_rate_hz,
        double technique_length_seconds,
        std::string interference_type = "complex",
        float target_value = 1.0,
        std::string normalization_type = "peak",
        std::string filter_type = "none"
    );

    static std::vector<std::complex<float>> ofdmShapedNoise(
        int fft_size,
        int num_subcarriers,
        int cp_length,
        double sample_rate_hz,
        double technique_length_seconds,
        float target_value = 1.0,
        std::string normalization_type = "peak",
        std::string filter_type = "none"
    );

    static std::vector<std::complex<float>> songMaker(
        std::string songName,
        double bandwidth_hz,
        double sample_rate_hz,
        float target_value = 1.0,
        std::string normalization_type = "peak",
        std::string filter_type = "none"
    );

    static std::vector<std::complex<float>> differentialComb(
        double spike_spacing_hz,
        int spike_count,
        double sample_rate_hz,
        double technique_length_seconds,
        float target_value = 1.0,
        std::string normalization_type = "peak",
        std::string filter_type = "none"
    );

private:
    static std::vector<double> rootRaisedCosineFilter(double symbol_rate_hz, double sample_rate_hz, double rolloff, int num_taps);
    static std::vector<double> createTimeArray(double sample_rate_hz, double technique_length_seconds);
    static void normalizeSignal(std::vector<std::complex<float>>& samples, float target_value, std::string normalization_type);
    static void applySpectralShaping(std::vector<std::complex<float>>& samples, double bandwidth_hz, double sample_rate_hz, std::string filter_type, double rolloff = 0.35);
};

#endif // WAVEFORM_ENGINE_H
