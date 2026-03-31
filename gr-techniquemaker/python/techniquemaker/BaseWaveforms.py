import numpy as np
from scipy import signal
import math
import random
from numpy.typing import NDArray
from typing import Literal

def _root_raised_cosine_filter(
    symbol_rate_hz: float,
    sample_rate_hz: float,
    rolloff: float,
    num_taps: int
) -> NDArray[np.float64]:
    if num_taps % 2 == 0:
        raise ValueError("num_taps must be an odd number for a symmetric RRC filter.")
    Ts = 1.0 / symbol_rate_hz
    t = np.arange(-(num_taps // 2), num_taps // 2 + 1) / sample_rate_hz
    h = np.zeros(num_taps, dtype=np.float64)
    for i, ti in enumerate(t):
        ti_norm = ti / Ts
        if np.isclose(ti, 0):
            h[i] = (1 / Ts) * (1 - rolloff + (4 * rolloff / np.pi))
        elif np.isclose(abs(ti_norm), 1.0 / (4 * rolloff)):
            h[i] = (rolloff / (np.sqrt(2) * Ts)) * (
                (1 + 2 / np.pi) * np.sin(np.pi / (4 * rolloff)) +
                (1 - 2 / np.pi) * np.cos(np.pi / (4 * rolloff))
            )
        else:
            numerator = np.sin(np.pi * ti_norm * (1 - rolloff)) + \
                        4 * rolloff * ti_norm * np.cos(np.pi * ti_norm * (1 + rolloff))
            denominator = np.pi * ti_norm * (1 - (4 * rolloff * ti_norm)**2)
            h[i] = (1 / Ts) * (numerator / denominator)
    if np.sum(h**2) > 1e-9:
        h = h / np.sqrt(np.sum(h**2))
    return h

def _create_time_array(sample_rate_hz: float, technique_length_seconds: float) -> NDArray[np.float64]:
    num_samples = math.floor(sample_rate_hz * technique_length_seconds)
    if num_samples <= 0:
        raise ValueError("Calculated number of samples is zero or negative.")
    return np.linspace(0, technique_length_seconds - technique_length_seconds / num_samples, num_samples, dtype=np.float64)

def _normalize_signal(
    samples: NDArray,
    target_value: float = 1.0,
    normalization_type: Literal["peak", "rms"] = "peak"
) -> NDArray:
    if target_value <= 0: return samples
    if normalization_type == "peak":
        max_val = np.max(np.abs(samples))
        if max_val > 0: return samples * (target_value / max_val)
    elif normalization_type == "rms":
        rms_val = np.sqrt(np.mean(np.abs(samples)**2))
        if rms_val > 0: return samples * (target_value / rms_val)
    return samples

def _apply_spectral_shaping(
    samples: NDArray,
    bandwidth_hz: float,
    sample_rate_hz: float,
    filter_type: Literal["none", "rectangular", "rrc"] = "none",
    rolloff: float = 0.35
) -> NDArray:
    if filter_type == "none": return samples
    nyquist = sample_rate_hz / 2
    cutoff = min(bandwidth_hz / 2 * 1.1, nyquist * 0.95)
    if filter_type == "rectangular":
        taps = signal.firwin(101, cutoff, fs=sample_rate_hz)
        return signal.lfilter(taps, 1.0, samples)
    elif filter_type == "rrc":
        sps = sample_rate_hz / bandwidth_hz
        num_taps = int(12 * sps) | 1
        taps = _root_raised_cosine_filter(bandwidth_hz, sample_rate_hz, rolloff, num_taps)
        return signal.lfilter(taps, 1.0, samples)
    return samples

def correlator_confusion(
    bandwidth_hz: float,
    sample_rate_hz: float,
    technique_length_seconds: float,
    pulse_interval_ms: float = 10.0,
    confusion_mode: Literal["phase_flip", "timing_jitter", "both"] = "both",
    target_value: float = 1.0,
    normalization_type: Literal["peak", "rms"] = "peak",
    filter_type: str = "none"
) -> NDArray[np.complex128]:
    total_samples = math.floor(sample_rate_hz * technique_length_seconds)
    out = np.zeros(total_samples, dtype=np.complex128)
    N_zc = 127; root = 1
    n = np.arange(N_zc); zc = np.exp(-1j * np.pi * root * n * (n + 1) / N_zc)
    sps = max(1, int(sample_rate_hz / bandwidth_hz)); zc_pulsed = np.zeros(N_zc * sps, dtype=np.complex128); zc_pulsed[::sps] = zc
    taps = signal.firwin(31, min(bandwidth_hz/2, sample_rate_hz/2.1), fs=sample_rate_hz); zc_final = signal.lfilter(taps, 1.0, zc_pulsed)
    curr_ptr = 0; interval_samps = int(pulse_interval_ms * sample_rate_hz / 1000.0)
    while curr_ptr + len(zc_final) < total_samples:
        p_val = zc_final.copy()
        if confusion_mode in ["phase_flip", "both"]:
            if random.random() > 0.5: p_val *= -1
        out[curr_ptr : curr_ptr + len(zc_final)] = p_val
        jitter = 0
        if confusion_mode in ["timing_jitter", "both"]:
            jitter = random.randint(-int(interval_samps*0.2), int(interval_samps*0.2))
        curr_ptr += max(len(zc_final), interval_samps + jitter)
    out = _apply_spectral_shaping(out, bandwidth_hz, sample_rate_hz, filter_type)
    return _normalize_signal(out, target_value, normalization_type)

def narrowband_noise_creator(bandwidth_hz: float, sample_rate_hz: float, technique_length_seconds: float, interference_type: Literal["complex", "real","sinc"] = "complex", target_value: float = 1.0, normalization_type: Literal["peak", "rms"] = "peak", filter_type: str = "none") -> NDArray[np.complex128]:
    time = _create_time_array(sample_rate_hz, technique_length_seconds)
    num_samples = len(time); num_sc = math.floor(bandwidth_hz * num_samples / sample_rate_hz)
    if bandwidth_hz > 0 and num_sc == 0: num_sc = 2
    elif num_sc % 2 == 1: num_sc += 1
    freq_domain = np.zeros(num_samples, dtype=np.complex128); half = num_sc // 2
    if half > 0: freq_domain[0:half+1] = 1; freq_domain[-half:] = 1
    if interference_type == "complex": phases = 2 * np.pi * np.random.random(num_samples)
    elif interference_type == "real": phases = np.angle(np.fft.fft(np.random.randn(num_samples)))
    else: phases = np.zeros(num_samples)
    freq_domain *= np.exp(1j * phases); out = np.fft.ifft(freq_domain)
    if interference_type != "complex": out = np.real(out)
    out = _apply_spectral_shaping(out, bandwidth_hz, sample_rate_hz, filter_type)
    return _normalize_signal(out, target_value, normalization_type)

def rrc_modulated_noise(symbol_rate_hz: float, sample_rate_hz: float, rolloff: float, technique_length_seconds: float, target_value: float = 1.0, normalization_type: Literal["peak", "rms"] = "peak", filter_type: str = "none") -> NDArray[np.float64]:
    num_samples = math.floor(technique_length_seconds * sample_rate_hz); noise = np.random.randn(num_samples); sps = sample_rate_hz / symbol_rate_hz; num_taps = int(12 * sps) | 1
    coeffs = _root_raised_cosine_filter(symbol_rate_hz, sample_rate_hz, rolloff, num_taps); out = signal.lfilter(coeffs, 1.0, noise)
    return _normalize_signal(out, target_value, normalization_type)

def swept_noise_creator(sweep_hz: float, bandwidth_hz: float, sample_rate_hz: float, technique_length_seconds: float, sweep_type: Literal["sawtooth", "triangle"] = "sawtooth", sweep_rate_hz_s: float = 0, interference_type: str = "complex", target_value: float = 1.0, normalization_type: Literal["peak", "rms"] = "peak", filter_type: str = "none") -> NDArray[np.complex128]:
    if sweep_rate_hz_s > 0: effective_duration = sweep_hz / sweep_rate_hz_s
    else: effective_duration = technique_length_seconds
    noise = narrowband_noise_creator(bandwidth_hz, sample_rate_hz, technique_length_seconds, interference_type, 1.0, "peak", filter_type)
    time = _create_time_array(sample_rate_hz, technique_length_seconds)
    if sweep_type == "triangle": freq = (2 * sweep_hz / effective_duration) * np.abs((time % effective_duration) - effective_duration / 2) - (sweep_hz / 2)
    else: freq = (sweep_hz / effective_duration) * (time % effective_duration) - (sweep_hz / 2)
    phase = np.cumsum(freq) / sample_rate_hz; out = noise * np.exp(1j * 2 * np.pi * phase)
    return _normalize_signal(out, target_value, normalization_type)

def chunk_noise_creator(technique_width_hz: float, chunks: int, sample_rate_hz: float, technique_length_seconds: float, interference_type: str = "complex", target_value: float = 1.0, normalization_type: Literal["peak", "rms"] = "peak", filter_type: str = "none") -> NDArray[np.complex128]:
    bw = technique_width_hz / chunks; noise = narrowband_noise_creator(bw, sample_rate_hz, technique_length_seconds, interference_type, 1.0, "peak", filter_type)
    time = _create_time_array(sample_rate_hz, technique_length_seconds); centers = np.linspace(-technique_width_hz/2 + bw/2, technique_width_hz/2 - bw/2, chunks); indices = np.floor(time / technique_length_seconds * chunks).astype(int).clip(0, chunks-1); order = np.arange(chunks); np.random.shuffle(order); out = noise * np.exp(1j * 2 * np.pi * centers[order[indices]] * time)
    return _normalize_signal(out, target_value, normalization_type)

def noise_tones(frequencies_str: str, bandwidth_hz: float, sample_rate_hz: float, technique_length_seconds: float, interference_type: str = "complex", target_value: float = 1.0, normalization_type: Literal["peak", "rms"] = "peak", filter_type: str = "none") -> NDArray:
    freqs = [float(f) for f in frequencies_str.split()]; time = _create_time_array(sample_rate_hz, technique_length_seconds); base = narrowband_noise_creator(bandwidth_hz, sample_rate_hz, technique_length_seconds, interference_type, 1.0, "peak", filter_type); out = np.zeros(len(time), dtype=np.complex128)
    for f in freqs: out += base * np.exp(1j * 2 * np.pi * f * time)
    return _normalize_signal(out, target_value, normalization_type)

def cosine_tones(frequencies_str: str, sample_rate_hz: float, technique_length_seconds: float, target_value: float = 1.0, normalization_type: Literal["peak", "rms"] = "peak", filter_type: str = "none") -> NDArray:
    freqs = [float(f) for f in frequencies_str.split()]; time = _create_time_array(sample_rate_hz, technique_length_seconds); out = np.zeros(len(time))
    for f in freqs: out += np.cos(2 * np.pi * f * time)
    return _normalize_signal(out, target_value, normalization_type)

def phasor_tones(frequencies_str: str, sample_rate_hz: float, technique_length_seconds: float, target_value: float = 1.0, normalization_type: Literal["peak", "rms"] = "peak", filter_type: str = "none") -> NDArray:
    freqs = [float(f) for f in frequencies_str.split()]; time = _create_time_array(sample_rate_hz, technique_length_seconds); out = np.zeros(len(time), dtype=np.complex128)
    for f in freqs: out += np.exp(1j * 2 * np.pi * f * time)
    return _normalize_signal(out, target_value, normalization_type)

def swept_phasors(sweep_hz: float, tones: int, sample_rate_hz: float, technique_length_seconds: float, sweep_rate_hz_s: float = 0, target_value: float = 1.0, normalization_type: Literal["peak", "rms"] = "peak", filter_type: str = "none") -> NDArray:
    if sweep_rate_hz_s > 0: effective_duration = sweep_hz / sweep_rate_hz_s
    else: effective_duration = technique_length_seconds
    time = _create_time_array(sample_rate_hz, technique_length_seconds); out = np.zeros(len(time), dtype=np.complex128); freqs = np.linspace(-sweep_hz/2, sweep_hz/2, tones, endpoint=False); m_sw = sweep_hz / effective_duration
    for f0 in freqs: f = (m_sw / 1.0) * (time % effective_duration) + f0; out += np.exp(1j * 2 * np.pi * np.cumsum(f) / sample_rate_hz)
    return _normalize_signal(out, target_value, normalization_type)

def swept_cosines(sweep_hz: float, tones: int, sample_rate_hz: float, technique_length_seconds: float, sweep_rate_hz_s: float = 0, target_value: float = 1.0, normalization_type: Literal["peak", "rms"] = "peak", filter_type: str = "none") -> NDArray:
    if sweep_rate_hz_s > 0: effective_duration = sweep_hz / sweep_rate_hz_s
    else: effective_duration = technique_length_seconds
    time = _create_time_array(sample_rate_hz, technique_length_seconds); out = np.zeros(len(time)); freqs = np.linspace(-sweep_hz/2, sweep_hz/2, tones, endpoint=False); m_sw = sweep_hz / effective_duration
    for f0 in freqs: f = (m_sw / 1.0) * (time % effective_duration) + f0; out += np.cos(2 * np.pi * np.cumsum(f) / sample_rate_hz)
    return _normalize_signal(out, target_value, normalization_type)

def FM_cosine(sweep_range_hz: float, modulated_frequency: float, sample_rate_hz: float, technique_length_seconds: float, target_value: float = 1.0, normalization_type: Literal["peak", "rms"] = "peak", filter_type: str = "none") -> NDArray:
    time = _create_time_array(sample_rate_hz, technique_length_seconds); dev = 0.5 * sweep_range_hz * np.cos(2 * np.pi * modulated_frequency * time); out = np.exp(1j * 2 * np.pi * np.cumsum(dev) / sample_rate_hz)
    return _normalize_signal(out, target_value, normalization_type)

def lfm_chirp(start_freq_hz: float, end_freq_hz: float, sample_rate_hz: float, technique_length_seconds: float, target_value: float = 1.0, normalization_type: Literal["peak", "rms"] = "peak", filter_type: str = "none") -> NDArray:
    time = _create_time_array(sample_rate_hz, technique_length_seconds); phi = 2 * np.pi * (start_freq_hz * time + 0.5 * (end_freq_hz - start_freq_hz) * time**2 / technique_length_seconds)
    return _normalize_signal(np.exp(1j * phi), target_value, normalization_type)

def fhss_noise(hop_frequencies_str: str, hop_duration_seconds: float, bandwidth_hz: float, sample_rate_hz: float, technique_length_seconds: float, interference_type: str = "complex", target_value: float = 1.0, normalization_type: Literal["peak", "rms"] = "peak", filter_type: str = "none") -> NDArray:
    freqs = [float(f) for f in hop_frequencies_str.split()]; time = _create_time_array(sample_rate_hz, technique_length_seconds); sph = max(1, math.floor(sample_rate_hz * hop_duration_seconds)); num_hops = math.ceil(len(time) / sph); base = narrowband_noise_creator(bandwidth_hz, sample_rate_hz, technique_length_seconds, interference_type, 1.0, "peak", filter_type); shifter = np.zeros(len(time), dtype=np.complex128)
    for i in range(num_hops):
        s, e = i*sph, min((i+1)*sph, len(time))
        if s >= len(time): break
        shifter[s:e] = np.exp(1j * 2 * np.pi * freqs[i % len(freqs)] * time[s:e])
    return _normalize_signal(base * shifter, target_value, normalization_type)

def ofdm_shaped_noise(fft_size: int, num_subcarriers: int, cp_length: int, sample_rate_hz: float, technique_length_seconds: float, target_value: float = 1.0, normalization_type: Literal["peak", "rms"] = "peak", filter_type: str = "none") -> NDArray:
    total = math.floor(sample_rate_hz * technique_length_seconds); sym_len = fft_size + cp_length; parts = []
    for _ in range(math.ceil(total / sym_len)):
        fd = np.zeros(fft_size, dtype=np.complex128); sc = (fft_size - num_subcarriers) // 2; fd[sc:sc+num_subcarriers] = (np.random.randn(num_subcarriers) + 1j * np.random.randn(num_subcarriers)) / np.sqrt(2); td = np.fft.ifft(np.fft.ifftshift(fd)); parts.append(np.concatenate([td[-cp_length:], td]))
    return _normalize_signal(np.concatenate(parts)[:total], target_value, normalization_type)

def songMaker(songName: str, bandwidth_hz: float, sample_rate_hz: float, target_value: float = 1.0, normalization_type: Literal["peak", "rms"] = "peak", filter_type: str = "none") -> NDArray:
    def noteMaker(noteLengthInBeats,noteNumber,bpm,sampsPerSec,bandwidth):
        BaseFreq=155.563; X=np.arange(0,7,1/12); B=2**X*BaseFreq
        secPerBeats=60/bpm; sampsPerPeriod=int(1/B[noteNumber]*sampsPerSec); sampsPerNote=sampsPerSec*secPerBeats*noteLengthInBeats
        cyclesPerNote=round(sampsPerNote/sampsPerPeriod*.9); sampsWithSilence=round(sampsPerNote-cyclesPerNote*sampsPerPeriod)
        E=max(round(bandwidth/(sampsPerSec/sampsPerPeriod)/2), 2)
        F=np.zeros(sampsPerPeriod); F[0:E]=1; G=np.real(np.fft.fft(F)); G-=np.mean(G)
        mx = np.max(np.abs(G))
        if mx > 0: G/=mx
        G -= np.roll(G, round(sampsPerPeriod/2))
        mx = np.max(np.abs(G))
        if mx > 0: G/=mx
        I_parts = [G]*cyclesPerNote
        if sampsWithSilence > 0:
            F=np.zeros(sampsWithSilence); E=round(bandwidth/(sampsPerSec/sampsWithSilence)/2); F[0:E]=1; G=np.real(np.fft.fft(F)); G-=np.mean(G)
            mx = np.max(np.abs(G))
            if mx > 0: G/=mx
            I_parts.append(G)
        return np.concatenate(I_parts) if I_parts else np.array([])
    BPMval=300; A=[]; B=[]
    if songName=="Air Force Song": BPMval=300; A=[2,1,1,1,1,2,1,2,1,2,1,6,1,1,1,3,3,3,3,2,1,6,1,1,1,12,2,1,6,1,1,1,3,3,3,3,2,1,6,1,1,1,12,2,1,6,1,1,1,3,3,3,3,2,1,6,1,1,1,5,1,3,5,1,4,1,1,5,1,3,3,1,1,1,2,1,2,1,3,8,10]; B=[13,13,13,13,13,13,0,13,0,10,13,13,11,10,8,10,11,12,13,15,18,18,20,18,15,13,10,13,13,11,10,8,10,11,12,13,17,20,20,18,17,15,13,10,13,13,11,10,8,10,11,12,13,15,18,18,15,17,18,17,0,10,18,18,19,19,19,20,20,21,21,22,20,18,22,18,22,18,20,18,0]
    elif songName=="Anchors Away": BPMval=150; A=[2,1,1,1.5,.5,2,2,1,1,4,2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,1,1,1.5,.5,2,2,1,1,4,2,1,1,1,1,1,1,.75,.25,.5,.5,.75,.25,.5,.5,4,4]; B=[16,20,23,25,20,25,28,30,23,28,25,28,25,23,25,27,28,22,25,30,28,27,23,21,18,16,20,23,25,20,25,28,30,23,28,25,28,25,23,25,27,28,32,23,22,23,30,23,22,23,28,0]
    elif songName=="Marine Hymn": BPMval=240; A=[1,1,2,2,2,2,3,1,2,1,1,2,2,1,3,5,1,1,1,2,2,2,2,3,1,2,1,1,2,2,1,3,5,1,1.5,.5,2,2,2,2,3,1,2,1.5,.5,2,2,1,3,5,1,1,1,2,2,2,2,3,1,2,1,1,2,2,2,2,5,3]; B=[17,18,20,20,20,20,20,25,20,17,18,20,20,18,15,13,0,17,18,20,20,20,20,20,25,20,17,18,20,20,18,15,13,0,25,24,22,18,22,25,20,17,20,25,24,22,18,22,25,20,0,13,17,20,20,20,20,20,25,20,17,18,20,20,18,15,13,0]
    elif songName=="Army Song": BPMval=240; A=[2,1,1,2,1,1,2,1,1,1.5,.5,1,1,2,1,1,1,2,1,1,2,1,4,2,1,1,2,1,1,2,1,1,1.5,.5,1,1,2,1,1,1,2,1,1,2,1,4,2,1,1,2,2,2,1,1,1,1,1,1,4,1,2,1,1,1,1,1,4,2,1,1,2,2,4,1.5,.5,1,1,2,1,1,1,2,1,1,2,1,4,2,1,1,1,2,1,1,2,1,4]; B=[0,14,11,14,14,11,14,14,11,14,16,14,11,14,11,12,14,12,9,14,12,9,7,0,14,11,14,14,11,14,14,11,14,16,14,11,14,11,12,14,12,9,14,12,9,7,0,14,14,19,19,14,14,14,16,18,19,16,14,19,19,18,16,18,19,16,21,0,14,14,19,19,18,16,18,19,16,14,11,12,14,12,9,14,12,9,7,0,11,12,14,12,9,14,16,18,19]
    elif songName=="Baby Shark": BPMval=110; A=[1,1,.5,.5,.5,.25,.5,.25,.5,.5,.5,.5,.5,.5,.25,.5,.25,.5,.5,.5,.5,.5,.5,.25,.5,.25,.5,.5,.5,1,1]; B=[9,11,14,14,14,14,14,14,14,9,11,14,14,14,14,14,14,14,9,11,14,14,14,14,14,14,14,14,14,13,0]
    elif songName=="Star Wars": BPMval=160; A=[1.5,0.25,0.25,1.5,0.25,0.25,0.33,0.33,0.33,0.33,0.33,0.33,0.33,0.33,0.33,0.66,0.17,0.17,0.17,0.33,0.33,0.33,1,1,0.33,0.33,0.33,4,4,0.66,0.66,0.66,4,2,0.66,0.66,0.66,4,2,0.66,0.66,0.66,4,1,0.33,0.33,0.33,4,4,0.66,0.66,0.66,4,2,0.66,0.66,0.66,4,2,0.66,0.66,0.66,3,1,1.5,0.5,3,1,1,1,1,1,0.66,0.66,0.66,1.5,0.5,2,1.5,0.5,3,1,1,1,1,0.5,0.5,1.5,0.5,5,1,3,1,1,1,1,1,0.66,0.66,0.66,1.5,0.5,2,1.5,0.5,1.33,0.66,1.33,0.66,1.33,0.66,1.33,0.66,6,0.66,0.66,0.66,3,1,2,2,4,4,0.66,0.66,0.66,4,2,0.66,0.66,0.66,4,2,0.66,0.66,0.66,3,1]; B=[7,7,7,7,7,7,7,2,12,14,12,7,7,2,12,14,7,7,7,12,7,14,17,0,2,2,2,7,14,12,11,9,19,14,12,11,9,19,14,12,11,12,9,0,2,2,2,7,14,12,11,9,19,14,12,11,9,19,14,12,11,12,9,0,2,2,4,4,12,11,9,7,7,9,11,9,4,6,2,2,4,4,12,11,9,7,14,14,9,9,2,4,6,12,11,9,7,7,9,11,9,4,6,14,14,19,17,15,14,12,10,9,7,14,14,14,14,4,7,12,9,7,14,12,11,9,19,14,12,11,9,19,14,12,11,12,9,0]
    elif songName=="Pink Panther": BPMval=320; A=[1,1,4,1,1,4,1,1,1,1,1,1,1,1,1,1,1,1,1,7,1,1,1,1,7,5,1,1,4,1,1,4,1,1,1,1,1,1,1,1,1,1,1,1,1,18,5,1,1,4,1,1,4,1,1,1,1,1,1,1,1,1,1,1,1,1,7,1,1,1,1,7,9,2,1,2,1,2,1,1,2,1,2,1,2,1,2,1,1,1,2,13,5]; B=[12,13,0,15,16,0,12,13,0,15,16,0,21,20,0,13,16,0,20,19,18,16,13,11,13,0,12,13,0,15,16,0,12,13,0,15,16,0,21,20,0,16,20,0,25,24,0,12,13,0,15,16,0,12,13,0,15,16,0,21,20,0,13,16,0,20,19,18,16,13,11,13,0,25,23,20,18,16,13,19,18,19,18,19,18,19,18,16,13,11,13,13,0]
    elif songName=="Mission Impossible": BPMval=90; A=[0.5,0.25,0.5,0.25,0.75,0.5,0.25,0.5,0.5,0.5,0.25,0.5,0.25,0.75,0.5,0.25,0.5,0.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,3.5,0.25,0.25,1.75,0.75,0.5,0.5,0.75,3.25,2.25,0.25,0.25,0.25,2.25,0.25,0.25,0.25,2.25,0.25,0.25,0.25,0.25,2.75,1]; B=[6,6,6,6,6,6,6,9,11,6,6,6,6,6,6,6,4,5,21,18,13,21,18,13,21,18,11,9,11,0,9,6,17,9,6,16,9,6,15,14,13,0,26,23,18,26,23,17,26,23,16,14,16,0,9,6,17,9,6,16,9,6,15,14,13,0,21,18,13,21,18,12,21,18,11,9,11,0,18,21,23,25,0,11,6,9,11,10,6,11,10,9,6,9,8,7,6,0]
    elif songName=="Annoying Tone": BPMval=100; A=[1]; B=[60]
    parts = []
    for j in range(len(A)): parts.append(noteMaker(A[j],B[j],BPMval,sample_rate_hz,bandwidth_hz))
    return _normalize_signal(np.concatenate(parts) if parts else np.array([]), target_value, normalization_type)

def wifi_preamble(
    sample_rate_hz: float,
    technique_length_seconds: float,
    mode: Literal["802.11b", "802.11g"] = "802.11b",
    target_value: float = 1.0,
    normalization_type: Literal["peak", "rms"] = "peak"
) -> NDArray[np.complex128]:
    """Generates a WiFi-like preamble sync pattern for sabotage attacks."""
    total_samples = math.floor(sample_rate_hz * technique_length_seconds)
    out = np.zeros(total_samples, dtype=np.complex128)
    
    if mode == "802.11b":
        # Barker 11 code
        barker = np.array([1, 1, 1, -1, -1, -1, 1, -1, -1, 1, -1], dtype=np.complex128)
        # 11 Mcps, 1 Mbps DBPSK
        sps = max(1, int(sample_rate_hz / 11e6)) 
        pattern = np.repeat(barker, sps)
    else:
        # Simplified L-STF (Short Training Field) for 802.11g/n
        # 10 repetitions of a 0.8us sequence
        seq = np.array([0, 0, 1+1j, 0, 0, 0, -1-1j, 0, 0, 0, 1+1j, 0, 0, 0, -1-1j, 0, 0, 0, -1-1j, 0, 0, 0, 1+1j, 0, 0, 0, 0, 0, 0, 0, -1-1j, 0, 0, 0, -1-1j, 0, 0, 0, 1+1j, 0, 0, 0, 1+1j, 0, 0, 0, 1+1j, 0, 0, 0, 1+1j, 0, 0], dtype=np.complex128)
        td = np.fft.ifft(np.fft.ifftshift(seq))
        pattern = np.tile(td, 10)
    
    # Repeat the pattern throughout the duration
    p_len = len(pattern)
    for i in range(0, total_samples, p_len):
        chunk = min(p_len, total_samples - i)
        out[i:i+chunk] = pattern[:chunk]
        
    return _normalize_signal(out, target_value, normalization_type)

def differential_comb_creator(
    spike_spacing_hz: float,
    spike_count: int,
    sample_rate_hz: float,
    technique_length_seconds: float,
    target_value: float = 1.0,
    normalization_type: Literal["peak", "rms"] = "peak",
    filter_type: str = "none"
) -> NDArray[np.complex128]:
    """Generates a comb of high-power spectral spikes."""
    time = _create_time_array(sample_rate_hz, technique_length_seconds)
    out = np.zeros(len(time), dtype=np.complex128)
    
    # Generate K spikes on each side of DC
    K = spike_count // 2
    for k in range(-K, K + 1):
        freq = k * spike_spacing_hz
        phase_offset = random.uniform(0, 2 * np.pi) # Randomize phase to lower PAPR
        out += np.exp(1j * (2 * np.pi * freq * time + phase_offset))
        
    out = _apply_spectral_shaping(out, spike_spacing_hz * spike_count, sample_rate_hz, filter_type)
    return _normalize_signal(out, target_value, normalization_type)

waveform_definitions = {
    "Narrowband Noise": {
        "func": narrowband_noise_creator,
        "params": [
            {"name": "bandwidth_hz", "title": "Bandwidth (Hz)", "type": "entry", "default": "100000"},
            {"name": "sample_rate_hz", "title": "Sample Rate (Hz)", "type": "entry", "default": "2000000"},
            {"name": "technique_length_seconds", "title": "Length (s)", "type": "entry", "default": "0.1"},
            {"name": "interference_type", "title": "Type", "type": "options", "choices": ["complex", "real", "sinc"], "default": "complex"}
        ]
    },
    "Differential Comb": {
        "func": differential_comb_creator,
        "params": [
            {"name": "spike_spacing_hz", "title": "Spacing (Hz)", "type": "entry", "default": "30000"},
            {"name": "spike_count", "title": "Spike Count", "type": "entry", "default": "10"},
            {"name": "sample_rate_hz", "title": "Sample Rate (Hz)", "type": "entry", "default": "2000000"},
            {"name": "technique_length_seconds", "title": "Length (s)", "type": "entry", "default": "0.1"}
        ]
    },
    "RRC Modulated Noise": {
        "func": rrc_modulated_noise,
        "params": [
            {"name": "symbol_rate_hz", "title": "Symbol Rate (Hz)", "type": "entry", "default": "50000"},
            {"name": "sample_rate_hz", "title": "Sample Rate (Hz)", "type": "entry", "default": "2000000"},
            {"name": "rolloff", "title": "Rolloff", "type": "entry", "default": "0.35"},
            {"name": "technique_length_seconds", "title": "Length (s)", "type": "entry", "default": "0.1"}
        ]
    },
    "Swept Noise": {
        "func": swept_noise_creator,
        "params": [
            {"name": "sweep_hz", "title": "Sweep Range (Hz)", "type": "entry", "default": "500000"},
            {"name": "bandwidth_hz", "title": "BW (Hz)", "type": "entry", "default": "50000"},
            {"name": "sample_rate_hz", "title": "Sample Rate (Hz)", "type": "entry", "default": "2000000"},
            {"name": "technique_length_seconds", "title": "Duration (s)", "type": "entry", "default": "0.1"},
            {"name": "sweep_type", "title": "Sweep Type", "type": "options", "choices": ["sawtooth", "triangle"], "default": "sawtooth"},
            {"name": "sweep_rate_hz_s", "title": "Sweep Rate (Hz/s)", "type": "entry", "default": "0"},
            {"name": "interference_type", "title": "Type", "type": "options", "choices": ["complex", "real", "sinc"], "default": "complex"}
        ]
    },
    "Chunked Noise": {
        "func": chunk_noise_creator,
        "params": [
            {"name": "technique_width_hz", "title": "Width (Hz)", "type": "entry", "default": "1000000"},
            {"name": "chunks", "title": "Chunks", "type": "entry", "default": "10"},
            {"name": "sample_rate_hz", "title": "Sample Rate (Hz)", "type": "entry", "default": "2000000"},
            {"name": "technique_length_seconds", "title": "Length (s)", "type": "entry", "default": "0.1"},
            {"name": "interference_type", "title": "Type", "type": "options", "choices": ["complex", "real", "sinc"], "default": "complex"}
        ]
    },
    "Noise Tones": {
        "func": noise_tones,
        "params": [
            {"name": "frequencies_str", "title": "Freqs (Hz)", "type": "entry", "default": "-100000 0 100000"},
            {"name": "bandwidth_hz", "title": "BW (Hz)", "type": "entry", "default": "10000"},
            {"name": "sample_rate_hz", "title": "Sample Rate (Hz)", "type": "entry", "default": "2000000"},
            {"name": "technique_length_seconds", "title": "Length (s)", "type": "entry", "default": "0.1"},
            {"name": "interference_type", "title": "Type", "type": "options", "choices": ["complex", "real", "sinc"], "default": "complex"}
        ]
    },
    "Cosine Tones": {
        "func": cosine_tones,
        "params": [
            {"name": "frequencies_str", "title": "Freqs (Hz)", "type": "entry", "default": "10000 50000 100000"},
            {"name": "sample_rate_hz", "title": "Sample Rate (Hz)", "type": "entry", "default": "2000000"},
            {"name": "technique_length_seconds", "title": "Length (s)", "type": "entry", "default": "0.1"}
        ]
    },
    "Phasor Tones": {
        "func": phasor_tones,
        "params": [
            {"name": "frequencies_str", "title": "Freqs (Hz)", "type": "entry", "default": "10000 50000 100000"},
            {"name": "sample_rate_hz", "title": "Sample Rate (Hz)", "type": "entry", "default": "2000000"},
            {"name": "technique_length_seconds", "title": "Length (s)", "type": "entry", "default": "0.1"}
        ]
    },
    "Swept Phasors": {
        "func": swept_phasors,
        "params": [
            {"name": "sweep_hz", "title": "Sweep (Hz)", "type": "entry", "default": "500000"},
            {"name": "tones", "title": "Tones", "type": "entry", "default": "5"},
            {"name": "sweep_rate_hz_s", "title": "Sweep Rate (Hz/s)", "type": "entry", "default": "0"},
            {"name": "sample_rate_hz", "title": "Sample Rate (Hz)", "type": "entry", "default": "2000000"},
            {"name": "technique_length_seconds", "title": "Length (s)", "type": "entry", "default": "0.1"}
        ]
    },
    "Swept Cosines": {
        "func": swept_cosines,
        "params": [
            {"name": "sweep_hz", "title": "Sweep (Hz)", "type": "entry", "default": "500000"},
            {"name": "tones", "title": "Tones", "type": "entry", "default": "5"},
            {"name": "sweep_rate_hz_s", "title": "Sweep Rate (Hz/s)", "type": "entry", "default": "0"},
            {"name": "sample_rate_hz", "title": "Sample Rate (Hz)", "type": "entry", "default": "2000000"},
            {"name": "technique_length_seconds", "title": "Length (s)", "type": "entry", "default": "0.1"}
        ]
    },
    "FM Cosine": {
        "func": FM_cosine,
        "params": [
            {"name": "sweep_range_hz", "title": "Sweep (Hz)", "type": "entry", "default": "100000"},
            {"name": "modulated_frequency", "title": "Mod Freq (Hz)", "type": "entry", "default": "1000"},
            {"name": "sample_rate_hz", "title": "Sample Rate (Hz)", "type": "entry", "default": "2000000"},
            {"name": "technique_length_seconds", "title": "Length (s)", "type": "entry", "default": "0.1"}
        ]
    },
    "LFM Chirp": {
        "func": lfm_chirp,
        "params": [
            {"name": "start_freq_hz", "title": "Start (Hz)", "type": "entry", "default": "-500000"},
            {"name": "end_freq_hz", "title": "End (Hz)", "type": "entry", "default": "500000"},
            {"name": "sample_rate_hz", "title": "Sample Rate (Hz)", "type": "entry", "default": "2000000"},
            {"name": "technique_length_seconds", "title": "Length (s)", "type": "entry", "default": "0.1"}
        ]
    },
    "FHSS Noise": {
        "func": fhss_noise,
        "params": [
            {"name": "hop_frequencies_str", "title": "Hops (Hz)", "type": "entry", "default": "-200000 0 200000"},
            {"name": "hop_duration_seconds", "title": "Duration (s)", "type": "entry", "default": "0.01"},
            {"name": "bandwidth_hz", "title": "BW (Hz)", "type": "entry", "default": "50000"},
            {"name": "sample_rate_hz", "title": "Sample Rate (Hz)", "type": "entry", "default": "2000000"},
            {"name": "technique_length_seconds", "title": "Length (s)", "type": "entry", "default": "0.1"},
            {"name": "interference_type", "title": "Type", "type": "options", "choices": ["complex", "real", "sinc"], "default": "complex"}
        ]
    },
    "OFDM-Shaped Noise": {
        "func": ofdm_shaped_noise,
        "params": [
            {"name": "fft_size", "title": "FFT Size", "type": "entry", "default": "64"},
            {"name": "num_subcarriers", "title": "Subcarriers", "type": "entry", "default": "48"},
            {"name": "cp_length", "title": "CP Length", "type": "entry", "default": "16"},
            {"name": "sample_rate_hz", "title": "Sample Rate (Hz)", "type": "entry", "default": "2000000"},
            {"name": "technique_length_seconds", "title": "Length (s)", "type": "entry", "default": "0.1"}
        ]
    },
    "Song Maker": {
        "func": songMaker,
        "params": [
            {"name": "songName", "title": "Song", "type": "options", "choices": ["Air Force Song", "Anchors Away", "Marine Hymn", "Army Song", "Baby Shark", "Star Wars", "Pink Panther", "Mission Impossible", "Annoying Tone"], "default": "Star Wars"},
            {"name": "bandwidth_hz", "title": "BW (Hz)", "type": "entry", "default": "100000"},
            {"name": "sample_rate_hz", "title": "Sample Rate (Hz)", "type": "entry", "default": "2000000"}
        ]
    },
    "Correlator Confusion": {
        "func": correlator_confusion,
        "params": [
            {"name": "bandwidth_hz", "title": "Target BW (Hz)", "type": "entry", "default": "1000000"},
            {"name": "pulse_interval_ms", "title": "Pulse Gap (ms)", "type": "entry", "default": "10.0"},
            {"name": "confusion_mode", "title": "Mode", "type": "options", "choices": ["phase_flip", "timing_jitter", "both"], "default": "both"}
        ]
    },
    "WiFi Preamble": {
        "func": wifi_preamble,
        "params": [
            {"name": "sample_rate_hz", "title": "Sample Rate (Hz)", "type": "entry", "default": "20000000"},
            {"name": "technique_length_seconds", "title": "Length (s)", "type": "entry", "default": "0.01"},
            {"name": "mode", "title": "Protocol Mode", "type": "options", "choices": ["802.11b", "802.11g"], "default": "802.11b"}
        ]
    }
}

for tech in waveform_definitions:
    waveform_definitions[tech]["params"].append({"name": "filter_type", "title": "Filter Type", "type": "options", "choices": ["none", "rectangular", "rrc"], "default": "none"})
    waveform_definitions[tech]["params"].append({"name": "target_value", "title": "Amplitude (0-1)", "type": "entry", "default": "1.0"})
    waveform_definitions[tech]["params"].append({"name": "normalization_type", "title": "Norm Type", "type": "options", "choices": ["peak", "rms"], "default": "peak"})
