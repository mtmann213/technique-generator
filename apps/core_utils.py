"""Core utilities for TechniqueMaker."""

import logging
import os
import threading
from typing import Any, Optional

import numpy as np


class ConfigManager:
    """Thread-safe singleton configuration manager."""

    _instance: Optional["ConfigManager"] = None
    _config: dict = {}
    _lock: threading.Lock = threading.Lock()

    def __new__(cls, config_path: str = "config/system_config.json") -> "ConfigManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._load_config(config_path)
                    cls._instance._setup_logging()
        return cls._instance

    def _load_config(self, config_path: str) -> None:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                import json  # type: ignore[attr-defined]

                self._config = json.load(f)
        else:
            self._config = {
                "hardware": {
                    "tx_usrp_serial": "34573DD",
                    "rx_usrp_serial": "3457464",
                    "signal_hound_serial": "24248760",
                    "default_sample_rate_hz": 2000000,
                    "default_center_freq_hz": 915000000,
                },
                "rf_defaults": {
                    "tx_gain": 50,
                    "rx_gain": 40,
                    "external_attenuation_db": 30,
                },
                "logging": {
                    "level": "INFO",
                    "file": "techniquemaker.log",
                },
            }
            try:
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, "w") as f:
                    import json  # type: ignore[attr-defined]

                    json.dump(self._config, f, indent=4)
            except (OSError, IOError):
                pass

    def _setup_logging(self) -> None:
        log_level_str = self._config.get("logging", {}).get("level", "INFO").upper()
        log_level: int = getattr(logging, log_level_str, logging.INFO)
        log_file = self._config.get("logging", {}).get("file", "techniquemaker.log")

        logger = logging.getLogger("TechniqueMaker")
        logger.setLevel(log_level)

        if not logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(log_level)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            ch.setFormatter(formatter)
            logger.addHandler(ch)

            try:
                fh = logging.FileHandler(log_file)
                fh.setLevel(log_level)
                fh.setFormatter(formatter)
                logger.addHandler(fh)
            except OSError:
                pass

        self.logger: logging.Logger = logger

    def get(
        self,
        section: str,
        key: Optional[str] = None,
        default: Optional[Any] = None,
    ) -> Any:
        """Get config value by section and key."""
        if key is None:
            return self._config.get(section, default)
        return self._config.get(section, {}).get(key, default)

    def get_logger(self) -> logging.Logger:
        """Get the logger instance."""
        return self.logger


def parse_scientific_notation(value_str: str) -> float:
    """Safely parse strings like '900e6' or '2.4e9' without using eval()."""
    value_str = value_str.strip()
    try:
        return float(value_str)
    except ValueError:
        raise ValueError(f"Cannot parse '{value_str}' into a number.")


def dbm_tolinear(dbm: float) -> float:
    """Convert dBm to linear scale."""
    return 10 ** (dbm / 10)


def linear_todbm(linear: float) -> float:
    """Convert linear to dBm."""
    if linear <= 0:
        return float("-inf")
    return 10 * np.log10(linear)


def normalize_samples(
    samples: np.ndarray, target_db: float = 0, clip_db: float = 10
) -> np.ndarray:
    """Normalize samples to target dB with optional clipping."""
    peak = np.max(np.abs(samples))
    if peak <= 0:
        return samples
    current_db = linear_todbm(peak)
    if current_db > target_db + clip_db:
        factor = dbm_tolinear(target_db + clip_db) / peak
    elif current_db < target_db - clip_db:
        factor = dbm_tolinear(target_db - clip_db) / peak
    else:
        return samples
    return samples * factor
