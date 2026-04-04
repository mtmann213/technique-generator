#pragma once
#include <string>
#include <vector>
#include <map>
#include <complex>

namespace SoapySDR {

typedef std::map<std::string, std::string> Kwargs;
typedef std::vector<Kwargs> KwargsList;
class Stream;

enum Direction { SOAPY_SDR_TX = 0, SOAPY_SDR_RX = 1 };
const std::string SOAPY_SDR_CF32 = "CF32";
const int SOAPY_SDR_TIMEOUT = -1;

class Device {
public:
    static Device *make(const Kwargs &args = Kwargs());
    static Device *make(const std::string &args);
    static void unmake(Device *device);

    // --- VTABLE ALIGNMENT SECTION (DO NOT REORDER) ---
    virtual ~Device(void) {}
    virtual std::string getDriverKey(void) const = 0;
    virtual std::string getHardwareKey(void) const = 0;
    virtual Kwargs getHardwareInfo(void) const = 0;
    virtual void setFrontendMapping(const int, const std::string &) = 0;
    virtual std::string getFrontendMapping(const int) const = 0;
    virtual size_t getNumChannels(const int direction) const = 0;
    virtual Kwargs getChannelInfo(const int direction, const size_t channel) const = 0;
    virtual bool fullDuplex(const int, const size_t) const = 0;
    virtual std::vector<std::string> listAntennas(const int direction, const size_t channel) const = 0;
    virtual void setAntenna(const int direction, const size_t channel, const std::string &name) = 0;
    virtual std::string getAntenna(const int, const size_t) const = 0;
    virtual std::vector<std::string> listGains(const int, const size_t) const = 0;
    virtual void setGainMode(const int, const size_t, const bool) = 0;
    virtual bool getGainMode(const int, const size_t) const = 0;
    virtual void setGain(const int direction, const size_t channel, const double gain) = 0;
    virtual void setGain(const int, const size_t, const std::string &, const double) = 0;
    virtual double getGain(const int, const size_t) const = 0;
    virtual double getGain(const int, const size_t, const std::string &) const = 0;
    virtual void setFrequency(const int direction, const size_t channel, const double frequency, const Kwargs &args = Kwargs()) = 0;
    virtual void setFrequency(const int, const size_t, const std::string &, const double, const Kwargs &) = 0;
    virtual double getFrequency(const int, const size_t) const = 0;
    virtual double getFrequency(const int, const size_t, const std::string &) const = 0;
    virtual void setSampleRate(const int direction, const size_t channel, const double rate) = 0;
    virtual double getSampleRate(const int, const size_t) const = 0;
    virtual void setBandwidth(const int, const size_t, const double) = 0;
    virtual double getBandwidth(const int, const size_t) const = 0;
    
    virtual Stream *setupStream(const int direction, const std::string &format, const std::vector<size_t> &channels = std::vector<size_t>(), const Kwargs &args = Kwargs()) = 0;
    virtual void closeStream(Stream *stream) = 0;
    virtual size_t getStreamMTU(Stream *stream) const = 0;
    virtual int activateStream(Stream *stream, const int flags = 0, const long long timeNs = 0, const size_t numElems = 0) = 0;
    virtual int deactivateStream(Stream *stream, const int flags = 0, const long long timeNs = 0) = 0;
    virtual int readStream(Stream *, void * const *, const size_t, int &, long long &, const long) = 0;
    virtual int writeStream(Stream *stream, const void * const *buffs, const size_t numElems, int &flags, const long timeoutUs = 100000) = 0;
};

}

using SoapySDR::SOAPY_SDR_TX;
using SoapySDR::SOAPY_SDR_RX;
using SoapySDR::SOAPY_SDR_CF32;
using SoapySDR::SOAPY_SDR_TIMEOUT;
