#ifndef INTERDICTION_CONTROLLER_H
#define INTERDICTION_CONTROLLER_H

#include <QObject>
#include <QTimer>
#include <gnuradio/top_block.h>
#include <gnuradio/uhd/usrp_source.h>
#include <gnuradio/uhd/usrp_sink.h>
#include <gnuradio/qtgui/waterfall_sink_c.h>
#include <gnuradio/techniquemaker/interdictor_cpp.h>
#include <gnuradio/analog/sig_source.h>
#include <gnuradio/blocks/add_blk.h>
#include <gnuradio/analog/noise_source.h>
#include <complex>
#include <vector>

using namespace gr::techniquemaker;

class InterdictionController : public QObject {
    Q_OBJECT
public:
    explicit InterdictionController(QObject *parent = nullptr);
    ~InterdictionController();

    void setup(const std::string& serial, double sample_rate, double center_freq);
    static std::vector<std::string> discoverDevices();
    void start();
    void stop();
    
    // Control API
    void setFreq(double freq);
    void setSampleRate(double rate);
    void setRxGain(double gain);
    void setTxGain(double gain);
    void setThreshold(double db);
    void setOutputMode(const std::string& mode);
    void setMaxTargets(int count);
    void setPreambleSabotage(bool enabled);
    void setSabotageDuration(double ms);
    void setJammingEnabled(bool enabled);
    void setStickyDenial(bool enabled);
    void setLookThroughMs(double ms);
    void setJamCycleMs(double ms);
    void setPredictiveTracking(bool enabled);
    void clearTargets();
    void setBaseWaveform(const std::vector<std::complex<float>>& wf);

    QWidget* getWaterfallWidget();

signals:
    void targetsUpdated(const std::vector<interdictor_cpp::Target>& targets);

private slots:
    void pollTelemetry();
    void onSimHop();

private:
    gr::top_block_sptr d_tb;
    gr::uhd::usrp_source::sptr d_src;
    gr::uhd::usrp_sink::sptr d_sink;
    gr::analog::sig_source<std::complex<float>>::sptr d_sim_src;
    gr::qtgui::waterfall_sink_c::sptr d_waterfall;
    interdictor_cpp::sptr d_interdictor;

    QTimer *d_telemetry_timer;
    QTimer *d_sim_timer;
    double d_sample_rate;
    double d_center_freq;
    bool d_sim_mode;
};

#endif // INTERDICTION_CONTROLLER_H
