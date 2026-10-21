import os
import sys
import tempfile
import traceback

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

import config
from config import config_dir, load_config
from i18n import set_language, tr
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
        tr("splash_downloading", v=update)
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
            tr("splash_installing")
        )

        app.processEvents()

        apply_update()

    except Exception as e:
        # A failed update must never prevent the app from starting.
        splash.progress.setRange(0, 100)

        splash.status.setText(
            tr("splash_failed", e=e)
        )

        app.processEvents()


def install_crash_handler():
    """Show and log unexpected errors instead of silently closing.

    The .exe has no console, so without this a crash leaves no trace.
    """
    log_path = os.path.join(config_dir(), "crash.log")

    def handler(exc_type, exc, tb):
        text = "".join(traceback.format_exception(exc_type, exc, tb))

        try:
            os.makedirs(config_dir(), exist_ok=True)

            with open(log_path, "a", encoding="utf-8") as f:
                f.write(text + "\n")
        except OSError:
            pass

        if QApplication.instance():
            QMessageBox.critical(
                None,
                tr("error_title"),
                f"{exc}\n\n" + tr("error_saved", path=log_path)
            )

    sys.excepthook = handler


def selftest():
    """Smoke test of a build: SquadBallistics.exe --selftest

    Loads the bundled data, opens the main window and runs a calculation
    for every weapon through the UI. Exit code 0 means everything works;
    otherwise the error is written to selftest.log next to the executable.
    """
    log_path = os.path.join(
        os.path.dirname(os.path.abspath(sys.argv[0])),
        "selftest.log"
    )

    try:
        app = QApplication(sys.argv)

        # Never touch the user's real settings (last weapon, recent list).
        config.CONFIG_PATH = os.path.join(
            tempfile.mkdtemp(prefix="sb-selftest-"),
            "config.json"
        )

        weapons = load_weapons(
            resource_path("weapons.json")
        )

        from crosshair import MainWindow

        window = MainWindow(weapons)

        window.show()

        lines = []

        from ballistics import solve

        for name, weapon in weapons.items():
            # A distance the weapon can reach with its default arc
            # (some artillery cannot fire flat at short range).
            for fraction in (0.3, 0.6, 0.85):
                distance = max(
                    weapon.min_distance + 5,
                    min(weapon.max_range() * fraction, 1500)
                )

                if solve(weapon, distance).reachable:
                    break

            window.select_weapon(name)

            window.distance_entry.setText(f"{distance:.0f}")

            window.calculate()

            app.processEvents()

            solution = window.last_solution

            if solution is None or not solution.reachable:
                raise RuntimeError(
                    f"{name}: {window.status_text()} {window.sub_label.text()}"
                )

            lines.append(
                f"OK  {name}: {distance:.0f} m -> {solution.angle:.2f} deg"
            )

        window.close()

        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\nSELFTEST PASSED\n")

        return 0

    except Exception:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(traceback.format_exc() + "SELFTEST FAILED\n")

        return 1


def main():
    if "--selftest" in sys.argv:
        return selftest()

    app = QApplication(sys.argv)

    set_language(load_config()["language"])

    install_crash_handler()

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
