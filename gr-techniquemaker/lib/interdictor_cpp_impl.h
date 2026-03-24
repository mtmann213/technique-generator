#ifndef INCLUDED_TECHNIQUEMAKER_INTERDICTOR_CPP_IMPL_H
#define INCLUDED_TECHNIQUEMAKER_INTERDICTOR_CPP_IMPL_H

#include <gnuradio/techniquemaker/interdictor_cpp.h>
#include <vector>
#include <complex>

namespace gr {
namespace techniquemaker {

class interdictor_cpp_impl : public interdictor_cpp
{
private:
    std::string d_technique;
    double d_sample_rate_hz;
    double d_bandwidth_hz;
    double d_reactive_threshold_db;
    double d_reactive_dwell_ms;
    int d_num_targets;
    bool d_manual_mode;
    double d_manual_freq;
    bool d_jamming_enabled;
    bool d_adaptive_bw;
    bool d_preamble_sabotage;
    double d_sabotage_duration_ms;
    double d_clock_pull_drift_hz_s;
    bool d_stutter_enabled;
    int d_stutter_clean_count;
    int d_stutter_burst_count;
    bool d_stutter_randomize;
    double d_frame_duration_ms;
    std::string d_output_mode;

    // Internal state for waveform generation
    std::vector<std::complex<float>> d_base_waveform;
    int d_waveform_idx;
    uint64_t d_total_samples_processed;
    double d_current_clock_pull_phase;
    int d_stutter_state; // 0=clean, 1=burst
    int d_stutter_counter;
    int d_current_clean_limit;
    
    // Hydra Tracking State
    struct Target {
        double center_freq;
        double bandwidth;
        bool active;
        double resample_ptr;
    };
    std::vector<Target> d_tracked_targets;
    std::vector<std::complex<float>> d_fft_buffer;
    int d_fft_ptr;
    int d_fft_size;
    std::vector<float> d_fft_window;
    int d_dwell_counter;

    // Sticky Denial & Look-through
    bool d_sticky_denial;
    double d_look_through_ms;
    double d_jam_cycle_ms;
    bool d_is_looking;
    uint64_t d_look_samples;
    uint64_t d_jam_samples;
    uint64_t d_guard_samples;
    uint64_t d_cycle_counter;
    std::vector<Target> d_persistent_targets;

    // Core Waveform Generators
    void generate_cw_tone();
    void generate_narrowband_noise();
    void generate_phasor_tones();
    void generate_swept_noise();
    void generate_rrc_noise();
    void generate_chunked_noise();
    void generate_noise_tones();
    void generate_cosine_tones();
    void generate_swept_phasors();
    void generate_swept_cosines();
    void generate_fm_cosine();
    void generate_lfm_chirp();
    void generate_fhss_noise();
    void generate_ofdm_noise();
    void generate_correlator_confusion();
    void generate_song();
    void generate_differential_comb();
    void perform_spectral_detection();
    void update_waveform();

public:
    interdictor_cpp_impl(const std::string& technique,
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
                         const std::string& output_mode);

    ~interdictor_cpp_impl();

    // Setters
    void set_technique(const std::string& technique) override;
    void set_sample_rate_hz(double sample_rate_hz) override;
    void set_bandwidth_hz(double bandwidth_hz) override;
    void set_reactive_threshold_db(double reactive_threshold_db) override;
    void set_reactive_dwell_ms(double reactive_dwell_ms) override;
    void set_num_targets(int num_targets) override;
    void set_manual_mode(bool manual_mode) override;
    void set_manual_freq(double manual_freq) override;
    void set_jamming_enabled(bool jamming_enabled) override;
    void set_adaptive_bw(bool adaptive_bw) override;
    void set_preamble_sabotage(bool preamble_sabotage) override;
    void set_sabotage_duration_ms(double sabotage_duration_ms) override;
    void set_clock_pull_drift_hz_s(double clock_pull_drift_hz_s) override;
    void set_stutter_enabled(bool stutter_enabled) override;
    void set_stutter_clean_count(int stutter_clean_count) override;
    void set_stutter_burst_count(int stutter_burst_count) override;
    void set_stutter_randomize(bool stutter_randomize) override;
    void set_frame_duration_ms(double frame_duration_ms) override;
    void set_output_mode(const std::string& output_mode) override;
    void set_sticky_denial(bool sticky) override;
    void set_look_through_ms(double ms) override;
    void set_jam_cycle_ms(double ms) override;
    void clear_persistent_targets() override;
    void set_base_waveform(const std::vector<std::complex<float>>& waveform) override;

    int work(int noutput_items,
             gr_vector_const_void_star &input_items,
             gr_vector_void_star &output_items) override;
};

} // namespace techniquemaker
} // namespace gr

#endif /* INCLUDED_TECHNIQUEMAKER_INTERDICTOR_CPP_IMPL_H */
