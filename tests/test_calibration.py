import os
import tempfile
import json
import numpy as np
from apps.session.calibration import CalibrationManager


def test_calibration_manager_empty():
    """Test CalibrationManager with no calibration file."""
    # Use a non-existent file path
    cal_file = "/tmp/nonexistent_calibration_file.json"
    cal = CalibrationManager(cal_file)

    assert cal.has_data is False
    assert cal.frequencies == []
    assert cal.estimate_power(1000000000, 50) is None


def test_calibration_manager_loads_data():
    """Test CalibrationManager loads calibration from file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cal_file = os.path.join(tmpdir, "calibration.json")

        # Create test calibration data
        test_cal = {
            "matrix": {
                "900000000": {"30": 10.0, "40": 20.0, "50": 30.0},
                "1000000000": {"30": 12.0, "40": 22.0, "50": 32.0},
            }
        }

        with open(cal_file, "w") as f:
            json.dump(test_cal, f)

        cal = CalibrationManager(cal_file)

        assert cal.has_data is True
        assert 900000000.0 in cal.frequencies
        assert 1000000000.0 in cal.frequencies


def test_estimate_power_exact_match():
    """Test power estimation when exact freq/gain match exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cal_file = os.path.join(tmpdir, "calibration.json")

        test_cal = {"matrix": {"1000000000": {"50": 30.0}}}

        with open(cal_file, "w") as f:
            json.dump(test_cal, f)

        cal = CalibrationManager(cal_file)

        # Exact match
        assert cal.estimate_power(1000000000, 50) == 30.0


def test_estimate_power_nearest_freq():
    """Test power estimation uses nearest frequency when exact not found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cal_file = os.path.join(tmpdir, "calibration.json")

        test_cal = {"matrix": {"900000000": {"50": 20.0}, "1100000000": {"50": 40.0}}}

        with open(cal_file, "w") as f:
            json.dump(test_cal, f)

        cal = CalibrationManager(cal_file)

        # Should use nearest freq (between 900M and 1100M, closer to 1100M)
        result = cal.estimate_power(1000000000, 50)
        assert result is not None
        # 1000M is equidistant, check it uses one of the values
        assert result in [20.0, 40.0]


def test_estimate_power_nearest_gain():
    """Test power estimation uses nearest gain when exact not found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cal_file = os.path.join(tmpdir, "calibration.json")

        test_cal = {"matrix": {"1000000000": {"30": 10.0, "50": 30.0}}}

        with open(cal_file, "w") as f:
            json.dump(test_cal, f)

        cal = CalibrationManager(cal_file)

        # Gain 40 is closer to 50 (distance 10) than 30 (distance 10)
        # Both are equidistant, argmin returns first (index 0 = 30)
        result = cal.estimate_power(1000000000, 40)
        # When equidistant, it picks the first one (30)
        assert result in [10.0, 30.0]


def test_estimate_power_no_matching_freq():
    """Test power estimation returns nearest when no exact match."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cal_file = os.path.join(tmpdir, "calibration.json")

        test_cal = {"matrix": {"1000000000": {"50": 30.0}}}

        with open(cal_file, "w") as f:
            json.dump(test_cal, f)

        cal = CalibrationManager(cal_file)

        # Even without exact match, returns nearest value (this is actual behavior)
        result = cal.estimate_power(500000000, 50)
        assert result == 30.0


def test_format_label_no_data():
    """Test format_label when no calibration data."""
    cal = CalibrationManager("/tmp/nonexistent.json")

    result = cal.format_label(1000000000, 50)
    assert result == "Est. Output: --- dBm"


def test_format_label_with_data():
    """Test format_label with calibration data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cal_file = os.path.join(tmpdir, "calibration.json")

        test_cal = {"matrix": {"1000000000": {"50": 32.5}}}

        with open(cal_file, "w") as f:
            json.dump(test_cal, f)

        cal = CalibrationManager(cal_file)

        result = cal.format_label(1000000000, 50)
        assert "32.5" in result
        assert "1000M" in result


def test_frequencies_sorted():
    """Test frequencies property returns sorted list."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cal_file = os.path.join(tmpdir, "calibration.json")

        test_cal = {
            "matrix": {
                "1100000000": {"50": 40.0},
                "900000000": {"50": 20.0},
                "1000000000": {"50": 30.0},
            }
        }

        with open(cal_file, "w") as f:
            json.dump(test_cal, f)

        cal = CalibrationManager(cal_file)

        # Should be sorted
        assert cal.frequencies == [900000000.0, 1000000000.0, 1100000000.0]
