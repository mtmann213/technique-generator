#pragma once

#include <SoapySDR/Types.hpp>
#include <string>
#include <vector>
#include <complex>

namespace SoapySDR
{

class Stream;

class Device
{
public:
    virtual ~Device(void);

    static KwargsList enumerate(const Kwargs &args = Kwargs());
    static KwargsList enumerate(const std::string &args);
    static Device *make(const Kwargs &args = Kwargs());
    static Device *make(const std::string &args);
    static void unmake(Device *device);
    static std::vector<Device *> make(const KwargsList &argsList);
    static std::vector<Device *> make(const std::vector<std::string> &argsList);
    static void unmake(const std::vector<Device *> &devices);

    virtual std::string getDriverKey(void) const = 0;
    virtual std::string getHardwareKey(void) const = 0;
    virtual Kwargs getHardwareInfo(void) const = 0;

    virtual void setFrontendMapping(const int direction, const std::string &mapping) = 0;
    virtual std::string getFrontendMapping(const int direction) const = 0;
    virtual size_t getNumChannels(const int direction) const = 0;
    virtual Kwargs getChannelInfo(const int direction, const size_t channel) const = 0;
    virtual bool getFullDuplex(const int direction, const size_t channel) const = 0;

    virtual std::vector<std::string> getStreamFormats(const int direction, const size_t channel) const = 0;
    virtual std::string getNativeStreamFormat(const int direction, const size_t channel, double &fullScale) const = 0;
    virtual ArgInfoList getStreamArgsInfo(const int direction, const size_t channel) const = 0;
    virtual Stream *setupStream(const int direction, const std::string &format, const std::vector<size_t> &channels = std::vector<size_t>(), const Kwargs &args = Kwargs()) = 0;
    virtual void closeStream(Stream *stream) = 0;
    virtual size_t getStreamMTU(Stream *stream) const = 0;
    virtual int activateStream(Stream *stream, const int flags = 0, const long long timeNs = 0, const size_t numElems = 0) = 0;
    virtual int deactivateStream(Stream *stream, const int flags = 0, const long long timeNs = 0) = 0;
    virtual int readStream(Stream *stream, void * const *buffs, const size_t numElems, int &flags, long long &timeNs, const long timeoutUs = 100000) = 0;
    virtual int writeStream(Stream *stream, const void * const *buffs, const size_t numElems, int &flags, const long long timeNs = 0, const long timeoutUs = 100000) = 0;
    virtual int readStreamStatus(Stream *stream, size_t &chanMask, int &flags, long long &timeNs, const long timeoutUs = 100000) = 0;

    virtual size_t getNumDirectAccessBuffers(Stream *stream) = 0;
    virtual int getDirectAccessBufferAddrs(Stream *stream, const size_t handle, void **buffs) = 0;
    virtual int acquireReadBuffer(Stream *stream, size_t &handle, const void **buffs, int &flags, long long &timeNs, const long timeoutUs = 100000) = 0;
    virtual void releaseReadBuffer(Stream *stream, const size_t handle) = 0;
    virtual int acquireWriteBuffer(Stream *stream, size_t &handle, void **buffs, const long timeoutUs = 100000) = 0;
    virtual void releaseWriteBuffer(Stream *stream, const size_t handle, const size_t numElems, int &flags, const long long timeNs = 0) = 0;

    virtual std::vector<std::string> listAntennas(const int direction, const size_t channel) const = 0;
    virtual void setAntenna(const int direction, const size_t channel, const std::string &name) = 0;
    virtual std::string getAntenna(const int direction, const size_t channel) const = 0;

    virtual bool hasDCOffsetMode(const int direction, const size_t channel) const = 0;
    virtual void setDCOffsetMode(const int direction, const size_t channel, const bool automatic) = 0;
    virtual bool getDCOffsetMode(const int direction, const size_t channel) const = 0;
    virtual bool hasDCOffset(const int direction, const size_t channel) const = 0;
    virtual void setDCOffset(const int direction, const size_t channel, const std::complex<double> &offset) = 0;
    virtual std::complex<double> getDCOffset(const int direction, const size_t channel) const = 0;
    virtual bool hasIQBalance(const int direction, const size_t channel) const = 0;
    virtual void setIQBalance(const int direction, const size_t channel, const std::complex<double> &balance) = 0;
    virtual std::complex<double> getIQBalance(const int direction, const size_t channel) const = 0;
    virtual bool hasIQBalanceMode(const int direction, const size_t channel) const = 0;
    virtual void setIQBalanceMode(const int direction, const size_t channel, const bool automatic) = 0;
    virtual bool getIQBalanceMode(const int direction, const size_t channel) const = 0;
    virtual bool hasFrequencyCorrection(const int direction, const size_t channel) const = 0;
    virtual void setFrequencyCorrection(const int direction, const size_t channel, const double value) = 0;
    virtual double getFrequencyCorrection(const int direction, const size_t channel) const = 0;

    virtual std::vector<std::string> listGains(const int direction, const size_t channel) const = 0;
    virtual bool hasGainMode(const int direction, const size_t channel) const = 0;
    virtual void setGainMode(const int direction, const size_t channel, const bool automatic) = 0;
    virtual bool getGainMode(const int direction, const size_t channel) const = 0;
    virtual void setGain(const int direction, const size_t channel, const double value) = 0;
    virtual void setGain(const int direction, const size_t channel, const std::string &name, const double value) = 0;
    virtual double getGain(const int direction, const size_t channel) const = 0;
    virtual double getGain(const int direction, const size_t channel, const std::string &name) const = 0;
    virtual Range getGainRange(const int direction, const size_t channel) const = 0;
    virtual Range getGainRange(const int direction, const size_t channel, const std::string &name) const = 0;

    virtual void setFrequency(const int direction, const size_t channel, const double frequency, const Kwargs &args = Kwargs()) = 0;
    virtual void setFrequency(const int direction, const size_t channel, const std::string &name, const double frequency, const Kwargs &args = Kwargs()) = 0;
    virtual double getFrequency(const int direction, const size_t channel) const = 0;
    virtual double getFrequency(const int direction, const size_t channel, const std::string &name) const = 0;
    virtual std::vector<std::string> listFrequencies(const int direction, const size_t channel) const = 0;
    virtual RangeList getFrequencyRange(const int direction, const size_t channel) const = 0;
    virtual RangeList getFrequencyRange(const int direction, const size_t channel, const std::string &name) const = 0;
    virtual ArgInfoList getFrequencyArgsInfo(const int direction, const size_t channel) const = 0;

    virtual void setSampleRate(const int direction, const size_t channel, const double rate) = 0;
    virtual double getSampleRate(const int direction, const size_t channel) const = 0;
    virtual std::vector<double> listSampleRates(const int direction, const size_t channel) const = 0;
    virtual RangeList getSampleRateRange(const int direction, const size_t channel) const = 0;

    virtual void setBandwidth(const int direction, const size_t channel, const double bw) = 0;
    virtual double getBandwidth(const int direction, const size_t channel) const = 0;
    virtual std::vector<double> listBandwidths(const int direction, const size_t channel) const = 0;
    virtual RangeList getBandwidthRange(const int direction, const size_t channel) const = 0;

    virtual void setMasterClockRate(const double rate) = 0;
    virtual double getMasterClockRate(void) const = 0;
    virtual RangeList getMasterClockRates(void) const = 0;
    virtual void setReferenceClockRate(const double rate) = 0;
    virtual double getReferenceClockRate(void) const = 0;
    virtual RangeList getReferenceClockRates(void) const = 0;
    virtual std::vector<std::string> listClockSources(void) const = 0;
    virtual void setClockSource(const std::string &source) = 0;
    virtual std::string getClockSource(void) const = 0;

    virtual std::vector<std::string> listTimeSources(void) const = 0;
    virtual void setTimeSource(const std::string &source) = 0;
    virtual std::string getTimeSource(void) const = 0;
    virtual bool hasHardwareTime(const std::string &what = "") const = 0;
    virtual long long getHardwareTime(const std::string &what = "") const = 0;
    virtual void setHardwareTime(const long long timeNs, const std::string &what = "") = 0;
    virtual void setCommandTime(const long long timeNs, const std::string &what = "") = 0;

    virtual std::vector<std::string> listSensors(void) const = 0;
    virtual ArgInfo getSensorInfo(const std::string &key) const = 0;
    virtual std::string readSensor(const std::string &key) const = 0;
    virtual std::vector<std::string> listSensors(const int direction, const size_t channel) const = 0;
    virtual ArgInfo getSensorInfo(const int direction, const size_t channel, const std::string &key) const = 0;
    virtual std::string readSensor(const int direction, const size_t channel, const std::string &key) const = 0;

    virtual std::vector<std::string> listRegisterInterfaces(void) const = 0;
    virtual void writeRegister(const std::string &name, const unsigned addr, const unsigned value) = 0;
    virtual unsigned readRegister(const std::string &name, const unsigned addr) const = 0;
    virtual void writeRegister(const unsigned addr, const unsigned value) = 0;
    virtual unsigned readRegister(const unsigned addr) const = 0;
    virtual void writeRegisters(const std::string &name, const unsigned addr, const std::vector<unsigned> &value) = 0;
    virtual std::vector<unsigned> readRegisters(const std::string &name, const unsigned addr, const size_t length) const = 0;

    virtual ArgInfoList getSettingInfo(void) const = 0;
    virtual void writeSetting(const std::string &key, const std::string &value) = 0;
    virtual std::string readSetting(const std::string &key) const = 0;
    virtual ArgInfoList getSettingInfo(const int direction, const size_t channel) const = 0;
    virtual void writeSetting(const int direction, const size_t channel, const std::string &key, const std::string &value) = 0;
    virtual std::string readSetting(const int direction, const size_t channel, const std::string &key) const = 0;

    virtual std::vector<std::string> listGPIOBanks(void) const = 0;
    virtual void writeGPIO(const std::string &bank, const unsigned value) = 0;
    virtual void writeGPIO(const std::string &bank, const unsigned value, const unsigned mask) = 0;
    virtual unsigned readGPIO(const std::string &bank) const = 0;
    virtual void writeGPIODir(const std::string &bank, const unsigned dir) = 0;
    virtual void writeGPIODir(const std::string &bank, const unsigned dir, const unsigned mask) = 0;
    virtual unsigned readGPIODir(const std::string &bank) const = 0;

    virtual void writeI2C(const int addr, const std::string &data) = 0;
    virtual std::string readI2C(const int addr, const size_t numBytes) = 0;

    virtual unsigned transactSPI(const int addr, const unsigned data, const size_t numBits) = 0;

    virtual std::vector<std::string> listUARTs(void) const = 0;
    virtual void writeUART(const std::string &which, const std::string &data) = 0;
    virtual std::string readUART(const std::string &which, const long timeoutUs = 100000) const = 0;

    virtual void* getNativeDeviceHandle(void) const = 0;
};

}

using SoapySDR::SOAPY_SDR_TX;
using SoapySDR::SOAPY_SDR_RX;
using SoapySDR::SOAPY_SDR_CF32;
using SoapySDR::SOAPY_SDR_TIMEOUT;
