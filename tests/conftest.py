import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, ROOT)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Containers often run tests as root, where Chromium refuses its sandbox.
os.environ.setdefault("QTWEBENGINE_DISABLE_SANDBOX", "1")

try:
    # Like app.py: QtWebEngine must be imported before QApplication exists.
    import PyQt6.QtWebEngineWidgets  # noqa: F401,E402
except ImportError:
    pass

import pytest  # noqa: E402

_APP = []


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """One QApplication for the whole test run, like the real app.

    Destroying it between test modules would tear down QtWebEngine while
    its profile is still alive.
    """
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        yield None
        return

    if not _APP:
        _APP.append(
            QApplication.instance()
            or QApplication(["squad-ballistics-tests"])
        )

    yield _APP[0]
