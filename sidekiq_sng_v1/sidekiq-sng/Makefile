CXX = g++
CXXFLAGS = -O3 -march=native -std=c++17 -I./include
LIBS = -lSoapySDR

all: sng

sng: main.cpp WaveformEngine.cpp
	$(CXX) $(CXXFLAGS) -o sng main.cpp WaveformEngine.cpp

# Run 'make soapy' if you have SoapySDR installed on the target machine
soapy: main.cpp WaveformEngine.cpp
	$(CXX) $(CXXFLAGS) -DUSE_SOAPY -o sng main.cpp WaveformEngine.cpp $(LIBS)

clean:
	rm -f sng technique.bin
