#include "InterdictionController.hpp"
#include <gnuradio/techniquemaker/interdictor_cpp.h>
#include "../../gr-techniquemaker/lib/interdictor_cpp_impl.h"
#include <gnuradio/blocks/add_blk.h>
#include <gnuradio/io_signature.h>
#include <uhd/device.hpp>
#include <uhd/types/device_addr.hpp>
#include <QtGlobal>
#include <QWidget>

InterdictionController::InterdictionController(QObject *parent) 
    : QObject(parent), d_tb(gr::make_top_block("PredatorNative")), d_telemetry_timer(new QTimer(this)), 
      d_sim_timer(new QTimer(this)), d_sim_mode(false) {
    connect(d_telemetry_timer, &QTimer::timeout, this, &InterdictionController::pollTelemetry);
    connect(d_sim_timer, &QTimer::timeout, this, &InterdictionController::onSimHop);
}

InterdictionController::~InterdictionController() {
    stop();
}

void InterdictionController::setup(const std::string& serial, double sample_rate, double center_freq) {
    d_sample_rate = sample_rate;
    d_center_freq = center_freq;
    d_tb = gr::make_top_block("PredatorNative"); // Re-create TB on setup

    gr::basic_block_sptr final_source;

    // 1. Source
    if (!serial.empty() && serial != "Virtual") {
        d_src = gr::uhd::usrp_source::make(std::string("serial=") + serial, uhd::stream_args_t("fc32"));
        d_src->set_samp_rate(d_sample_rate);
        d_src->set_center_freq(d_center_freq);
        final_source = d_src;
        d_sim_mode = false;
        d_sim_timer->stop();
    } else {
        // Simulated Source
        auto noise = gr::analog::noise_source_c::make(gr::analog::GR_GAUSSIAN, 0.001);
        d_sim_src = gr::analog::sig_source<std::complex<float>>::make(d_sample_rate, gr::analog::GR_COS_WAVE, 0, 0.5);
        auto mixer = gr::blocks::add_blk<gr_complex>::make();
        d_tb->connect(noise, 0, mixer, 0);
        d_tb->connect(d_sim_src, 0, mixer, 1);
        final_source = mixer;
        d_sim_mode = true;
        d_sim_timer->start(500); // 500ms dwell
    }

    // 2. Interdictor (C++)
    d_interdictor = gnuradio::make_block_sptr<interdictor_cpp_impl>(
        "Direct CW", d_sample_rate, 100e3, -45.0, 400.0, 1, false, 0.0, true, false, false, 20.0, 0.0, false, 3, 1, false, 40.0, "Auto-Surgical"
    );

    // 3. Sink
    if (!d_sim_mode) {
        d_sink = gr::uhd::usrp_sink::make(std::string("serial=") + serial, uhd::stream_args_t("fc32"));
        d_sink->set_samp_rate(d_sample_rate);
        d_sink->set_center_freq(d_center_freq);
    }

    // 4. Visualization
    d_waterfall = gr::qtgui::waterfall_sink_c::make(1024, 1, d_center_freq, d_sample_rate, "Tactical Spectrum", 1);
    d_waterfall->set_intensity_range(-120, 20);

    // 5. Connections
    d_tb->connect(final_source, 0, d_interdictor, 0);
    
    if (!d_sim_mode && d_sink) {
        d_tb->connect(d_interdictor, 0, d_sink, 0);
    }

    // Display Mixer (Source + Jammer)
    auto disp_mixer = gr::blocks::add_blk<gr_complex>::make();
    d_tb->connect(final_source, 0, disp_mixer, 0);
    d_tb->connect(d_interdictor, 0, disp_mixer, 1);
    d_tb->connect(disp_mixer, 0, d_waterfall, 0);

    d_telemetry_timer->start(100);
}

void InterdictionController::onSimHop() {
    if (d_sim_mode && d_sim_src) {
        // Random hop between -400k and +400k
        static std::vector<double> offsets = {-400e3, -200e3, 0, 200e3, 400e3};
        static int last_idx = 0;
        int next_idx = rand() % offsets.size();
        while(next_idx == last_idx) next_idx = rand() % offsets.size();
        last_idx = next_idx;
        d_sim_src->set_frequency(offsets[next_idx]);
    }
}

std::vector<std::string> InterdictionController::discoverDevices() {
    std::vector<std::string> results;
    uhd::device_addrs_t device_addrs = uhd::device::find(uhd::device_addr_t(""));
    for (const auto& addr : device_addrs) {
        std::string label = addr.get("serial", "N/A");
        if (addr.has_key("product")) label += " (" + addr.get("product") + ")";
        results.push_back(label);
    }
    return results;
}

void InterdictionController::start() {
    if (d_tb) d_tb->start();
}

void InterdictionController::stop() {
    if (d_tb) {
        d_tb->stop();
        d_tb->wait();
    }
}

QWidget* InterdictionController::getWaterfallWidget() {
    if (d_waterfall) {
        return d_waterfall->qwidget();
    }
    return nullptr;
}

void InterdictionController::pollTelemetry() {
    if (d_interdictor) {
        auto targets = d_interdictor->get_targets();
        emit targetsUpdated(targets);
    }
}

// Control Methods
void InterdictionController::setFreq(double freq) {
    if (d_src) d_src->set_center_freq(freq);
    if (d_sink) d_sink->set_center_freq(freq);
    if (d_waterfall) d_waterfall->set_frequency_range(freq, d_sample_rate);
}

void InterdictionController::setSampleRate(double rate) {
    d_sample_rate = rate;
    if (d_src) d_src->set_samp_rate(rate);
    if (d_sink) d_sink->set_samp_rate(rate);
    if (d_interdictor) d_interdictor->set_sample_rate_hz(rate);
    if (d_waterfall) d_waterfall->set_frequency_range(d_center_freq, rate);
}

void InterdictionController::setRxGain(double gain) { if (d_src) d_src->set_gain(gain); }
void InterdictionController::setTxGain(double gain) { if (d_sink) d_sink->set_gain(gain); }
void InterdictionController::setThreshold(double db) { if (d_interdictor) d_interdictor->set_reactive_threshold_db(db); }
void InterdictionController::setOutputMode(const std::string& mode) { if (d_interdictor) d_interdictor->set_output_mode(mode); }
void InterdictionController::setMaxTargets(int count) { if (d_interdictor) d_interdictor->set_num_targets(count); }
void InterdictionController::setPreambleSabotage(bool enabled) { if (d_interdictor) d_interdictor->set_preamble_sabotage(enabled); }
void InterdictionController::setSabotageDuration(double ms) { if (d_interdictor) d_interdictor->set_sabotage_duration_ms(ms); }
void InterdictionController::setJammingEnabled(bool enabled) { if (d_interdictor) d_interdictor->set_jamming_enabled(enabled); }
void InterdictionController::setStickyDenial(bool enabled) { if (d_interdictor) d_interdictor->set_sticky_denial(enabled); }
void InterdictionController::setLookThroughMs(double ms) { if (d_interdictor) d_interdictor->set_look_through_ms(ms); }
void InterdictionController::setJamCycleMs(double ms) { if (d_interdictor) d_interdictor->set_jam_cycle_ms(ms); }
void InterdictionController::setPredictiveTracking(bool enabled) { if (d_interdictor) d_interdictor->set_predictive_tracking(enabled); }
void InterdictionController::clearTargets() { if (d_interdictor) d_interdictor->clear_persistent_targets(); }
void InterdictionController::setBaseWaveform(const std::vector<std::complex<float>>& wf) { if (d_interdictor) d_interdictor->set_base_waveform(wf); }
