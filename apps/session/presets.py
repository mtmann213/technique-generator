"""Tactical preset management: save, load, list, delete mission profiles."""

import os
import json
import logging

logger = logging.getLogger("TechniqueMaker.session.presets")


class PresetManager:
    """Load, save, and apply tactical presets from JSON."""

    def __init__(self, preset_file="config/predator_presets.json"):
        self._file = preset_file
        self._presets = {}
        self._load()

    # -- Public API --

    @property
    def names(self):
        return list(self._presets.keys())

    def get(self, name):
        return self._presets.get(name)

    def save(self, name, data):
        self._presets[name] = data
        self._persist()
        logger.info(f"Preset saved: {name}")

    def delete(self, name):
        if name in self._presets:
            del self._presets[name]
            self._persist()
            logger.info(f"Preset deleted: {name}")

    def apply_to(self, target, name):
        """Apply preset values to a target object via setattr.
        Target must have the attributes as keys in the preset dict."""
        p = self.get(name)
        if not p:
            logger.warning(f"Preset not found: {name}")
            return False
        for key, value in p.items():
            if hasattr(target, key):
                setattr(target, key, value)
        logger.info(f"Preset applied: {name}")
        return True

    # -- Private --

    def _load(self):
        if os.path.exists(self._file):
            try:
                with open(self._file, "r") as f:
                    self._presets = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load presets: {e}")
                self._presets = {}

    def _persist(self):
        try:
            os.makedirs(os.path.dirname(self._file), exist_ok=True)
            with open(self._file, "w") as f:
                json.dump(self._presets, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save presets: {e}")
