#include "interdictor_cpp_impl.h"
#include <gnuradio/io_signature.h>
#include <gnuradio/fft/fft.h>
#include <random>
#include <cmath>
#include <iostream>
#include <algorithm>
#include <numeric>
#include <cstring>

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
      d_current_clean_limit(stutter_clean_count),
      d_fft_ptr(0),
      d_fft_size(1024),
      d_dwell_counter(0),
      d_sticky_denial(false),
      d_look_through_ms(10.0),
      d_jam_cycle_ms(90.0),
      d_is_looking(true),
      d_cycle_counter(0)
{
    d_fft_buffer.resize(d_fft_size, std::complex<float>(0, 0));
    d_look_samples = static_cast<uint64_t>(d_look_through_ms * d_sample_rate_hz / 1000.0);
    d_jam_samples = static_cast<uint64_t>(d_jam_cycle_ms * d_sample_rate_hz / 1000.0);
    update_waveform();
}

interdictor_cpp_impl::~interdictor_cpp_impl()
{
}

void normalize_signal_v3(std::vector<std::complex<float>>& wf, float target = 1.0f) {
    float max_abs = 0.0f;
    for (const auto& s : wf) {
        float a = std::abs(s);
        if (a > max_abs) max_abs = a;
    }
    if (max_abs > 0) {
        float scale = target / max_abs;
        for (auto& s : wf) s *= scale;
    }
}

void interdictor_cpp_impl::generate_cw_tone()
{
    d_base_waveform.assign(1024, std::complex<float>(1.0f, 0.0f));
}

void interdictor_cpp_impl::generate_narrowband_noise()
{
    int num_samples = static_cast<int>(d_sample_rate_hz * 0.1);
    d_base_waveform.resize(num_samples);
    std::random_device rd; std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0f, 1.0f);
    for (int i = 0; i < num_samples; ++i) d_base_waveform[i] = std::complex<float>(dist(gen), dist(gen));
    normalize_signal_v3(d_base_waveform);
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
    normalize_signal_v3(d_base_waveform);
}

void interdictor_cpp_impl::generate_cosine_tones()
{
    std::vector<double> freqs = {1000.0, 5000.0, 10000.0};
    int num_samples = static_cast<int>(d_sample_rate_hz * 0.1);
    d_base_waveform.assign(num_samples, std::complex<float>(0, 0));
    for (double f : freqs) {
        for (int i = 0; i < num_samples; ++i) {
            float val = cos(2.0f * M_PI * f * i / d_sample_rate_hz);
            d_base_waveform[i] += std::complex<float>(val, 0);
        }
    }
    normalize_signal_v3(d_base_waveform);
}

void interdictor_cpp_impl::generate_swept_noise()
{
    int num_samples = static_cast<int>(d_sample_rate_hz * 0.1);
    d_base_waveform.resize(num_samples);
    std::random_device rd; std::mt19937 gen(rd());
    std::normal_distribution<float> dist(0.0f, 1.0f);
    double sweep_hz = 500000.0;
    for (int i = 0; i < num_samples; ++i) {
        double t = static_cast<double>(i) / d_sample_rate_hz;
        double inst_freq = (sweep_hz / 0.1) * t - (sweep_hz / 2.0);
        float phase = 2.0f * M_PI * inst_freq * t;
        std::complex<float> noise(dist(gen), dist(gen));
        d_base_waveform[i] = noise * std::complex<float>(cos(phase), sin(phase));
    }
    normalize_signal_v3(d_base_waveform);
}

void interdictor_cpp_impl::generate_lfm_chirp()
{
    int num_samples = static_cast<int>(d_sample_rate_hz * 0.1);
    d_base_waveform.resize(num_samples);
    double f0 = -d_bandwidth_hz / 2.0;
    double f1 = d_bandwidth_hz / 2.0;
    double T = 0.1;
    for (int i = 0; i < num_samples; ++i) {
        double t = static_cast<double>(i) / d_sample_rate_hz;
        double phase = 2.0 * M_PI * (f0 * t + 0.5 * (f1 - f0) * t * t / T);
        d_base_waveform[i] = std::complex<float>(cos(phase), sin(phase));
    }
}

void interdictor_cpp_impl::generate_fm_cosine()
{
    int num_samples = static_cast<int>(d_sample_rate_hz * 0.1);
    d_base_waveform.resize(num_samples);
    double sweep_range = d_bandwidth_hz;
    double mod_freq = 1000.0;
    double cumulative_phase = 0.0;
    for (int i = 0; i < num_samples; ++i) {
        double t = static_cast<double>(i) / d_sample_rate_hz;
        double inst_freq_dev = 0.5 * sweep_range * cos(2.0 * M_PI * mod_freq * t);
        cumulative_phase += 2.0 * M_PI * inst_freq_dev / d_sample_rate_hz;
        d_base_waveform[i] = std::complex<float>(cos(cumulative_phase), sin(cumulative_phase));
    }
}

void interdictor_cpp_impl::generate_swept_phasors()
{
    int num_samples = static_cast<int>(d_sample_rate_hz * 0.1);
    d_base_waveform.assign(num_samples, std::complex<float>(0, 0));
    int tones = 5;
    double sweep_hz = d_bandwidth_hz;
    for (int k = 0; k < tones; ++k) {
        double f0 = -sweep_hz/2.0 + k*(sweep_hz/tones);
        double cumulative_phase = 0.0;
        for (int i = 0; i < num_samples; ++i) {
            double t = static_cast<double>(i) / d_sample_rate_hz;
            double inst_freq = (sweep_hz / tones / 0.1) * t + f0;
            cumulative_phase += 2.0 * M_PI * inst_freq / d_sample_rate_hz;
            d_base_waveform[i] += std::complex<float>(cos(cumulative_phase), sin(cumulative_phase));
        }
    }
    normalize_signal_v3(d_base_waveform);
}

void interdictor_cpp_impl::generate_swept_cosines()
{
    int num_samples = static_cast<int>(d_sample_rate_hz * 0.1);
    d_base_waveform.assign(num_samples, std::complex<float>(0, 0));
    int tones = 5;
    double sweep_hz = d_bandwidth_hz;
    for (int k = 0; k < tones; ++k) {
        double f0 = -sweep_hz/2.0 + k*(sweep_hz/tones);
        double cumulative_phase = 0.0;
        for (int i = 0; i < num_samples; ++i) {
            double t = static_cast<double>(i) / d_sample_rate_hz;
            double inst_freq = (sweep_hz / tones / 0.1) * t + f0;
            cumulative_phase += 2.0 * M_PI * inst_freq / d_sample_rate_hz;
            d_base_waveform[i] += std::complex<float>(cos(cumulative_phase), 0);
        }
    }
    normalize_signal_v3(d_base_waveform);
}

void interdictor_cpp_impl::generate_rrc_noise() { generate_narrowband_noise(); }
void interdictor_cpp_impl::generate_chunked_noise() { generate_narrowband_noise(); }
void interdictor_cpp_impl::generate_noise_tones() { generate_phasor_tones(); }
void interdictor_cpp_impl::generate_fhss_noise() { generate_narrowband_noise(); }
void interdictor_cpp_impl::generate_ofdm_noise() { generate_narrowband_noise(); }
void interdictor_cpp_impl::generate_correlator_confusion() { generate_cw_tone(); }
void interdictor_cpp_impl::generate_song() { generate_cosine_tones(); }

void interdictor_cpp_impl::generate_differential_comb()
{
    int num_samples = static_cast<int>(d_sample_rate_hz * 0.1);
    d_base_waveform.assign(num_samples, std::complex<float>(0, 0));
    double spacing = d_bandwidth_hz; 
    int count = d_num_targets > 0 ? d_num_targets : 10;
    std::random_device rd; std::mt19937 gen(rd()); std::uniform_real_distribution<float> dist(0.0f, 2.0f * M_PI);
    int K = count / 2;
    for (int k = -K; k <= K; ++k) {
        double freq = k * spacing; float phase_offset = dist(gen);
        for (int i = 0; i < num_samples; ++i) {
            float phase = 2.0f * M_PI * freq * i / d_sample_rate_hz + phase_offset;
            d_base_waveform[i] += std::complex<float>(cos(phase), sin(phase));
        }
    }
    normalize_signal_v3(d_base_waveform);
}

void interdictor_cpp_impl::perform_spectral_detection()
{
    if (d_fft_ptr < d_fft_size) return;

    gr::fft::fft<std::complex<float>, true> fft(d_fft_size);
    std::vector<std::complex<float>> out(d_fft_size);
    memcpy(fft.get_inbuf(), &d_fft_buffer[0], d_fft_size * sizeof(std::complex<float>));
    fft.execute();
    memcpy(&out[0], fft.get_outbuf(), d_fft_size * sizeof(std::complex<float>));

    if (!d_sticky_denial) d_tracked_targets.clear();
    
    bool in_island = false;
    int start_bin = 0;

    for (int i = 0; i < d_fft_size; i++) {
        float mag_sq = out[i].real()*out[i].real() + out[i].imag()*out[i].imag();
        float db = 10.0f * log10f(mag_sq / d_fft_size + 1e-12f);

        if (db > d_reactive_threshold_db) {
            if (!in_island) { in_island = true; start_bin = i; }
        } else {
            if (in_island) {
                in_island = false;
                int end_bin = i - 1;
                int center_bin = (start_bin + end_bin) / 2;
                if (center_bin > d_fft_size / 2) center_bin -= d_fft_size;
                double cf = (double)center_bin * d_sample_rate_hz / d_fft_size;
                double bw = (double)(end_bin - start_bin) * d_sample_rate_hz / d_fft_size;

                if (d_sticky_denial) {
                    bool exists = false;
                    for (const auto& existing : d_tracked_targets) {
                        if (std::abs(existing.center_freq - cf) < (bw/2)) { exists = true; break; }
                    }
                    if (!exists) d_tracked_targets.push_back({cf, bw, true, 0.0});
                } else {
                    d_tracked_targets.push_back({cf, bw, true, 0.0});
                }
                
                if (!d_sticky_denial && d_tracked_targets.size() >= (size_t)d_num_targets) break;
            }
        }
    }
    d_fft_ptr = 0;
}

void interdictor_cpp_impl::update_waveform()
{
    if (d_technique == "CW Tone (Pure)" || d_technique == "Direct CW") generate_cw_tone();
    else if (d_technique == "Phasor Tones") generate_phasor_tones();
    else if (d_technique == "Cosine Tones") generate_cosine_tones();
    else if (d_technique == "Swept Noise") generate_swept_noise();
    else if (d_technique == "LFM Chirp") generate_lfm_chirp();
    else if (d_technique == "FM Cosine") generate_fm_cosine();
    else if (d_technique == "Swept Phasors") generate_swept_phasors();
    else if (d_technique == "Swept Cosines") generate_swept_cosines();
    else if (d_technique == "Differential Comb") generate_differential_comb();
    else if (d_technique == "RRC Modulated Noise") generate_rrc_noise();
    else if (d_technique == "Chunked Noise") generate_chunked_noise();
    else if (d_technique == "Noise Tones") generate_noise_tones();
    else if (d_technique == "FHSS Noise") generate_fhss_noise();
    else if (d_technique == "OFDM-Shaped Noise") generate_ofdm_noise();
    else if (d_technique == "Correlator Confusion") generate_correlator_confusion();
    else if (d_technique == "Song Maker") generate_song();
    else generate_narrowband_noise();
    d_waveform_idx = 0;
}

// Setters
void interdictor_cpp_impl::set_technique(const std::string& technique) { d_technique = technique; update_waveform(); }
void interdictor_cpp_impl::set_sample_rate_hz(double sample_rate_hz) { d_sample_rate_hz = sample_rate_hz; d_look_samples = static_cast<uint64_t>(d_look_through_ms * d_sample_rate_hz / 1000.0); d_jam_samples = static_cast<uint64_t>(d_jam_cycle_ms * d_sample_rate_hz / 1000.0); update_waveform(); }
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
void interdictor_cpp_impl::set_sticky_denial(bool sticky) { d_sticky_denial = sticky; if (!sticky) d_tracked_targets.clear(); }
void interdictor_cpp_impl::set_look_through_ms(double ms) { d_look_through_ms = ms; d_look_samples = static_cast<uint64_t>(ms * d_sample_rate_hz / 1000.0); }
void interdictor_cpp_impl::set_jam_cycle_ms(double ms) { d_jam_cycle_ms = ms; d_jam_samples = static_cast<uint64_t>(ms * d_sample_rate_hz / 1000.0); }
void interdictor_cpp_impl::clear_persistent_targets() { d_tracked_targets.clear(); }

int interdictor_cpp_impl::work(int noutput_items,
                               gr_vector_const_void_star &input_items,
                               gr_vector_void_star &output_items)
{
    const gr_complex *in = (const gr_complex *) input_items[0];
    gr_complex *out = (gr_complex *) output_items[0];

    // 1. Look-through & Detection Logic
    for (int i = 0; i < noutput_items; i++) {
        d_cycle_counter++;
        if (d_is_looking) {
            if (d_fft_ptr < d_fft_size) d_fft_buffer[d_fft_ptr++] = in[i];
            if (d_cycle_counter >= d_look_samples) { d_is_looking = false; d_cycle_counter = 0; perform_spectral_detection(); }
        } else {
            if (d_cycle_counter >= d_jam_samples) { d_is_looking = true; d_cycle_counter = 0; }
        }
    }

    if (!d_jamming_enabled || d_is_looking) {
        std::fill(out, out + noutput_items, std::complex<float>(0, 0));
        return noutput_items;
    }

    // 2. Synthesis Logic
    int wf_len = d_base_waveform.size();
    if (wf_len == 0) { std::fill(out, out + noutput_items, std::complex<float>(0, 0)); return noutput_items; }

    std::fill(out, out + noutput_items, std::complex<float>(0, 0));
    if (d_output_mode == "Auto-Surgical") {
        // Multi-Target Matched-Bandwidth Surgical Summation
        std::fill(out, out + noutput_items, std::complex<float>(0, 0));
        double native_bw = d_bandwidth_hz > 0 ? d_bandwidth_hz : 100000.0;

        for (auto& target : d_tracked_targets) {
            if (!target.active) continue;
            double bw_ratio = target.bandwidth / native_bw;
            
            for (int i = 0; i < noutput_items; i++) {
                float phase = 2.0f * M_PI * target.center_freq * (d_total_samples_processed + i) / d_sample_rate_hz;
                
                // Linear Interpolation for Resampling
                double virtual_idx = target.resample_ptr;
                int idx_low = static_cast<int>(std::floor(virtual_idx)) % wf_len;
                int idx_high = (idx_low + 1) % wf_len;
                float frac = static_cast<float>(virtual_idx - std::floor(virtual_idx));
                
                std::complex<float> sample = d_base_waveform[idx_low] * (1.0f - frac) + d_base_waveform[idx_high] * frac;
                
                out[i] += sample * std::complex<float>(cos(phase), sin(phase));
                target.resample_ptr += bw_ratio;
                if (target.resample_ptr >= wf_len) target.resample_ptr -= wf_len;
            }
        }
        d_total_samples_processed += noutput_items;
    } else {
        double freq_offset = d_manual_mode ? d_manual_freq : 0.0;
        for (int i = 0; i < noutput_items; i++) {
            std::complex<float> base_sample = d_base_waveform[d_waveform_idx];
            d_waveform_idx = (d_waveform_idx + 1) % wf_len;
            if (freq_offset != 0.0) {
                float phase = 2.0f * M_PI * freq_offset * d_total_samples_processed / d_sample_rate_hz;
                out[i] = base_sample * std::complex<float>(cos(phase), sin(phase));
            } else out[i] = base_sample;
            d_total_samples_processed++;
        }
    }
    
    return noutput_items;
}

} // namespace techniquemaker
} // namespace gr
