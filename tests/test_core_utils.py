import os
import tempfile
import json
from apps.core_utils import ConfigManager, parse_scientific_notation


def test_parse_scientific_notation():
    """Test the parse_scientific_notation function."""
    # Test regular numbers
    assert parse_scientific_notation("1.5") == 1.5
    assert parse_scientific_notation("42") == 42.0
    assert parse_scientific_notation("0") == 0.0
    assert parse_scientific_notation("-3.14") == -3.14

    # Test scientific notation
    assert parse_scientific_notation("1e3") == 1000.0
    assert parse_scientific_notation("2.5e6") == 2500000.0
    assert parse_scientific_notation("1.2e-3") == 0.0012
    assert parse_scientific_notation("5E+2") == 500.0  # uppercase E

    # Test with whitespace
    assert parse_scientific_notation("  1.5  ") == 1.5
    assert parse_scientific_notation("\t2e3\n") == 2000.0

    # Test invalid input
    try:
        parse_scientific_notation("not_a_number")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    try:
        parse_scientific_notation("")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_config_manager_singleton():
    """Test that ConfigManager is a singleton."""
    # Reset singleton
    ConfigManager._instance = None
    ConfigManager._config = {}

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "test_config.json")

        # Create first instance
        config1 = ConfigManager(config_path)
        config1.get("test", "value", "default")

        # Create second instance
        config2 = ConfigManager(config_path)

        # Should be the same instance
        assert config1 is config2

        # Clean up
        ConfigManager._instance = None
        ConfigManager._config = {}


def test_config_manager_defaults():
    """Test ConfigManager loads defaults when file doesn't exist."""
    # Reset singleton
    ConfigManager._instance = None
    ConfigManager._config = {}

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "nonexistent.json")

        config = ConfigManager(config_path)

        # Should have default hardware config
        hw_config = config.get("hardware")
        assert hw_config is not None
        assert hw_config["tx_usrp_serial"] == "34573DD"
        assert hw_config["rx_usrp_serial"] == "3457464"
        assert hw_config["signal_hound_serial"] == "24248760"
        assert hw_config["default_sample_rate_hz"] == 2000000
        assert hw_config["default_center_freq_hz"] == 915000000

        # Should have default RF defaults
        rf_config = config.get("rf_defaults")
        assert rf_config is not None
        assert rf_config["tx_gain"] == 50
        assert rf_config["rx_gain"] == 40
        assert rf_config["external_attenuation_db"] == 30

        # Should have default logging
        log_config = config.get("logging")
        assert log_config is not None
        assert log_config["level"] == "INFO"
        assert log_config["file"] == "techniquemaker.log"

        # Clean up
        ConfigManager._instance = None
        ConfigManager._config = {}


def test_config_manager_loads_from_file():
    """Test ConfigManager loads configuration from file."""
    # Need to reset singleton for this test
    ConfigManager._instance = None
    ConfigManager._config = {}

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "test_config.json")

        # Create test config
        test_config = {
            "test_section": {"test_key": "test_value", "number": 42},
            "another_section": {"list": [1, 2, 3]},
        }

        with open(config_path, "w") as f:
            json.dump(test_config, f)

        # Load config
        config = ConfigManager(config_path)

        # Should have loaded our test values
        assert config.get("test_section", "test_key") == "test_value"
        assert config.get("test_section", "number") == 42
        assert config.get("another_section", "list") == [1, 2, 3]

        # Should return default for missing keys
        assert config.get("test_section", "missing", "default") == "default"

        # Clean up
        ConfigManager._instance = None
        ConfigManager._config = {}


def test_config_manager_get_logger():
    """Test ConfigManager get_logger returns a logger."""
    # Reset singleton
    ConfigManager._instance = None
    ConfigManager._config = {}

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "test_config.json")

        config = ConfigManager(config_path)
        logger = config.get_logger()

        # Should return a logging.Logger instance
        import logging

        assert isinstance(logger, logging.Logger)
        assert logger.name == "TechniqueMaker"

        # Clean up
        ConfigManager._instance = None
        ConfigManager._config = {}


def test_config_manager_get_section():
    """Test ConfigManager get() returns section dict when key is None."""
    # Need to reset singleton for this test
    ConfigManager._instance = None
    ConfigManager._config = {}

    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "test_config.json")

        # Create test config
        test_config = {
            "section_one": {"key_a": "value_a", "key_b": "value_b"},
            "section_two": {"key_c": "value_c"},
        }

        with open(config_path, "w") as f:
            json.dump(test_config, f)

        config = ConfigManager(config_path)

        # Should return the section dict
        section_one = config.get("section_one")
        assert section_one == {"key_a": "value_a", "key_b": "value_b"}

        section_two = config.get("section_two")
        assert section_two == {"key_c": "value_c"}

        # Should return default for missing section
        missing = config.get("missing_section", None, "default")
        assert missing == "default"

        # Clean up
        ConfigManager._instance = None
        ConfigManager._config = {}
