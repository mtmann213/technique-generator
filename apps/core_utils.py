import os
import json
import logging

class ConfigManager:
    _instance = None
    _config = {}

    def __new__(cls, config_path="config/system_config.json"):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config(config_path)
            cls._instance._setup_logging()
        return cls._instance

    def _load_config(self, config_path):
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                self._config = json.load(f)
        else:
            # Fallback defaults if file is missing
            self._config = {
                "hardware": {
                    "tx_usrp_serial": "34573DD",
                    "rx_usrp_serial": "3457464",
                    "signal_hound_serial": "24248760",
                    "default_sample_rate_hz": 2000000,
                    "default_center_freq_hz": 915000000
                },
                "rf_defaults": {
                    "tx_gain": 50,
                    "rx_gain": 40,
                    "external_attenuation_db": 30
                },
                "logging": {
                    "level": "INFO",
                    "file": "techniquemaker.log"
                }
            }
            # Try to save defaults to file
            try:
                os.makedirs(os.path.dirname(config_path), exist_ok=True)
                with open(config_path, "w") as f:
                    json.dump(self._config, f, indent=4)
            except Exception:
                pass

    def _setup_logging(self):
        log_level_str = self._config.get("logging", {}).get("level", "INFO").upper()
        log_level = getattr(logging, log_level_str, logging.INFO)
        log_file = self._config.get("logging", {}).get("file", "techniquemaker.log")

        logger = logging.getLogger("TechniqueMaker")
        logger.setLevel(log_level)
        
        # Prevent adding multiple handlers if instantiated multiple times
        if not logger.handlers:
            # Console handler
            ch = logging.StreamHandler()
            ch.setLevel(log_level)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            logger.addHandler(ch)

            # File handler
            try:
                fh = logging.FileHandler(log_file)
                fh.setLevel(log_level)
                fh.setFormatter(formatter)
                logger.addHandler(fh)
            except Exception:
                pass
                
        self.logger = logger

    def get(self, section, key=None, default=None):
        if key is None:
            return self._config.get(section, default)
        return self._config.get(section, {}).get(key, default)

    def get_logger(self):
        return self.logger

def parse_scientific_notation(value_str: str) -> float:
    """Safely parse strings like '900e6' or '2.4e9' without using eval()."""
    value_str = value_str.strip()
    # Simple float conversion handles scientific notation natively in Python
    try:
        return float(value_str)
    except ValueError:
        raise ValueError(f"Cannot parse '{value_str}' into a number.")
