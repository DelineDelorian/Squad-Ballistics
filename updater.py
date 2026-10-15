import os
import sys
import subprocess
import zipfile
import tempfile

import requests

CURRENT_VERSION = "1.1.0"

VERSION_URL = (
    "https://raw.githubusercontent.com/"
    "DelineDelorian/Squad-Ballistics/main/version.txt"
)

EXE_URL = (
    "https://github.com/"
    "DelineDelorian/Squad-Ballistics/releases/latest/download/"
    "SquadBallistics.zip"
)

UPDATE_DIR = os.path.join(
    tempfile.gettempdir(),
    "SquadBallisticsUpdate"
)

UPDATE_ZIP = os.path.join(UPDATE_DIR, "update.zip")


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
    """Download the release zip. progress_callback(percent or None)."""
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
            UPDATE_ZIP,
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

    if not zipfile.is_zipfile(UPDATE_ZIP):
        raise RuntimeError("Downloaded update is not a valid zip file")


def apply_update():
    """Replace the installed files and restart. Exits the process."""
    if not is_frozen():
        return

    exe_path = os.path.abspath(sys.executable)

    current_dir = os.path.dirname(exe_path)

    extract_dir = tempfile.mkdtemp(dir=UPDATE_DIR)

    with zipfile.ZipFile(
        UPDATE_ZIP,
        "r"
    ) as zip_ref:

        zip_ref.extractall(extract_dir)

    extracted_folder = os.path.join(
        extract_dir,
        "SquadBallistics"
    )

    if not os.path.isdir(extracted_folder):
        extracted_folder = extract_dir

    bat_path = os.path.join(UPDATE_DIR, "update.bat")

    bat = (
        "@echo off\r\n"
        # Paths may contain non-ASCII characters (e.g. a Cyrillic user
        # name in %TEMP%), so switch cmd to UTF-8 before using them.
        "chcp 65001 >nul\r\n"
        "timeout /t 2 /nobreak >nul\r\n"
        f'xcopy "{extracted_folder}" "{current_dir}" /E /H /C /I /Y >nul\r\n'
        f'del "{UPDATE_ZIP}"\r\n'
        f'rmdir /s /q "{extract_dir}"\r\n'
        f'start "" "{exe_path}"\r\n'
        '(goto) 2>nul & del "%~f0"\r\n'
    )

    with open(
        bat_path,
        "w",
        encoding="utf-8",
        newline=""
    ) as f:

        f.write(bat)

    subprocess.Popen(
        ["cmd", "/c", bat_path],
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
    )

    sys.exit(0)
