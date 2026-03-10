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
from . import BaseWaveforms

class techniquepdu(gr.sync_block):
    """
    GNU Radio block that generates a signal technique and outputs it as a PDU.
    """
    def __init__(self, technique='Narrowband Noise', 
                 sample_rate_hz=1e6, 
                 bandwidth_hz=100e3, 
                 technique_length_seconds=0.1,
                 interference_type='complex',
                 symbol_rate_hz=50e3,
                 rolloff=0.35,
                 sweep_hz=500e3,
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
                 normalization_type='peak'):
        
        gr.sync_block.__init__(self,
            name="techniquepdu",
            in_sig=None,
            out_sig=None)

        self.technique = technique
        self.sample_rate_hz = sample_rate_hz
        self.bandwidth_hz = bandwidth_hz
        self.technique_length_seconds = technique_length_seconds
        self.interference_type = interference_type
        self.symbol_rate_hz = symbol_rate_hz
        self.rolloff = rolloff
        self.sweep_hz = sweep_hz
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

        # Message ports
        self.message_port_register_in(pmt.intern("trigger"))
        self.message_port_register_out(pmt.intern("pdu"))
        self.set_msg_handler(pmt.intern("trigger"), self.handle_trigger)

    def handle_trigger(self, msg):
        try:
            if self.technique not in BaseWaveforms.waveform_definitions:
                return

            wf_def = BaseWaveforms.waveform_definitions[self.technique]
            func = wf_def['func']
            
            params = {}
            for param_def in wf_def['params']:
                name = param_def['name']
                # Mapping GUI attributes to function arguments
                val = getattr(self, name, None)
                if val is not None:
                    params[name] = val
                
                # Special cases for non-matching names
                if name == 'songName': params[name] = self.song_name
                if name == 'technique_length_seconds':
                    params[name] = self.technique_length_seconds

            samples = func(**params)
            samples = np.asarray(samples, dtype=np.complex64)

            meta = pmt.make_dict()
            meta = pmt.dict_add(meta, pmt.intern("sample_rate"), pmt.from_double(self.sample_rate_hz))
            meta = pmt.dict_add(meta, pmt.intern("target_value"), pmt.from_double(self.target_value))
            meta = pmt.dict_add(meta, pmt.intern("normalization_type"), pmt.intern(self.normalization_type))
            
            samples_pmt = pmt.init_c32vector(len(samples), samples)
            pdu = pmt.cons(meta, samples_pmt)
            self.message_port_pub(pmt.intern("pdu"), pdu)

        except Exception as e:
            print(f"Error in techniquepdu trigger: {e}")

    # Setters for GRC
    def set_technique(self, technique): self.technique = technique
    def set_sample_rate_hz(self, v): self.sample_rate_hz = v
    def set_bandwidth_hz(self, v): self.bandwidth_hz = v
    def set_technique_length_seconds(self, v): self.technique_length_seconds = v
    def set_interference_type(self, v): self.interference_type = v
    def set_symbol_rate_hz(self, v): self.symbol_rate_hz = v
    def set_rolloff(self, v): self.rolloff = v
    def set_sweep_hz(self, v): self.sweep_hz = v
    def set_technique_width_hz(self, v): self.technique_width_hz = v
    def set_chunks(self, v): self.chunks = int(v)
    def set_frequencies_str(self, v): self.frequencies_str = v
    def set_tones(self, v): self.tones = int(v)
    def set_sweep_range_hz(self, v): self.sweep_range_hz = v
    def set_modulated_frequency(self, v): self.modulated_frequency = v
    def set_song_name(self, v): self.song_name = v
    def set_start_freq_hz(self, v): self.start_freq_hz = v
    def set_end_freq_hz(self, v): self.end_freq_hz = v
    def set_hop_frequencies_str(self, v): self.hop_frequencies_str = v
    def set_hop_duration_seconds(self, v): self.hop_duration_seconds = v
    def set_fft_size(self, v): self.fft_size = int(v)
    def set_num_subcarriers(self, v): self.num_subcarriers = int(v)
    def set_cp_length(self, v): self.cp_length = int(v)
    def set_target_value(self, v): self.target_value = float(v)
    def set_normalization_type(self, v): self.normalization_type = v
