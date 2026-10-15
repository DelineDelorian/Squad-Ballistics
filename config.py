import copy
import json
import os
import sys

APP_NAME = "SquadBallistics"

# Config used to live in "configs/config.json" relative to the working
# directory, which changes depending on how the app is started. It is read
# once from there and migrated to the per-user location below.
LEGACY_CONFIG_PATH = os.path.join("configs", "config.json")

DEFAULT_CONFIG = {
    "fov": 90,

    "fps": 60,

    "opacity": 255,

    "color": [0, 255, 0],

    "dot_enabled": True,
    "dot_size": 4,

    "lines_enabled": True,
    "line_length": 14,
    "line_thickness": 2,
    "line_gap": 6,

    "outline_enabled": True,
    "outline_thickness": 1,

    "glow_enabled": True,

    "t_style": False,

    "circle_enabled": False,
    "circle_radius": 20,

    "animated": True,

    # Multiplier for the pixel offset, to fine-tune the overlay if it does
    # not line up perfectly with the game (100 = no correction).
    "offset_scale": 100,

    "last_weapon": "",
    "arc": "auto"
}


def config_dir():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
            os.path.expanduser("~"), ".config"
        )

    return os.path.join(base, APP_NAME)


CONFIG_PATH = os.path.join(config_dir(), "config.json")


def _merge(loaded):
    """Fill missing keys with defaults and drop values of the wrong type."""
    config = copy.deepcopy(DEFAULT_CONFIG)

    if not isinstance(loaded, dict):
        return config

    for key, default in DEFAULT_CONFIG.items():
        if key not in loaded:
            continue

        value = loaded[key]

        if key == "color":
            if (
                isinstance(value, list)
                and len(value) == 3
                and all(isinstance(c, (int, float)) for c in value)
            ):
                config[key] = [max(0, min(255, int(c))) for c in value]
            continue

        if isinstance(default, bool):
            if isinstance(value, bool):
                config[key] = value
        elif isinstance(default, (int, float)):
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                config[key] = value
        elif isinstance(value, type(default)):
            config[key] = value

    return config


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config(path=None):
    path = path or CONFIG_PATH

    for candidate in (path, LEGACY_CONFIG_PATH):
        if not os.path.exists(candidate):
            continue

        try:
            config = _merge(_read(candidate))
        except (OSError, ValueError):
            # Corrupted file: fall back to defaults instead of crashing.
            continue

        if candidate != path:
            save_config(config, path)

        return config

    config = copy.deepcopy(DEFAULT_CONFIG)
    save_config(config, path)
    return config


def save_config(config, path=None):
    path = path or CONFIG_PATH

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)

        tmp = path + ".tmp"

        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

        os.replace(tmp, path)
    except OSError:
        # Never crash the UI because the config could not be written.
        pass
