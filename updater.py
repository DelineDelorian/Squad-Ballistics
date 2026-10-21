import os
import shutil
import subprocess
import sys
import tempfile

import requests

CURRENT_VERSION = "1.2.0"

VERSION_URL = (
    "https://raw.githubusercontent.com/"
    "DelineDelorian/Squad-Ballistics/main/version.txt"
)

# The app is a single .exe; an update replaces that one file.
EXE_URL = (
    "https://github.com/"
    "DelineDelorian/Squad-Ballistics/releases/latest/download/"
    "SquadBallistics.exe"
)

UPDATE_DIR = os.path.join(
    tempfile.gettempdir(),
    "SquadBallisticsUpdate"
)

NEW_EXE = os.path.join(UPDATE_DIR, "SquadBallistics.new.exe")


def is_frozen():
    """True when running from the PyInstaller .exe build."""
    return bool(getattr(sys, "frozen", False)) and sys.platform == "win32"


def parse_version(text):
    parts = []

    for part in text.strip().lstrip("vV").split("."):
        digits = "".join(c for c in part if c.isdigit())
        parts.append(int(digits) if digits else 0)

    while len(parts) < 3:
        parts.append(0)

    return tuple(parts)


def is_newer(latest, current=CURRENT_VERSION):
    try:
        return parse_version(latest) > parse_version(current)
    except ValueError:
        return False


def check_for_updates():
    """Return the newer version string, or None."""
    if not is_frozen():
        return None

    try:
        response = requests.get(
            VERSION_URL,
            timeout=5
        )

        response.raise_for_status()

        latest_version = (
            response.text.strip()
        )

    except requests.RequestException:
        return None

    if latest_version and is_newer(latest_version):
        return latest_version

    return None


def download_update(progress_callback=None):
    """Download the new .exe. progress_callback(percent or None)."""
    os.makedirs(UPDATE_DIR, exist_ok=True)

    with requests.get(
        EXE_URL,
        stream=True,
        timeout=(5, 30)
    ) as response:

        response.raise_for_status()

        total = int(
            response.headers.get(
                "content-length",
                0
            )
        )

        downloaded = 0

        with open(
            NEW_EXE,
            "wb"
        ) as f:

            for chunk in response.iter_content(65536):

                f.write(chunk)

                downloaded += len(chunk)

                if progress_callback:

                    if total:
                        progress_callback(
                            min(100, int(downloaded * 100 / total))
                        )
                    else:
                        progress_callback(None)

    if total and downloaded != total:
        raise RuntimeError("The download was interrupted")

    with open(NEW_EXE, "rb") as f:
        if f.read(2) != b"MZ":
            raise RuntimeError("Downloaded update is not a Windows program")


def update_script(new_exe, exe_path):
    """Batch script that swaps the .exe once this process has exited.

    The running .exe is locked until the app (and PyInstaller's
    bootloader) exits, so the move is retried for up to a minute. The app
    is restarted either way, so a failed update never leaves the user
    without a working program.
    """
    return (
        "@echo off\r\n"
        # Paths may contain non-ASCII characters (e.g. a Cyrillic user
        # name in %TEMP%), so switch cmd to UTF-8 before using them.
        "chcp 65001 >nul\r\n"
        "set tries=0\r\n"
        ":retry\r\n"
        "timeout /t 1 /nobreak >nul\r\n"
        f'move /y "{new_exe}" "{exe_path}" >nul 2>nul && goto start\r\n'
        "set /a tries+=1\r\n"
        "if %tries% lss 60 goto retry\r\n"
        ":start\r\n"
        f'start "" "{exe_path}"\r\n'
        '(goto) 2>nul & del "%~f0"\r\n'
    )


def apply_update():
    """Replace the running .exe with the downloaded one and restart."""
    if not is_frozen():
        return

    exe_path = os.path.abspath(sys.executable)

    bat_path = os.path.join(UPDATE_DIR, "update.bat")

    with open(
        bat_path,
        "w",
        encoding="utf-8",
        newline=""
    ) as f:

        f.write(update_script(NEW_EXE, exe_path))

    subprocess.Popen(
        ["cmd", "/c", bat_path],
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
    )

    sys.exit(0)


def remove_old_install_files():
    """Delete what the old folder-based version left next to the .exe.

    Versions up to 1.1.0 were a folder with SquadBallistics.exe and an
    "_internal" directory. Updating them puts the single-file .exe into
    that folder, leaving ~200 MB of unused files behind. Only our own,
    recognisable layout is removed.
    """
    if not is_frozen():
        return

    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    internal = os.path.join(exe_dir, "_internal")

    if os.path.normcase(getattr(sys, "_MEIPASS", "")) == os.path.normcase(
        internal
    ):
        # Still a folder build: these files are in use.
        return

    markers = ("weapons.json", "base_library.zip")

    if all(os.path.exists(os.path.join(internal, m)) for m in markers):
        shutil.rmtree(internal, ignore_errors=True)
