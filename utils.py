import os
import sys


def resource_path(relative_path):
    """Absolute path to a bundled resource.

    Works both from source and from a PyInstaller build, where data files are
    unpacked into sys._MEIPASS.
    """
    base_path = getattr(
        sys,
        "_MEIPASS",
        os.path.dirname(os.path.abspath(__file__))
    )

    return os.path.join(base_path, relative_path)
