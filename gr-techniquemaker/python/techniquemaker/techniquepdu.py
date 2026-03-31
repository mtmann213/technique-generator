#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 Abel Nunez.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#

import numpy as np
from gnuradio import gr
import pmt
import random
from scipy import signal
from . import BaseWaveforms

class techniquepdu(gr.sync_block):
    """
    GNU Radio block for reactive signal synthesis and protocol-aware interdiction.
    Supports multi-target tracking, adaptive bandwidth, preamble sabotage, Clock-Pull drift,
    and the Stability Frame 'Stutter' attack.
    """
    def __init__(self, technique='Narrowband Noise', 
                 sample_rate_hz=1e6, 
                 bandwidth_hz=100e3, 
                 technique_length_seconds=1.0,
                 interference_type='complex',
                 symbol_rate_hz=50e3,
                 rolloff=0.35,
                 sweep_hz=500e3,
                 sweep_type='sawtooth',
                 sweep_rate_hz_s=100e3,
                 technique_width_hz=1e6,
                 chunks=5,
                 frequencies_str='1000 2000 3000',
                 tones=5,
                 sweep_range_hz=1e6,
                 modulated_frequency=1e3,
                 song_name='Baby Shark',
                 start_freq_hz=-100e3,
                 end_freq_hz=100e3,
                 hop_frequencies_str='-100000 0 100000',
                 hop_duration_seconds=0.01,
                 fft_size=1024,
                 num_subcarriers=600,
                 cp_length=256,
                 target_value=1.0,
                 normalization_type='peak',
                 filter_type='none',
                 reactive_threshold_db=-40.0,
                 reactive_dwell_ms=100.0,
                 warhead_technique='Narrowband Noise',
                 num_targets=1,
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
                 enable_command_port=False,
                 output_mode='Continuous (Stream)'):
        
        gr.sync_block.__init__(self,
            name="techniquepdu",
            in_sig=[np.complex64] if technique == 'Reactive Jammer' else None,
            out_sig=[np.complex64])

        self.technique = technique
        self.sample_rate_hz = sample_rate_hz
        self.bandwidth_hz = bandwidth_hz
        self.technique_length_seconds = technique_length_seconds
        self.interference_type = interference_type
        self.symbol_rate_hz = symbol_rate_hz
        self.rolloff = rolloff
        self.sweep_hz = sweep_hz
        self.sweep_type = sweep_type
        self.sweep_rate_hz_s = sweep_rate_hz_s
        self.technique_width_hz = technique_width_hz
        self.chunks = chunks
        self.frequencies_str = frequencies_str
        self.tones = tones
        self.sweep_range_hz = sweep_range_hz
        self.modulated_frequency = modulated_frequency
        self.song_name = song_name
        self.start_freq_hz = start_freq_hz
        self.end_freq_hz = end_freq_hz
        self.hop_frequencies_str = hop_frequencies_str
        self.hop_duration_seconds = hop_duration_seconds
        self.fft_size = fft_size
        self.num_subcarriers = num_subcarriers
        self.cp_length = cp_length
        self.target_value = target_value
        self.normalization_type = normalization_type
        self.filter_type = filter_type
        self.reactive_threshold_db = reactive_threshold_db
        self.reactive_dwell_ms = reactive_dwell_ms
        self.warhead_technique = warhead_technique
        self.num_targets = int(num_targets)
        self.manual_mode = manual_mode
        self.manual_freq = manual_freq
        self.interdiction_enabled = jamming_enabled
        self.adaptive_bw = adaptive_bw
        self.preamble_sabotage = preamble_sabotage
        self.sabotage_duration_ms = sabotage_duration_ms
        self.clock_pull_drift_hz_s = clock_pull_drift_hz_s
        self.stutter_enabled = stutter_enabled
        self.stutter_clean_count = int(stutter_clean_count)
        self.stutter_burst_count = int(stutter_burst_count)
        self.stutter_randomize = bool(stutter_randomize)
        self.frame_duration_ms = frame_duration_ms
        self.enable_command_port = enable_command_port
        self.output_mode = output_mode
        self.predictive_tracking = False

        # Internal State
        self._phase = np.zeros(16)
        self._sweep_time = 0.0
        self._filter_coeffs = None
        self._filter_zi = None
        self._base_samples = None 
        self._base_ptr = 0
        self._need_regen = True
        self._target_freqs = np.zeros(16)
        self._dwell_counter = 0
        self._sabotage_counter = 0
        self._drift_time = 0.0 
        self._stutter_timer = 0.0
        self._current_cycle_clean = self.stutter_clean_count
        self._last_report_freqs = []

        self.message_port_register_in(pmt.intern("trigger"))
        self.message_port_register_in(pmt.intern("command"))
        self.message_port_register_out(pmt.intern("pdu"))
        self.message_port_register_out(pmt.intern("info"))
        self.set_msg_handler(pmt.intern("trigger"), self.handle_trigger)
        self.set_msg_handler(pmt.intern("command"), self.handle_command)

    def _setup_filter(self):
        nyquist = self.sample_rate_hz / 2
        cutoff = min(self.bandwidth_hz / 2 * 1.1, nyquist * 0.95)
        self._filter_coeffs = signal.firwin(101, cutoff, fs=self.sample_rate_hz)
        self._filter_zi = signal.lfilter_zi(self._filter_coeffs, 1.0) * 0j

    def _generate_base(self):
        try:
            actual_tech = self.warhead_technique if self.technique == 'Reactive Jammer' else self.technique
            wf_def = BaseWaveforms.waveform_definitions.get(actual_tech)
            if not wf_def: return np.array([0], dtype=np.complex64)
            params = {p['name']: getattr(self, p['name'], None) for p in wf_def['params']}
            if 'songName' in params: params['songName'] = self.song_name
            return np.asarray(wf_def['func'](**params), dtype=np.complex64)
        except Exception as e:
            print(f"[TechniquePDU] Synthesis Error: {e}")
            return np.array([0], dtype=np.complex64)

    def work(self, input_items, output_items):
        out = output_items[0]; n = len(out)
        if self.output_mode == 'Burst (PDU)': out[:] = 0; return n

        if self._need_regen:
            streaming_types = ['Swept Noise', 'Narrowband Noise']
            current_active = self.warhead_technique if self.technique == 'Reactive Jammer' else self.technique
            if current_active in streaming_types: self._setup_filter()
            else: self._base_samples = self._generate_base(); self._base_ptr = 0
            self._need_regen = False

        # --- 1. Detection Logic ---
        is_reactive = self.technique == 'Reactive Jammer'
        if is_reactive and not self.manual_mode and len(input_items) > 0:
            if self._dwell_counter <= 0:
                in0 = input_items[0]; fft_len = self.fft_size
                if len(in0) >= fft_len:
                    spectrum = np.fft.fft(in0[:fft_len])
                    psd = 20 * np.log10(np.abs(np.fft.fftshift(spectrum)) / fft_len + 1e-12)
                    temp_psd = psd.copy(); new_targets = []
                    freq_axis = np.linspace(-self.sample_rate_hz/2, self.sample_rate_hz/2, fft_len)
                    for _ in range(self.num_targets):
                        peak_idx = np.argmax(temp_psd); peak_val = temp_psd[peak_idx]
                        if peak_val > self.reactive_threshold_db:
                            target_f = freq_axis[peak_idx]; new_targets.append(target_f)
                            if self.adaptive_bw and _ == 0:
                                thresh_10db = peak_val - 10; left_idx = peak_idx
                                while left_idx > 0 and temp_psd[left_idx] > thresh_10db: left_idx -= 1
                                right_idx = peak_idx
                                while right_idx < fft_len - 1 and temp_psd[right_idx] > thresh_10db: right_idx += 1
                                measured_bw = (right_idx - left_idx) * (self.sample_rate_hz / fft_len)
                                if abs(measured_bw - self.bandwidth_hz) > 5000:
                                    self.bandwidth_hz = max(10000, min(measured_bw, self.sample_rate_hz/2))
                                    self._setup_filter()
                            start = max(0, peak_idx - 20); end = min(fft_len, peak_idx + 20); temp_psd[start:end] = -150
                        else: break
                    if new_targets:
                        self._target_freqs[:len(new_targets)] = new_targets
                        self._dwell_counter = int(self.reactive_dwell_ms * self.sample_rate_hz / 1000.0)
                        self._sabotage_counter = int(self.sabotage_duration_ms * self.sample_rate_hz / 1000.0)
                        self._drift_time = 0.0; self._stutter_timer = 0.0
                        # Randomize next clean count if enabled
                        if self.stutter_randomize:
                            self._current_cycle_clean = random.randint(1, max(1, self.stutter_clean_count))
                        else:
                            self._current_cycle_clean = self.stutter_clean_count
                        
                        if len(new_targets) != len(self._last_report_freqs):
                            self._last_report_freqs = new_targets

        # --- Predictive Tracking ---
        if self.predictive_tracking and self._last_report_freqs:
            # Shift predicted frequencies if no recent detection
            if self._dwell_counter <= 0:
                self._last_report_freqs = [f + 50000.0 for f in self._last_report_freqs]
                self._dwell_counter = n + 100 # Reset dwell for predicted hop

        if self.manual_mode: self._target_freqs[0] = self.manual_freq; self._dwell_counter = n + 100

        # --- 2. Protocol & Timing Gating ---
        if not self.interdiction_enabled or (is_reactive and self._dwell_counter <= 0):
            out[:] = 0; self._dwell_counter -= n; return n

        gate_open = True
        if is_reactive and self.preamble_sabotage:
            if self._sabotage_counter <= 0: gate_open = False
        
        elif is_reactive and self.stutter_enabled:
            frame_idx = int(self._stutter_timer * 1000.0 / self.frame_duration_ms)
            cycle_len = self._current_cycle_clean + self.stutter_burst_count
            rel_idx = frame_idx % cycle_len
            # Burst if we are in the last 'stutter_burst_count' frames of the cycle
            if rel_idx < self._current_cycle_clean: gate_open = False

        if not gate_open:
            out[:] = 0; self._dwell_counter -= n; self._stutter_timer += n / self.sample_rate_hz; return n

        # --- 3. Mixing & Synthesis ---
        current_active = self.warhead_technique if self.technique == 'Reactive Jammer' else self.technique
        use_realtime_noise = current_active in ['Swept Noise', 'Narrowband Noise']
        if use_realtime_noise:
            white = (np.random.randn(n) + 1j * np.random.randn(n)) / np.sqrt(2)
            source_samples, self._filter_zi = signal.lfilter(self._filter_coeffs, 1.0, white, zi=self._filter_zi)
        else:
            s_len = len(self._base_samples); indices = (np.arange(n) + self._base_ptr) % s_len
            source_samples = self._base_samples[indices]; self._base_ptr = (self._base_ptr + n) % s_len

        fs = self.sample_rate_hz
        is_swept = current_active in ['Swept Noise', 'Swept Phasors', 'Swept Cosines']
        t_output = self._sweep_time + np.arange(n) / fs
        t_drift = self._drift_time + np.arange(n) / fs
        freq_drift = self.clock_pull_drift_hz_s * t_drift
        
        hydra_out = np.zeros(n, dtype=np.complex128)
        active_target_count = self.num_targets if not self.manual_mode else 1
        if is_reactive and not self.manual_mode: active_target_count = min(active_target_count, len(self._last_report_freqs))

        for tid in range(max(1, active_target_count)):
            f_target = self._target_freqs[tid]
            if is_swept:
                f_span = self.sweep_hz; rate = self.sweep_rate_hz_s if self.sweep_rate_hz_s > 0 else (f_span / self.technique_length_seconds); period = f_span / rate if rate > 0 else 1.0
                f_inst = (2 * f_span / period) * np.abs((t_output % period) - period / 2) - (f_span / 2) if self.sweep_type == 'triangle' else (f_span / period) * (t_output % period) - (f_span / 2)
                phases = 2 * np.pi * np.cumsum(f_inst + f_target + freq_drift) / fs + self._phase[tid]
                hydra_out += source_samples * np.exp(1j * phases); self._phase[tid] = phases[-1] % (2 * np.pi)
            else:
                phases = 2 * np.pi * (f_target * t_drift + 0.5 * self.clock_pull_drift_hz_s * t_drift**2) + self._phase[tid]
                hydra_out += source_samples * np.exp(1j * phases)

        if active_target_count > 1: hydra_out /= np.sqrt(active_target_count)
        out[:] = hydra_out
        self._sweep_time += n / fs
        self._drift_time += n / fs
        self._stutter_timer += n / fs
        self._dwell_counter -= n
        self._sabotage_counter -= n
        return n

    def handle_command(self, msg):
        if not self.enable_command_port: return
        try:
            if not pmt.is_dict(msg): return
            keys = pmt.dict_keys(msg); 
            for i in range(pmt.length(keys)):
                k_p = pmt.vector_ref(keys, i); k = pmt.symbol_to_string(k_p)
                v_p = pmt.dict_ref(msg, k_p, pmt.PMT_NIL); s = f"set_{k}"
                if hasattr(self, s):
                    if pmt.is_bool(v_p): val = pmt.to_bool(v_p)
                    elif pmt.is_real(v_p) or pmt.is_integer(v_p): val = pmt.to_double(v_p)
                    else: val = pmt.symbol_to_string(v_p)
                    getattr(self, s)(val)
            self._need_regen = True
        except Exception as e: print(f"Error: {e}")

    def handle_trigger(self, msg):
        samples = self._generate_base(); meta = pmt.make_dict()
        meta = pmt.dict_add(meta, pmt.intern("sample_rate"), pmt.from_double(self.sample_rate_hz))
        self.message_port_pub(pmt.intern("pdu"), pmt.cons(meta, pmt.init_c32vector(len(samples), samples)))

    def set_technique(self, v): self.technique = v; self._need_regen = True
    def set_sample_rate_hz(self, v): self.sample_rate_hz = float(v); self._need_regen = True
    def set_bandwidth_hz(self, v): self.bandwidth_hz = float(v); self._need_regen = True
    def set_technique_length_seconds(self, v): self.technique_length_seconds = float(v); self._need_regen = True
    def set_interference_type(self, v): self.interference_type = str(v); self._need_regen = True
    def set_symbol_rate_hz(self, v): self.symbol_rate_hz = float(v); self._need_regen = True
    def set_rolloff(self, v): self.rolloff = float(v); self._need_regen = True
    def set_sweep_hz(self, v): self.sweep_hz = float(v); self._need_regen = True
    def set_sweep_type(self, v): self.sweep_type = str(v); self._need_regen = True
    def set_sweep_rate_hz_s(self, v): self.sweep_rate_hz_s = float(v); self._need_regen = True
    def set_technique_width_hz(self, v): self.technique_width_hz = float(v); self._need_regen = True
    def set_chunks(self, v): self.chunks = int(v); self._need_regen = True
    def set_frequencies_str(self, v): self.frequencies_str = str(v); self._need_regen = True
    def set_tones(self, v): self.tones = int(v); self._need_regen = True
    def set_sweep_range_hz(self, v): self.sweep_range_hz = float(v); self._need_regen = True
    def set_modulated_frequency(self, v): self.modulated_frequency = float(v); self._need_regen = True
    def set_song_name(self, v): self.song_name = str(v); self._need_regen = True
    def set_start_freq_hz(self, v): self.start_freq_hz = float(v); self._need_regen = True
    def set_end_freq_hz(self, v): self.end_freq_hz = float(v); self._need_regen = True
    def set_hop_frequencies_str(self, v): self.hop_frequencies_str = str(v); self._need_regen = True
    def set_hop_duration_seconds(self, v): self.hop_duration_seconds = float(v); self._need_regen = True
    def set_fft_size(self, v): self.fft_size = int(v); self._need_regen = True
    def set_num_subcarriers(self, v): self.num_subcarriers = int(v); self._need_regen = True
    def set_cp_length(self, v): self.cp_length = int(v); self._need_regen = True
    def set_target_value(self, v): self.target_value = float(v); self._need_regen = True
    def set_normalization_type(self, v): self.normalization_type = str(v); self._need_regen = True
    def set_filter_type(self, v): self.filter_type = str(v); self._need_regen = True
    def set_reactive_threshold_db(self, v): self.reactive_threshold_db = float(v)
    def set_reactive_dwell_ms(self, v): self.reactive_dwell_ms = float(v)
    def set_warhead_technique(self, v): self.warhead_technique = str(v); self._need_regen = True
    def set_num_targets(self, v): self.num_targets = int(v)
    def set_manual_mode(self, v): self.manual_mode = bool(v)
    def set_manual_freq(self, v): self.manual_freq = float(v)
    def set_jamming_enabled(self, v): self.interdiction_enabled = bool(v)
    def set_adaptive_bw(self, v): self.adaptive_bw = bool(v)
    def set_preamble_sabotage(self, v): self.preamble_sabotage = bool(v)
    def set_sabotage_duration_ms(self, v): self.sabotage_duration_ms = float(v)
    def set_clock_pull_drift_hz_s(self, v): self.clock_pull_drift_hz_s = float(v)
    def set_stutter_enabled(self, v): self.stutter_enabled = bool(v)
    def set_stutter_clean_count(self, v): self.stutter_clean_count = int(v)
    def set_stutter_burst_count(self, v): self.stutter_burst_count = int(v)
    def set_stutter_randomize(self, v): self.stutter_randomize = bool(v)
    def set_frame_duration_ms(self, v): self.frame_duration_ms = float(v)
    def set_enable_command_port(self, v): self.enable_command_port = bool(v)
    def set_output_mode(self, v): self.output_mode = str(v); self._need_regen = True
    def set_predictive_tracking(self, v): self.predictive_tracking = bool(v)
