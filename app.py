import os
import sys

os.environ["QT_LOGGING_RULES"] = "*.debug=false"

from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox
)

try:
    # QtWebEngine must be imported before QApplication is created.
    import PyQt6.QtWebEngineWidgets  # noqa: F401
except ImportError:
    pass

from ballistics import (
    load_weapons,
    WeaponDataError
)

from utils import resource_path
from splash import SplashScreen

from updater import (
    check_for_updates,
    download_update,
    apply_update
)


def run_update(app, splash):
    update = check_for_updates()

    if not update:
        return

    splash.status.setText(
        f"Downloading {update}..."
    )

    def progress(percent):
        if percent is None:
            # Unknown size: show a busy indicator.
            splash.progress.setRange(0, 0)
        else:
            splash.progress.setValue(percent)

        app.processEvents()

    try:
        download_update(progress)

        splash.status.setText(
            "Installing..."
        )

        app.processEvents()

        apply_update()

    except Exception as e:
        # A failed update must never prevent the app from starting.
        splash.progress.setRange(0, 100)

        splash.status.setText(
            f"Update failed: {e}"
        )

        app.processEvents()


def main():
    app = QApplication(sys.argv)

    try:
        weapons = load_weapons(
            resource_path("weapons.json")
        )
    except WeaponDataError as e:
        QMessageBox.critical(
            None,
            "Squad Ballistics",
            str(e)
        )
        return 1

    splash = SplashScreen()

    splash.show()

    app.processEvents()

    run_update(app, splash)

    from crosshair import MainWindow

    window = MainWindow(weapons)

    window.show()

    splash.close()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
