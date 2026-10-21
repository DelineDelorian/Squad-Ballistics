import copy
import json
import os
import re
import sys

APP_NAME = "SquadBallistics"

# Versions up to 1.1.0 kept "configs/config.json" relative to the working
# directory (normally the folder of the .exe). It is read once from there
# and migrated to the per-user location below.
LEGACY_CONFIG_PATH = os.path.join("configs", "config.json")


def legacy_config_paths():
    paths = [LEGACY_CONFIG_PATH]

    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        paths.append(os.path.join(exe_dir, "configs", "config.json"))

    return paths

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
    "recent_weapons": [],
    "arc": "auto",

    "outline_color": "white",
    "info_enabled": True,

    # Overlay placement
    "monitor": 0,
    "center_offset_x": 0,
    "center_offset_y": 0,

    # Interface
    "language": "auto",
    "accent": "#3b82f6",
    "main_on_top": False,

    # Calculator
    "unit_mode": "auto",
    "auto_calc": True,
    "show_mods": False,
    "distance_step": 25,

    # Map page: "software" rendering fixes a black map on some GPUs/drivers;
    # map_external opens SquadCalc in the system browser instead.
    "map_render": "auto",
    "map_external": False,

    "hotkeys": {
        "toggle_overlay": "F8",
        "reset_offset": "F9",
        "distance_up": "",
        "distance_down": ""
    }
}

# Allowed values. RANGES are also the limits of the sliders in the UI.
CHOICES = {
    "language": ("auto", "ru", "en"),
    "arc": ("auto", "low", "high"),
    "unit_mode": ("auto", "deg", "mil"),
    "outline_color": ("white", "black"),
    "map_render": ("auto", "software"),
}

RANGES = {
    "fov": (1, 179),
    "fps": (10, 240),
    "opacity": (20, 255),
    "dot_size": (1, 20),
    "line_length": (1, 40),
    "line_gap": (0, 30),
    "line_thickness": (1, 10),
    "outline_thickness": (1, 5),
    "circle_radius": (5, 80),
    "offset_scale": (50, 150),
    "monitor": (0, 15),
    "center_offset_x": (-300, 300),
    "center_offset_y": (-300, 300),
    "distance_step": (1, 100),
}

DISTANCE_STEPS = (1, 5, 10, 25, 50, 100)

_HEX_COLOR = re.compile(r"#[0-9a-fA-F]{6}")


def config_dir():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
            os.path.expanduser("~"), ".config"
        )

    return os.path.join(base, APP_NAME)


def data_dir():
    """Per-user folder for caches (map tiles), separate from settings."""
    if sys.platform == "win32":
        base = (
            os.environ.get("LOCALAPPDATA")
            or os.environ.get("APPDATA")
            or os.path.expanduser("~")
        )
    else:
        base = os.environ.get("XDG_CACHE_HOME") or os.path.join(
            os.path.expanduser("~"), ".cache"
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

        if key == "hotkeys":
            if isinstance(value, dict):
                for action in default:
                    if isinstance(value.get(action), str):
                        config[key][action] = value[action]
            continue

        if key == "recent_weapons":
            if isinstance(value, list):
                config[key] = [v for v in value if isinstance(v, str)][:5]
            continue

        if isinstance(default, bool):
            if isinstance(value, bool):
                config[key] = value
        elif isinstance(default, (int, float)):
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                low, high = RANGES.get(key, (-float("inf"), float("inf")))
                config[key] = max(low, min(high, value))
        elif key in CHOICES:
            if value in CHOICES[key]:
                config[key] = value
        elif key == "accent":
            if isinstance(value, str) and _HEX_COLOR.fullmatch(value):
                config[key] = value
        elif isinstance(value, type(default)):
            config[key] = value

    if config["distance_step"] not in DISTANCE_STEPS:
        config["distance_step"] = DEFAULT_CONFIG["distance_step"]

    return config


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_config(path=None):
    path = path or CONFIG_PATH

    for candidate in [path] + legacy_config_paths():
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
