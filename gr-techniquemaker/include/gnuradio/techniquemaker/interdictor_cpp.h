#ifndef INCLUDED_TECHNIQUEMAKER_INTERDICTOR_CPP_H
#define INCLUDED_TECHNIQUEMAKER_INTERDICTOR_CPP_H

#include <gnuradio/techniquemaker/api.h>
#include <gnuradio/sync_block.h>
#include <string>

namespace gr {
namespace techniquemaker {

class TECHNIQUEMAKER_API interdictor_cpp : virtual public gr::sync_block
{
public:
    typedef std::shared_ptr<interdictor_cpp> sptr;

    static sptr make(const std::string& technique,
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

    virtual void set_technique(const std::string& technique) = 0;
    virtual void set_sample_rate_hz(double sample_rate_hz) = 0;
    virtual void set_bandwidth_hz(double bandwidth_hz) = 0;
    virtual void set_reactive_threshold_db(double reactive_threshold_db) = 0;
    virtual void set_reactive_dwell_ms(double reactive_dwell_ms) = 0;
    virtual void set_num_targets(int num_targets) = 0;
    virtual void set_manual_mode(bool manual_mode) = 0;
    virtual void set_manual_freq(double manual_freq) = 0;
    virtual void set_jamming_enabled(bool jamming_enabled) = 0;
    virtual void set_adaptive_bw(bool adaptive_bw) = 0;
    virtual void set_preamble_sabotage(bool preamble_sabotage) = 0;
    virtual void set_sabotage_duration_ms(double sabotage_duration_ms) = 0;
    virtual void set_clock_pull_drift_hz_s(double clock_pull_drift_hz_s) = 0;
    virtual void set_stutter_enabled(bool stutter_enabled) = 0;
    virtual void set_stutter_clean_count(int stutter_clean_count) = 0;
    virtual void set_stutter_burst_count(int stutter_burst_count) = 0;
    virtual void set_stutter_randomize(bool stutter_randomize) = 0;
    virtual void set_frame_duration_ms(double frame_duration_ms) = 0;
    virtual void set_output_mode(const std::string& output_mode) = 0;
    virtual void set_sticky_denial(bool sticky) = 0;
    virtual void set_look_through_ms(double ms) = 0;
    virtual void set_jam_cycle_ms(double ms) = 0;
    virtual void clear_persistent_targets() = 0;
};

} // namespace techniquemaker
} // namespace gr

#endif /* INCLUDED_TECHNIQUEMAKER_INTERDICTOR_CPP_H */
