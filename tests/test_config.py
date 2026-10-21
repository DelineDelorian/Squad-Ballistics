import json

import config


def test_defaults_created(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "cfg" / "config.json"

    cfg = config.load_config(str(path))

    assert cfg == config.DEFAULT_CONFIG
    assert path.exists()

    # Mutating the returned config must not change the defaults.
    cfg["color"][0] = 1
    assert config.DEFAULT_CONFIG["color"][0] == 0


def test_missing_keys_are_filled(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"fov": 110.0, "color": [255, 0, 0]}))

    cfg = config.load_config(str(path))

    assert cfg["fov"] == 110.0
    assert cfg["color"] == [255, 0, 0]
    assert cfg["offset_scale"] == 100


def test_corrupted_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "config.json"
    path.write_text("{not json")

    assert config.load_config(str(path))["fov"] == 90


def test_wrong_types_ignored(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "fov": "wide",
        "dot_enabled": 1,
        "color": [1, 2],
        "dot_size": 7,
    }))

    cfg = config.load_config(str(path))

    assert cfg["fov"] == 90
    assert cfg["dot_enabled"] is True
    assert cfg["color"] == [0, 255, 0]
    assert cfg["dot_size"] == 7


def test_legacy_config_migrated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    legacy = tmp_path / "configs" / "config.json"
    legacy.parent.mkdir()
    legacy.write_text(json.dumps({"fov": 100}))

    path = tmp_path / "new" / "config.json"

    assert config.load_config(str(path))["fov"] == 100
    assert json.loads(path.read_text())["fov"] == 100


def test_hotkeys_merged(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "hotkeys": {"distance_up": "PgUp", "toggle_overlay": 5},
        "recent_weapons": ["a", 3, "b"],
    }))

    cfg = config.load_config(str(path))

    assert cfg["hotkeys"]["distance_up"] == "PgUp"
    assert cfg["hotkeys"]["toggle_overlay"] == "F8"
    assert cfg["hotkeys"]["reset_offset"] == "F9"
    assert cfg["recent_weapons"] == ["a", "b"]


def test_values_are_validated(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "config.json"
    path.write_text(json.dumps({
        "dot_size": 500,
        "opacity": -4,
        "fov": 0,
        "language": "klingon",
        "arc": "sideways",
        "accent": "red; background: url(x)",
        "distance_step": 7,
        "outline_color": "black",
    }))

    cfg = config.load_config(str(path))

    assert cfg["dot_size"] == config.RANGES["dot_size"][1]
    assert cfg["opacity"] == config.RANGES["opacity"][0]
    assert cfg["fov"] == 1
    assert cfg["language"] == "auto"
    assert cfg["arc"] == "auto"
    assert cfg["accent"] == config.DEFAULT_CONFIG["accent"]
    assert cfg["distance_step"] == config.DEFAULT_CONFIG["distance_step"]
    assert cfg["outline_color"] == "black"


def test_defaults_are_inside_ranges():
    for key, (low, high) in config.RANGES.items():
        assert low <= config.DEFAULT_CONFIG[key] <= high, key

    for key, choices in config.CHOICES.items():
        assert config.DEFAULT_CONFIG[key] in choices, key
