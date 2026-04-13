import os
import tempfile
import json
from apps.session.presets import PresetManager


def test_preset_manager_empty():
    """Test PresetManager with no preset file."""
    # Use a non-existent file path
    pm = PresetManager("/tmp/nonexistent_presets.json")

    assert pm.names == []
    assert pm.get("any") is None


def test_preset_manager_loads_presets():
    """Test PresetManager loads presets from file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        preset_file = os.path.join(tmpdir, "presets.json")

        test_presets = {
            "preset1": {"freq": 915000000, "gain": 50},
            "preset2": {"freq": 2450000000, "gain": 40},
        }

        with open(preset_file, "w") as f:
            json.dump(test_presets, f)

        pm = PresetManager(preset_file)

        assert "preset1" in pm.names
        assert "preset2" in pm.names
        assert len(pm.names) == 2


def test_preset_manager_get():
    """Test getting a preset by name."""
    with tempfile.TemporaryDirectory() as tmpdir:
        preset_file = os.path.join(tmpdir, "presets.json")

        test_presets = {"test_preset": {"freq": 915000000, "gain": 50, "rate": 2000000}}

        with open(preset_file, "w") as f:
            json.dump(test_presets, f)

        pm = PresetManager(preset_file)

        preset = pm.get("test_preset")
        assert preset == {"freq": 915000000, "gain": 50, "rate": 2000000}

        # Non-existent preset
        assert pm.get("missing") is None


def test_preset_manager_save():
    """Test saving a new preset."""
    with tempfile.TemporaryDirectory() as tmpdir:
        preset_file = os.path.join(tmpdir, "presets.json")

        pm = PresetManager(preset_file)

        # Save a new preset
        pm.save("new_preset", {"freq": 868000000, "gain": 30})

        # Should be in the list
        assert "new_preset" in pm.names

        # Should have correct data
        assert pm.get("new_preset") == {"freq": 868000000, "gain": 30}

        # Should be persisted to file
        with open(preset_file, "r") as f:
            saved = json.load(f)
        assert "new_preset" in saved


def test_preset_manager_delete():
    """Test deleting a preset."""
    with tempfile.TemporaryDirectory() as tmpdir:
        preset_file = os.path.join(tmpdir, "presets.json")

        test_presets = {"preset1": {"freq": 915000000}, "preset2": {"freq": 2450000000}}

        with open(preset_file, "w") as f:
            json.dump(test_presets, f)

        pm = PresetManager(preset_file)

        # Delete existing preset
        pm.delete("preset1")

        assert "preset1" not in pm.names
        assert "preset2" in pm.names

        # Deleting non-existent preset should not error
        pm.delete("missing_preset")
        assert "missing_preset" not in pm.names


def test_preset_manager_apply_to():
    """Test applying preset to target object."""
    with tempfile.TemporaryDirectory() as tmpdir:
        preset_file = os.path.join(tmpdir, "presets.json")

        test_presets = {
            "my_preset": {
                "center_freq": 915000000,
                "tx_gain": 50,
                "sample_rate": 2000000,
            }
        }

        with open(preset_file, "w") as f:
            json.dump(test_presets, f)

        pm = PresetManager(preset_file)

        # Create a mock target object with preset attributes
        class Target:
            center_freq = None
            tx_gain = None
            sample_rate = None

        target = Target()

        # Apply preset
        result = pm.apply_to(target, "my_preset")

        assert result is True
        assert target.center_freq == 915000000
        assert target.tx_gain == 50
        assert target.sample_rate == 2000000


def test_preset_manager_apply_to_missing():
    """Test applying missing preset returns False."""
    with tempfile.TemporaryDirectory() as tmpdir:
        preset_file = os.path.join(tmpdir, "presets.json")

        # Empty presets
        with open(preset_file, "w") as f:
            json.dump({}, f)

        pm = PresetManager(preset_file)

        class Target:
            pass

        target = Target()

        result = pm.apply_to(target, "missing")

        assert result is False


def test_preset_manager_preserves_other_presets():
    """Test saving preset preserves existing ones."""
    with tempfile.TemporaryDirectory() as tmpdir:
        preset_file = os.path.join(tmpdir, "presets.json")

        # Existing presets
        existing = {"existing_preset": {"freq": 1000000000}}

        with open(preset_file, "w") as f:
            json.dump(existing, f)

        pm = PresetManager(preset_file)

        # Add new preset
        pm.save("new_preset", {"freq": 2000000000})

        # Both should exist
        assert "existing_preset" in pm.names
        assert "new_preset" in pm.names
