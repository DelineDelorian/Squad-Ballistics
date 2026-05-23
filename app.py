import os
os.environ["QT_LOGGING_RULES"] = "*.debug=false"

import sys
import json

from PyQt6.QtWidgets import QApplication

from splash import SplashScreen

from updater import (
    check_for_updates,
    download_update,
    apply_update
)

from crosshair import MainWindow

with open(
    "weapons.json",
    "r",
    encoding="utf-8"
) as f:

    weapons = json.load(f)

app = QApplication(sys.argv)

splash = SplashScreen()

splash.show()

app.processEvents()

update = check_for_updates()

if update:

    splash.status.setText(
        f"Downloading {update}..."
    )

    def progress(percent):
        splash.progress.setValue(percent)

        app.processEvents()

    download_update(progress)

    splash.status.setText(
        "Installing..."
    )

    app.processEvents()

    apply_update()

window = MainWindow(weapons)

window.show()

splash.close()

sys.exit(app.exec())