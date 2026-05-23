import os
import sys
import requests
import subprocess

from PyQt6.QtWidgets import (
    QMessageBox
)

CURRENT_VERSION = "1.0.0"

VERSION_URL = (
    "https://raw.githubusercontent.com/"
    "USERNAME/REPO/main/version.txt"
)

EXE_URL = (
    "https://github.com/"
    "USERNAME/REPO/releases/latest/download/"
    "SquadBallistics.exe"
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
        "update.exe",
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

    current_exe = os.path.basename(
        sys.argv[0]
    )

    bat = f'''
    @echo off

    timeout /t 2 /nobreak

    del "{current_exe}"

    rename update.exe "{current_exe}"

    start "" "{current_exe}"
    '''

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