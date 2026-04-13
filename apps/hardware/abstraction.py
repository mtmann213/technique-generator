"""Hardware abstraction layer for multi-SDR support.

This module provides a unified interface for different SDR hardware backends,
allowing the application to work with USRP, SoapySDR, or Sidekiq devices
without knowing the specific backend.

Usage:
    from apps.hardware.abstraction import detect_hardware, create_hardware

    # Detect available hardware
    available = detect_hardware()

    # Create a hardware instance (returns None if not available)
    hw = create_hardware("usrp", serial="34573DD")
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger("TechniqueMaker.hardware")


class SDRHardware(ABC):
    """Abstract base class for SDR hardware."""

    @abstractmethod
    def configure(
        self,
        center_freq: float,
        sample_rate: float,
        gain: float,
        bandwidth: float = 0,
    ) -> None:
        """Configure the device for transmission."""
        pass

    @abstractmethod
    def transmit(self, samples: np.ndarray, repeat: bool = False) -> int:
        """Transmit samples. Returns number of samples sent."""
        pass

    @abstractmethod
    def receive(self, num_samples: int) -> np.ndarray:
        """Receive samples."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the device."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Device name."""
        pass


class MockHardware(SDRHardware):
    """Mock hardware for testing without SDR."""

    def __init__(self) -> None:
        self._configured = False
        self._center_freq = 0.0
        self._sample_rate = 0.0
        self._gain = 0.0

    @property
    def name(self) -> str:
        return "Mock"

    def configure(
        self,
        center_freq: float,
        sample_rate: float,
        gain: float,
        bandwidth: float = 0,
    ) -> None:
        self._configured = True
        self._center_freq = center_freq
        self._sample_rate = sample_rate
        self._gain = gain
        logger.info(
            f"Mock configured: freq={center_freq / 1e6}MHz, "
            f"rate={sample_rate / 1e6}MHz, gain={gain}dB"
        )

    def transmit(self, samples: np.ndarray, repeat: bool = False) -> int:
        if not self._configured:
            raise RuntimeError("Mock not configured")
        return len(samples)

    def receive(self, num_samples: int) -> np.ndarray:
        if not self._configured:
            raise RuntimeError("Mock not configured")
        return np.zeros(num_samples, dtype=np.complex64)

    def close(self) -> None:
        logger.info("Mock closed")


def detect_hardware() -> Dict[str, bool]:
    """Detect which hardware backends are available."""
    available: Dict[str, bool] = {
        "mock": True,  # Always available
        "usrp": False,
        "soapy": False,
        "sidekiq": False,
    }

    # Check for USRP (UHD)
    try:
        import gnuradio.uhd  # type: ignore[import-unfounded]

        available["usrp"] = True
    except ImportError:
        pass

    # Check for SoapySDR
    try:
        import SoapySDR  # type: ignore[import-unfounded]

        available["soapy"] = True
    except ImportError:
        pass

    # Check for Sidekiq (look for library)
    if os.path.exists("/usr/lib/libsidekiq.so") or os.path.exists(
        "/usr/local/lib/libsidekiq.so"
    ):
        available["sidekiq"] = True

    return available


def create_hardware(hw_type: str, serial: str = "", **kwargs) -> Optional[SDRHardware]:
    """Create a hardware instance.

    Args:
        hw_type: One of "usrp", "soapy", "sidekiq", "mock"
        serial: Device serial number (optional)
        **kwargs: Additional configuration

    Returns:
        SDRHardware instance or None if hardware unavailable
    """
    available = detect_hardware()

    if hw_type == "mock":
        return MockHardware()

    if hw_type == "usrp":
        if not available["usrp"]:
            logger.warning("USRP hardware not available")
            return None
        return create_usrp_hardware(serial, **kwargs)

    if hw_type == "soapy":
        if not available["soapy"]:
            logger.warning("SoapySDR hardware not available")
            return None
        return create_soapy_hardware(serial, **kwargs)

    if hw_type == "sidekiq":
        if not available["sidekiq"]:
            logger.warning("Sidekiq hardware not available")
            return None
        return create_sidekiq_hardware(serial, **kwargs)

    logger.error(f"Unknown hardware type: {hw_type}")
    return None


def create_usrp_hardware(serial: str = "", **kwargs) -> Optional[SDRHardware]:
    """Create USRP hardware instance."""
    try:
        from gnuradio import uhd  # type: ignore[import-unfounded]

        class USRPHardware(SDRHardware):
            def __init__(self, serial: str) -> None:
                self._serial = serial
                self._device = None
                self._streamer = None

            @property
            def name(self) -> str:
                return f"USRP-{self._serial}"

            def configure(
                self,
                center_freq: float,
                sample_rate: float,
                gain: float,
                bandwidth: float = 0,
            ) -> None:
                if self._device is None:
                    self._device = uhd.grc.device_addr_specific(
                        "", serial=self._serial if self._serial else ""
                    )

            def transmit(self, samples: np.ndarray, repeat: bool = False) -> int:
                raise NotImplementedError("TX not implemented")

            def receive(self, num_samples: int) -> np.ndarray:
                raise NotImplementedError("RX not implemented")

            def close(self) -> None:
                if self._device:
                    self._device = None

        return USRPHardware(serial) if serial else None
    except ImportError:
        return None


def create_soapy_hardware(serial: str = "", **kwargs) -> Optional[SDRHardware]:
    """Create SoapySDR hardware instance."""
    try:
        import SoapySDR  # type: ignore[import-unfounded]

        class SoapyHardware(SDRHardware):
            def __init__(self, serial: str) -> None:
                self._serial = serial
                self._device = None

            @property
            def name(self) -> str:
                return f"SoapySDR-{self._serial}"

            def configure(
                self,
                center_freq: float,
                sample_rate: float,
                gain: float,
                bandwidth: float = 0,
            ) -> None:
                if self._device is None:
                    SoapySDR.setLogLevel(SoapySDR.SLL_DEBUG)
                    self._device = SoapySDR.Device(
                        {"driver": "auto", "serial": self._serial}
                    )

            def transmit(self, samples: np.ndarray, repeat: bool = False) -> int:
                raise NotImplementedError("TX not implemented")

            def receive(self, num_samples: int) -> np.ndarray:
                raise NotImplementedError("RX not implemented")

            def close(self) -> None:
                if self._device:
                    self._device = None

        return SoapyHardware(serial) if serial else None
    except ImportError:
        return None


def create_sidekiq_hardware(serial: str = "", **kwargs) -> Optional[SDRHardware]:
    """Create Sidekiq hardware instance."""
    # Sidekiq is a proprietary hardware - placeholder
    logger.warning("Sidekiq support is a placeholder")
    return None


def get_hw_from_config(config_manager: Any) -> Optional[SDRHardware]:
    """Get hardware based on config.

    Reads from ConfigManager and creates appropriate hardware.
    """
    hw_type = config_manager.get("hardware", "hw_type", "mock")
    serial = config_manager.get("hardware", "tx_usrp_serial", "")
    return create_hardware(hw_type, serial)


# Backwards compatibility - detect single preferred hardware
def detect_preferred_hardware() -> str:
    """Detect the best available hardware.

    Returns:
        hw_type: One of "usrp", "soapy", "sidekiq", "mock"
    """
    available = detect_hardware()
    if available["usrp"]:
        return "usrp"
    if available["sidekiq"]:
        return "sidekiq"
    if available["soapy"]:
        return "soapy"
    return "mock"
