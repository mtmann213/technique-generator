#ifndef TACTICAL_LOGGER_H
#define TACTICAL_LOGGER_H

#include <string>
#include <fstream>
#include <mutex>
#include <iostream>
#include <chrono>
#include <iomanip>

class TacticalLogger {
public:
    static TacticalLogger& instance() {
        static TacticalLogger _instance;
        return _instance;
    }

    void log(const std::string& level, const std::string& message) {
        std::lock_guard<std::mutex> lock(d_mutex);
        
        auto now = std::chrono::system_clock::now();
        auto in_time_t = std::chrono::system_clock::to_time_t(now);
        
        std::stringstream ss;
        ss << std::put_time(std::localtime(&in_time_t), "%Y-%m-%d %H:%M:%S") << " [" << level << "] " << message;
        std::string entry = ss.str();

        // Write to file
        if (d_file.is_open()) {
            d_file << entry << std::endl;
        }

        // Print to console for debug
        std::cout << entry << std::endl;
    }

private:
    TacticalLogger() {
        d_file.open("techniquemaker_native.log", std::ios::app);
    }
    
    ~TacticalLogger() {
        if (d_file.is_open()) d_file.close();
    }

    std::ofstream d_file;
    std::mutex d_mutex;
};

// Macros for easy access
#define LOG_INFO(msg) TacticalLogger::instance().log("INFO", msg)
#define LOG_WARN(msg) TacticalLogger::instance().log("WARN", msg)
#define LOG_TACTICAL(msg) TacticalLogger::instance().log("TACTICAL", msg)

#endif // TACTICAL_LOGGER_H
