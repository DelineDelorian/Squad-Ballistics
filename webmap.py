"""Embedded SquadCalc map (QtWebEngine).

Three things make the embedded map behave like a normal browser:

* Network. The embedded Chromium tries HTTP/3 (QUIC), Encrypted Client
  Hello and secure-DNS lookups that some networks block or throttle
  (Russia blocks QUIC to foreign sites and, since 2026, Google/Cloudflare
  encrypted DNS). The page then hangs and stays black even though the
  site opens fine in a regular browser. Those features are switched off,
  so the map uses plain HTTPS over the system DNS.
* Rendering. Some GPU/driver combinations show a black web view. A
  "software" render mode disables the GPU for the map; the page offers it
  automatically when the loaded map looks completely black.
* Speed. A persistent profile keeps map tiles in a disk cache and the
  page is created once and kept alive, so it is not reloaded on every
  visit or UI rebuild.
"""

import os

from PyQt6.QtCore import (
    QTimer,
    QUrl,
    pyqtSignal
)

from PyQt6.QtGui import (
    QColor,
    QDesktopServices
)

from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget
)

import theme
from config import data_dir
from i18n import tr

SQUADCALC_URL = "https://squadcalc.app/"

# Plain HTTPS over the system DNS (see the module docstring).
NETWORK_FLAGS = ("--disable-quic",)
DISABLED_FEATURES = (
    "EncryptedClientHello",
    "DnsOverHttps",
    "UseDnsHttpsSvcbAlpn",
)

SOFTWARE_FLAGS = ("--disable-gpu", "--disable-gpu-compositing")

# How long a page may load before help is offered.
LOAD_TIMEOUT_MS = 25000

# Wait for tiles to appear before judging whether the map is black.
BLACK_CHECK_DELAY_MS = 4000

# Keep the original values so a restart does not inherit our flags.
_ORIGINAL_FLAGS = "SB_ORIGINAL_CHROMIUM_FLAGS"
_ORIGINAL_QUICK = "SB_ORIGINAL_QT_QUICK_BACKEND"


def chromium_flags(render_mode, existing=""):
    """Chromium switches for the embedded browser."""
    flags = []
    disabled = []

    for flag in existing.split():
        if flag.startswith("--disable-features="):
            disabled += [f for f in flag.split("=", 1)[1].split(",") if f]
        elif flag not in flags:
            flags.append(flag)

    extra = list(NETWORK_FLAGS)

    if render_mode == "software":
        extra += SOFTWARE_FLAGS

    for flag in extra:
        if flag not in flags:
            flags.append(flag)

    for feature in DISABLED_FEATURES:
        if feature not in disabled:
            disabled.append(feature)

    flags.append("--disable-features=" + ",".join(disabled))

    return " ".join(flags)


def configure_environment(render_mode, environ=None):
    """Set up QtWebEngine. Must run before QApplication is created."""
    environ = os.environ if environ is None else environ

    if _ORIGINAL_FLAGS not in environ:
        environ[_ORIGINAL_FLAGS] = environ.get(
            "QTWEBENGINE_CHROMIUM_FLAGS", ""
        )
        environ[_ORIGINAL_QUICK] = environ.get("QT_QUICK_BACKEND", "")

    environ["QTWEBENGINE_CHROMIUM_FLAGS"] = chromium_flags(
        render_mode,
        environ[_ORIGINAL_FLAGS]
    )

    if render_mode == "software":
        # The web view is drawn through Qt Quick; render that in software
        # too, otherwise a broken GPU path stays black.
        environ["QT_QUICK_BACKEND"] = "software"
    elif environ[_ORIGINAL_QUICK]:
        environ["QT_QUICK_BACKEND"] = environ[_ORIGINAL_QUICK]
    else:
        environ.pop("QT_QUICK_BACKEND", None)


def looks_black(image, threshold=0.97):
    """True when (almost) every sampled pixel of the image is black."""
    if image.isNull() or image.width() < 10 or image.height() < 10:
        return False

    columns, rows = 32, 24
    dark = 0

    for i in range(columns):
        for j in range(rows):
            color = image.pixelColor(
                int((i + 0.5) * image.width() / columns),
                int((j + 0.5) * image.height() / rows)
            )

            if color.red() + color.green() + color.blue() < 24:
                dark += 1

    return dark >= threshold * columns * rows


def open_external(url=SQUADCALC_URL):
    QDesktopServices.openUrl(QUrl(url))


def _make_page_classes():
    """Page classes are created lazily: QtWebEngine may be missing."""
    from PyQt6.QtWebEngineCore import QWebEnginePage

    class ExternalLinkPage(QWebEnginePage):
        """Target of target=_blank links: opens them in the system browser."""

        def acceptNavigationRequest(self, url, nav_type, is_main_frame):
            open_external(url.toString())
            self.deleteLater()
            return False

    class MapWebPage(QWebEnginePage):
        def createWindow(self, window_type):
            return ExternalLinkPage(self.profile(), self)

    return MapWebPage


def create_profile(name="SquadBallistics"):
    """Persistent profile: cookies, SquadCalc settings and a tile cache."""
    from PyQt6.QtWebEngineCore import QWebEngineProfile

    base = os.path.join(data_dir(), "WebEngine")

    profile = QWebEngineProfile(name)

    profile.setPersistentStoragePath(os.path.join(base, "Storage"))
    profile.setCachePath(os.path.join(base, "Cache"))
    profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
    profile.setHttpCacheMaximumSize(512 * 1024 * 1024)

    return profile


_shared_profile = None


def shared_profile():
    """The one profile of the process.

    Chromium does not cope well with a profile being deleted and created
    again under the same name, so it is created once and kept until the
    process exits (pages are deleted before that, see MapPage.shutdown).
    """
    global _shared_profile

    from PyQt6 import sip

    if _shared_profile is None or sip.isdeleted(_shared_profile):
        _shared_profile = create_profile()

        # Owned by C++ without a parent: never destroyed by Python's
        # garbage collector in the middle of the shutdown.
        sip.transferto(_shared_profile, None)

    return _shared_profile


class MapPage(QWidget):
    """Map tab: a small toolbar, the web view and a help panel."""

    compat_requested = pyqtSignal()

    def __init__(self, config):
        super().__init__()

        self.config = config

        self.view = None
        self.page = None
        self.profile = None

        self.loading = False

        layout = QVBoxLayout(self)

        layout.setContentsMargins(16, 12, 16, 16)

        layout.setSpacing(8)

        toolbar = QHBoxLayout()

        self.status = QLabel()

        self.status.setProperty("role", "muted")

        self.reload_button = QPushButton()
        self.reload_button.setProperty("flat_style", True)
        self.reload_button.clicked.connect(self.reload)

        self.external_button = QPushButton()
        self.external_button.setProperty("flat_style", True)
        self.external_button.clicked.connect(lambda: open_external())

        toolbar.addWidget(self.status, 1)
        toolbar.addWidget(self.reload_button)
        toolbar.addWidget(self.external_button)

        layout.addLayout(toolbar)

        self.progress = QProgressBar()

        self.progress.setTextVisible(False)

        self.progress.setFixedHeight(3)

        self.progress.setRange(0, 100)

        self.progress.setStyleSheet(
            f"QProgressBar {{ background: transparent; border: none; }}"
            f"QProgressBar::chunk {{ background: {config['accent']}; }}"
        )

        self.progress.hide()

        layout.addWidget(self.progress)

        # Help panel: shown when the map fails, hangs or looks black.
        self.panel = QFrame()

        self.panel.setObjectName("card")

        panel_layout = QVBoxLayout(self.panel)

        panel_layout.setContentsMargins(20, 16, 20, 16)

        self.panel_title = QLabel()
        self.panel_title.setProperty("role", "title")

        self.panel_text = QLabel()
        self.panel_text.setProperty("role", "muted")
        self.panel_text.setWordWrap(True)

        buttons = QHBoxLayout()

        self.retry_button = QPushButton()
        self.retry_button.clicked.connect(self.reload)

        self.panel_external_button = QPushButton()
        self.panel_external_button.setProperty("flat_style", True)
        self.panel_external_button.clicked.connect(lambda: open_external())

        self.compat_button = QPushButton()
        self.compat_button.setProperty("flat_style", True)
        self.compat_button.clicked.connect(self.compat_requested.emit)

        self.hide_button = QPushButton("✕")
        self.hide_button.setProperty("flat_style", True)
        self.hide_button.setFixedWidth(40)
        self.hide_button.clicked.connect(self.hide_panel)

        for button in (
            self.retry_button,
            self.panel_external_button,
            self.compat_button
        ):
            buttons.addWidget(button)

        buttons.addStretch()
        buttons.addWidget(self.hide_button)

        panel_layout.addWidget(self.panel_title)
        panel_layout.addWidget(self.panel_text)
        panel_layout.addLayout(buttons)

        self.panel.hide()

        layout.addWidget(self.panel)

        self.view_holder = QVBoxLayout()

        self.view_holder.setContentsMargins(0, 0, 0, 0)

        layout.addLayout(self.view_holder, 1)

        self.timeout_timer = QTimer(self)
        self.timeout_timer.setSingleShot(True)
        self.timeout_timer.setInterval(LOAD_TIMEOUT_MS)
        self.timeout_timer.timeout.connect(self.on_timeout)

        self.black_timer = QTimer(self)
        self.black_timer.setSingleShot(True)
        self.black_timer.setInterval(BLACK_CHECK_DELAY_MS)
        self.black_timer.timeout.connect(self.check_black)

        self.panel_kind = None

        self.retranslate()

    # ---------- texts ----------

    def retranslate(self):
        self.reload_button.setText(tr("map_reload"))
        self.external_button.setText(tr("web_open"))
        self.retry_button.setText(tr("map_retry"))
        self.panel_external_button.setText(tr("web_open"))
        self.compat_button.setText(tr("map_compat_button"))

        if self.panel_kind:
            self.show_panel(self.panel_kind)

        self.update_status()

    def update_status(self, progress=None):
        if self.view is None and self.panel_kind == "missing":
            text = ""
        elif self.loading:
            text = tr("map_loading")

            if progress:
                text += f" {progress}%"
        elif self.view is None:
            text = ""
        else:
            text = "squadcalc.app"

        if self.config.get("map_render") == "software":
            text += ("  ·  " if text else "") + tr("map_compat_on")

        self.status.setText(text)

    # ---------- loading ----------

    def ensure_loaded(self):
        """Create the browser on first use (it is heavy)."""
        if self.view is not None or self.panel_kind == "missing":
            return

        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
        except ImportError:
            self.show_panel("missing")
            self.update_status()
            return

        page_class = _make_page_classes()

        self.profile = shared_profile()

        self.view = QWebEngineView()

        self.page = page_class(self.profile, self.view)

        self.page.setBackgroundColor(QColor(theme.BG))

        self.view.setPage(self.page)

        self.page.loadStarted.connect(self.on_load_started)
        self.page.loadProgress.connect(self.on_load_progress)
        self.page.loadFinished.connect(self.on_load_finished)
        self.page.renderProcessTerminated.connect(self.on_render_crash)

        self.view_holder.addWidget(self.view)

        self.page.load(QUrl(SQUADCALC_URL))

    def reload(self):
        self.hide_panel()

        if self.view is None:
            self.ensure_loaded()
            return

        if self.page.url().isEmpty():
            self.page.load(QUrl(SQUADCALC_URL))
        else:
            self.page.triggerAction(self.page.WebAction.ReloadAndBypassCache)

    def on_load_started(self):
        self.loading = True

        self.black_timer.stop()

        self.timeout_timer.start()

        self.progress.setValue(0)

        self.progress.show()

        self.update_status()

    def on_load_progress(self, value):
        self.progress.setValue(value)

        self.update_status(value)

    def on_load_finished(self, ok):
        self.loading = False

        self.timeout_timer.stop()

        self.progress.hide()

        self.update_status()

        if ok:
            if self.panel_kind in ("slow", "failed", "crashed"):
                self.hide_panel()

            self.black_timer.start()
        else:
            self.show_panel("failed")

    def on_timeout(self):
        if self.loading:
            self.show_panel("slow")

    def on_render_crash(self, status, code):
        self.loading = False

        self.progress.hide()

        self.show_panel("crashed")

    def check_black(self):
        if self.view is None or not self.view.isVisible() or self.loading:
            return

        if looks_black(self.view.grab().toImage()):
            self.show_panel("black")

    def shutdown(self):
        """Destroy the page and the view now, before the profile.

        Left to the garbage collector at exit, Chromium objects can be torn
        down in the wrong order and crash the process while it closes.
        """
        self.timeout_timer.stop()
        self.black_timer.stop()

        if self.view is None:
            return

        from PyQt6 import sip

        view, page = self.view, self.page

        self.view = self.page = self.profile = None

        self.view_holder.removeWidget(view)

        sip.delete(page)

        sip.delete(view)

    # ---------- help panel ----------

    def show_panel(self, kind):
        self.panel_kind = kind

        self.panel_title.setText(tr(f"map_{kind}_title"))

        self.panel_text.setText(tr(f"map_{kind}_text"))

        self.retry_button.setVisible(kind != "missing")

        self.compat_button.setVisible(
            kind != "missing" and self.config.get("map_render") != "software"
        )

        self.panel.show()

    def hide_panel(self):
        self.panel_kind = None

        self.panel.hide()
