import sys
import os

def setup_env():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    oot_python_path = os.path.join(current_dir, "gr-techniquemaker", "python")
    
    # 1. Add standard gnuradio install paths to the VERY FRONT of sys.path
    system_paths = [
        "/usr/local/lib/python3.12/dist-packages",
        "/usr/local/lib/python3.12/site-packages",
        "/usr/local/lib/python3/dist-packages"
    ]
    for p in reversed(system_paths):
        if p not in sys.path:
            sys.path.insert(0, p)
            
    # 2. Add local path to the END of sys.path as a fallback
    if oot_python_path not in sys.path:
        sys.path.append(oot_python_path)
    
    # 3. Setup subprocess environment
    env = os.environ.copy()
    existing_pp = env.get("PYTHONPATH", "")
    
    # Build new PYTHONPATH: System Paths -> Existing -> Local Path
    sys_pp_str = os.pathsep.join(system_paths)
    if existing_pp:
        env["PYTHONPATH"] = f"{sys_pp_str}{os.pathsep}{existing_pp}{os.pathsep}{oot_python_path}"
    else:
        env["PYTHONPATH"] = f"{sys_pp_str}{os.pathsep}{oot_python_path}"
    
    return env

env = setup_env()

import time
from gnuradio import gr, blocks, analog
from gnuradio.techniquemaker import interdictor_cpp

class TestFlowgraph(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)
        self.samp_rate = 2000000
        # Create a hopping signal
        self.src = analog.sig_source_c(self.samp_rate, analog.GR_COS_WAVE, 100000, 1.0, 0)
        
        # Interdictor in Sticky mode
        self.interdictor = interdictor_cpp(
            technique='Direct CW',
            sample_rate_hz=self.samp_rate,
            bandwidth_hz=10000,
            reactive_threshold_db=-45.0,
            reactive_dwell_ms=400.0,
            num_targets=10,
            manual_mode=False,
            manual_freq=0.0,
            jamming_enabled=True,
            adaptive_bw=False,
            preamble_sabotage=False,
            sabotage_duration_ms=20.0,
            clock_pull_drift_hz_s=0.0,
            stutter_enabled=False,
            stutter_clean_count=3,
            stutter_burst_count=1,
            stutter_randomize=False,
            frame_duration_ms=40.0,
            output_mode='Auto-Surgical'
        )
        self.interdictor.set_sticky_denial(True)
        self.interdictor.set_look_through_ms(10.0)
        self.interdictor.set_jam_cycle_ms(90.0)
        self.interdictor.set_base_waveform([complex(1,0)])
        
        self.sink = blocks.null_sink(gr.sizeof_gr_complex)
        self.connect(self.src, self.interdictor, self.sink)

if __name__ == '__main__':
    tb = TestFlowgraph()
    tb.start()
    print("Testing 100kHz tone...")
    time.sleep(1)
    print("Switching to 200kHz tone...")
    tb.src.set_frequency(200000)
    time.sleep(1)
    tb.stop()
    tb.wait()
