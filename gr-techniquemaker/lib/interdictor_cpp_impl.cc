#include "interdictor_cpp_impl.h"
#include <gnuradio/io_signature.h>
#include <random>
#include <cmath>
#include <iostream>
#include <algorithm>

namespace gr {
namespace techniquemaker {

interdictor_cpp::sptr
interdictor_cpp::make(const std::string& technique,
                      double sample_rate_hz,
                      double bandwidth_hz,
                      double reactive_threshold_db,
                      double reactive_dwell_ms,
                      int num_targets,
                      bool manual_mode,
                      double manual_freq,
                      bool jamming_enabled,
                      bool adaptive_bw,
                      bool preamble_sabotage,
                      double sabotage_duration_ms,
                      double clock_pull_drift_hz_s,
                      bool stutter_enabled,
                      int stutter_clean_count,
                      int stutter_burst_count,
                      bool stutter_randomize,
                      double frame_duration_ms,
                      const std::string& output_mode)
{
    return gnuradio::make_block_sptr<interdictor_cpp_impl>(
        technique, sample_rate_hz, bandwidth_hz, reactive_threshold_db,
        reactive_dwell_ms, num_targets, manual_mode, manual_freq,
        jamming_enabled, adaptive_bw, preamble_sabotage, sabotage_duration_ms,
        clock_pull_drift_hz_s, stutter_enabled, stutter_clean_count,
        stutter_burst_count, stutter_randomize, frame_duration_ms, output_mode);
}

interdictor_cpp_impl::interdictor_cpp_impl(const std::string& technique,
                                           double sample_rate_hz,
                                           double bandwidth_hz,
                                           double reactive_threshold_db,
                                           double reactive_dwell_ms,
                                           int num_targets,
                                           bool manual_mode,
                                           double manual_freq,
                                           bool jamming_enabled,
                                           bool adaptive_bw,
                                           bool preamble_sabotage,
                                           double sabotage_duration_ms,
                                           double clock_pull_drift_hz_s,
                                           bool stutter_enabled,
                                           int stutter_clean_count,
                                           int stutter_burst_count,
                                           bool stutter_randomize,
                                           double frame_duration_ms,
                                           const std::string& output_mode)
    : gr::sync_block("interdictor_cpp",
                     gr::io_signature::make(1, 1, sizeof(gr_complex)),
                     gr::io_signature::make(1, 1, sizeof(gr_complex))),
      d_technique(technique),
      d_sample_rate_hz(sample_rate_hz),
      d_bandwidth_hz(bandwidth_hz),
      d_reactive_threshold_db(reactive_threshold_db),
      d_reactive_dwell_ms(reactive_dwell_ms),
      d_num_targets(num_targets),
      d_manual_mode(manual_mode),
      d_manual_freq(manual_freq),
      d_jamming_enabled(jamming_enabled),
      d_adaptive_bw(adaptive_bw),
      d_preamble_sabotage(preamble_sabotage),
      d_sabotage_duration_ms(sabotage_duration_ms),
      d_clock_pull_drift_hz_s(clock_pull_drift_hz_s),
      d_stutter_enabled(stutter_enabled),
      d_stutter_clean_count(stutter_clean_count),
      d_stutter_burst_count(stutter_burst_count),
      d_stutter_randomize(stutter_randomize),
      d_frame_duration_ms(frame_duration_ms),
      d_output_mode(output_mode),
      d_waveform_idx(0),
      d_total_samples_processed(0),
      d_current_clock_pull_phase(0.0),
      d_stutter_state(0),
      d_stutter_counter(0),
      d_current_clean_limit(stutter_clean_count)
{
    update_waveform();
}

interdictor_cpp_impl::~interdictor_cpp_impl()
{
}

void interdictor_cpp_impl::generate_cw_tone()
{
    d_base_waveform.assign(1024, std::complex<float>(1.0f, 0.0f));
}

void interdictor_cpp_impl::generate_narrowband_noise()
{
    int num_samples = static_cast<int>(d_sample_rate_hz * 0.1);
    if (num_samples < 1024) num_samples = 1024;
    d_base_waveform.resize(num_samples);
    
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0f, 1.0f);
    
    for (int i = 0; i < num_samples; ++i) {
        d_base_waveform[i] = std::complex<float>(dist(gen), dist(gen));
    }
}

void interdictor_cpp_impl::generate_phasor_tones()
{
    std::vector<double> freqs = {1000.0, 5000.0, 10000.0};
    int num_samples = static_cast<int>(d_sample_rate_hz * 0.1);
    d_base_waveform.assign(num_samples, std::complex<float>(0, 0));
    
    for (double f : freqs) {
        for (int i = 0; i < num_samples; ++i) {
            float phase = 2.0f * M_PI * f * i / d_sample_rate_hz;
            d_base_waveform[i] += std::complex<float>(cos(phase), sin(phase));
        }
    }
}

void interdictor_cpp_impl::generate_swept_noise()
{
    int num_samples = static_cast<int>(d_sample_rate_hz * 0.1);
    d_base_waveform.resize(num_samples);
    
    std::random_device rd;
    std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0f, 1.0f);
    
    double sweep_hz = 500000.0;
    for (int i = 0; i < num_samples; ++i) {
        double t = static_cast<double>(i) / d_sample_rate_hz;
        double inst_freq = (sweep_hz / 0.1) * t - (sweep_hz / 2.0);
        float phase = 2.0f * M_PI * inst_freq * t;
        std::complex<float> noise(dist(gen), dist(gen));
        d_base_waveform[i] = noise * std::complex<float>(cos(phase), sin(phase));
    }
}

void interdictor_cpp_impl::update_waveform()
{
    if (d_technique == "CW Tone (Pure)" || d_technique == "Direct CW") {
        generate_cw_tone();
    } else if (d_technique == "Phasor Tones") {
        generate_phasor_tones();
    } else if (d_technique == "Swept Noise") {
        generate_swept_noise();
    } else {
        generate_narrowband_noise();
    }
    d_waveform_idx = 0;
}

// Setters
void interdictor_cpp_impl::set_technique(const std::string& technique) { d_technique = technique; update_waveform(); }
void interdictor_cpp_impl::set_sample_rate_hz(double sample_rate_hz) { d_sample_rate_hz = sample_rate_hz; update_waveform(); }
void interdictor_cpp_impl::set_bandwidth_hz(double bandwidth_hz) { d_bandwidth_hz = bandwidth_hz; }
void interdictor_cpp_impl::set_reactive_threshold_db(double reactive_threshold_db) { d_reactive_threshold_db = reactive_threshold_db; }
void interdictor_cpp_impl::set_reactive_dwell_ms(double reactive_dwell_ms) { d_reactive_dwell_ms = reactive_dwell_ms; }
void interdictor_cpp_impl::set_num_targets(int num_targets) { d_num_targets = num_targets; }
void interdictor_cpp_impl::set_manual_mode(bool manual_mode) { d_manual_mode = manual_mode; }
void interdictor_cpp_impl::set_manual_freq(double manual_freq) { d_manual_freq = manual_freq; }
void interdictor_cpp_impl::set_jamming_enabled(bool jamming_enabled) { d_jamming_enabled = jamming_enabled; }
void interdictor_cpp_impl::set_adaptive_bw(bool adaptive_bw) { d_adaptive_bw = adaptive_bw; }
void interdictor_cpp_impl::set_preamble_sabotage(bool preamble_sabotage) { d_preamble_sabotage = preamble_sabotage; }
void interdictor_cpp_impl::set_sabotage_duration_ms(double sabotage_duration_ms) { d_sabotage_duration_ms = sabotage_duration_ms; }
void interdictor_cpp_impl::set_clock_pull_drift_hz_s(double clock_pull_drift_hz_s) { d_clock_pull_drift_hz_s = clock_pull_drift_hz_s; }
void interdictor_cpp_impl::set_stutter_enabled(bool stutter_enabled) { d_stutter_enabled = stutter_enabled; }
void interdictor_cpp_impl::set_stutter_clean_count(int stutter_clean_count) { d_stutter_clean_count = stutter_clean_count; }
void interdictor_cpp_impl::set_stutter_burst_count(int stutter_burst_count) { d_stutter_burst_count = stutter_burst_count; }
void interdictor_cpp_impl::set_stutter_randomize(bool stutter_randomize) { d_stutter_randomize = stutter_randomize; }
void interdictor_cpp_impl::set_frame_duration_ms(double frame_duration_ms) { d_frame_duration_ms = frame_duration_ms; }
void interdictor_cpp_impl::set_output_mode(const std::string& output_mode) { d_output_mode = output_mode; }

int interdictor_cpp_impl::work(int noutput_items,
                               gr_vector_const_void_star &input_items,
                               gr_vector_void_star &output_items)
{
    // Unused input for now
    (void)input_items;
    gr_complex *out = (gr_complex *) output_items[0];

    if (!d_jamming_enabled) {
        std::fill(out, out + noutput_items, std::complex<float>(0, 0));
        return noutput_items;
    }

    int wf_len = d_base_waveform.size();
    if (wf_len == 0) {
        std::fill(out, out + noutput_items, std::complex<float>(0, 0));
        return noutput_items;
    }

    double freq_offset = d_manual_mode ? d_manual_freq : 0.0;
    
    for (int i = 0; i < noutput_items; i++) {
        std::complex<float> base_sample = d_base_waveform[d_waveform_idx];
        d_waveform_idx = (d_waveform_idx + 1) % wf_len;
        
        if (freq_offset != 0.0) {
            float phase = 2.0f * M_PI * freq_offset * d_total_samples_processed / d_sample_rate_hz;
            out[i] = base_sample * std::complex<float>(cos(phase), sin(phase));
        } else {
            out[i] = base_sample;
        }
        d_total_samples_processed++;
    }
    
    return noutput_items;
}

} // namespace techniquemaker
} // namespace gr
