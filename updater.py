import os
import sys
import requests
import subprocess
import zipfile
import shutil
import tempfile

from PyQt6.QtWidgets import (
    QMessageBox
)

CURRENT_VERSION = "1.0.2"

VERSION_URL = (
    "https://raw.githubusercontent.com/"
    "DelineDelorian/Squad-Ballistics/main/version.txt"
)

EXE_URL = (
    "https://github.com/"
    "DelineDelorian/Squad-Ballistics/releases/latest/download/"
    "SquadBallistics.zip"
)

def check_for_updates():

    if not sys.argv[0].endswith(".exe"):
        return None
    try:
        response = requests.get(
            VERSION_URL,
            timeout=5
        )

        latest_version = (
            response.text.strip()
        )

        if latest_version != CURRENT_VERSION:
            return latest_version

    except:
        pass

    return None

def download_update(progress_callback=None):

    response = requests.get(
        EXE_URL,
        stream=True
    )

    total = int(
        response.headers.get(
            "content-length",
            0
        )
    )

    downloaded = 0

    with open(
        "update.zip",
        "wb"
    ) as f:

        for chunk in response.iter_content(8192):

            f.write(chunk)

            downloaded += len(chunk)

            if progress_callback:

                percent = int(
                    downloaded * 100 / total
                )

                progress_callback(percent)

def apply_update():

    if not sys.argv[0].endswith(".exe"):
        return

    current_dir = os.path.dirname(
        sys.argv[0]
    )

    temp_dir = tempfile.mkdtemp()

    with zipfile.ZipFile(
        "update.zip",
        "r"
    ) as zip_ref:

        zip_ref.extractall(temp_dir)

    extracted_folder = os.path.join(
        temp_dir,
        "SquadBallistics"
    )

    bat = f"""
    @echo off

    timeout /t 2 /nobreak

    xcopy "{extracted_folder}" "{current_dir}" /E /H /C /I /Y

    del "update.zip"

    start "" "{sys.argv[0]}"

    (goto) 2>nul & del "%~f0"
    """

    with open(
        "update.bat",
        "w"
    ) as f:

        f.write(bat)

    subprocess.Popen(
        ["update.bat"],
        shell=True
    )

    sys.exit()
