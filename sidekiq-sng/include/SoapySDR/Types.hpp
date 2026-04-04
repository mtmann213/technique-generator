#pragma once

#include <string>
#include <vector>
#include <map>

namespace SoapySDR {

    typedef std::map<std::string, std::string> Kwargs;
    typedef std::vector<Kwargs> KwargsList;
    
    class Stream;

    struct Range {
        double minimum;
        double maximum;
        double step;
        Range(double minimum=0.0, double maximum=0.0, double step=0.0) : minimum(minimum), maximum(maximum), step(step) {}
    };
    typedef std::vector<Range> RangeList;

    struct ArgInfo {
        std::string key;
        std::string value;
        std::string name;
        std::string description;
        std::string units;
        int type;
        Range range;
        std::vector<std::string> options;
        std::vector<std::string> optionNames;
    };
    typedef std::vector<ArgInfo> ArgInfoList;

    enum Direction {
        SOAPY_SDR_TX = 0,
        SOAPY_SDR_RX = 1
    };

    const std::string SOAPY_SDR_CF32 = "CF32";
    const int SOAPY_SDR_TIMEOUT = -1;
    const int SOAPY_SDR_ALL_OR_NOTHING = (1 << 0);

}
