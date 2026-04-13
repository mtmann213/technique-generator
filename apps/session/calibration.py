"""RF calibration matrix: gain-to-dBm mapping for power estimation."""

import os
import json
import logging
import numpy as np

logger = logging.getLogger("TechniqueMaker.session.calibration")


class CalibrationManager:
    """Load calibration data and estimate TX output power."""

    def __init__(self, cal_file="config/calibration_matrix.json"):
        self._file = cal_file
        self._matrix = {}  # {freq: {gain: dbm}}
        self._load()

    @property
    def has_data(self):
        return bool(self._matrix)

    @property
    def frequencies(self):
        return sorted(self._matrix.keys())

    def estimate_power(self, center_freq, tx_gain):
        """Estimate output power by finding nearest calibrated freq/gain.
        Returns float dBm or None if no calibration data exists."""
        if not self._matrix:
            return None
        freqs = sorted(self._matrix.keys())
        closest_f = freqs[int(np.argmin(np.abs(np.array(freqs) - center_freq)))]
        gain_map = self._matrix[closest_f]
        gain_keys = sorted(gain_map.keys())
        closest_g = gain_keys[int(np.argmin(np.abs(np.array(gain_keys) - tx_gain)))]
        return gain_map[closest_g]

    def format_label(self, center_freq, tx_gain):
        """Human-readable label for the UI."""
        pwr = self.estimate_power(center_freq, tx_gain)
        if pwr is None:
            return "Est. Output: --- dBm"
        # Find closest freq for display
        freqs = sorted(self._matrix.keys())
        closest_f = freqs[int(np.argmin(np.abs(np.array(freqs) - center_freq)))]
        return f"Est. Output: {pwr:.1f} dBm (@{closest_f/1e6:.0f}M)"

    # -- Private --

    def _load(self):
        if os.path.exists(self._file):
            try:
                with open(self._file, "r") as f:
                    raw = json.load(f)
                    m = raw.get("matrix", {})
                    self._matrix = {
                        float(k): {float(gk): gv for gk, gv in v.items()} for k, v in m.items()
                    }
            except Exception as e:
                logger.error(f"Failed to load calibration: {e}")
                self._matrix = {}
