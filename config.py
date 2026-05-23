import json
import os

CONFIG_PATH = "configs/config.json"

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

    "animated": True
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(config):
    os.makedirs("configs", exist_ok=True)

    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=4)