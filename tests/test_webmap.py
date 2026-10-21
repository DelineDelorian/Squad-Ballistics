import pytest

pytest.importorskip("PyQt6.QtGui")

from PyQt6.QtGui import QColor, QImage

import webmap


def flags_of(text):
    return text.split()


def disabled_features(text):
    for flag in flags_of(text):
        if flag.startswith("--disable-features="):
            return flag.split("=", 1)[1].split(",")
    return []


def test_network_flags_always_on():
    flags = webmap.chromium_flags("auto")

    assert "--disable-quic" in flags_of(flags)
    for feature in ("EncryptedClientHello", "DnsOverHttps", "UseDnsHttpsSvcbAlpn"):
        assert feature in disabled_features(flags)

    assert "--disable-gpu" not in flags_of(flags)


def test_software_mode_disables_gpu():
    flags = flags_of(webmap.chromium_flags("software"))

    assert "--disable-gpu" in flags
    assert "--disable-gpu-compositing" in flags


def test_user_flags_are_kept_and_merged():
    flags = webmap.chromium_flags(
        "auto",
        "--lang=ru --disable-features=Foo,Bar --disable-quic"
    )

    assert flags_of(flags).count("--disable-quic") == 1
    assert "--lang=ru" in flags_of(flags)
    assert disabled_features(flags)[:2] == ["Foo", "Bar"]
    assert sum(f.startswith("--disable-features=") for f in flags_of(flags)) == 1


def test_configure_environment_survives_restarts():
    env = {"QTWEBENGINE_CHROMIUM_FLAGS": "--lang=ru"}

    webmap.configure_environment("software", env)
    assert "--disable-gpu" in env["QTWEBENGINE_CHROMIUM_FLAGS"]
    assert env["QT_QUICK_BACKEND"] == "software"

    # A restarted app inherits the environment; switching back must not
    # keep the software flags from the previous run.
    child = dict(env)
    webmap.configure_environment("auto", child)

    assert "--disable-gpu" not in child["QTWEBENGINE_CHROMIUM_FLAGS"]
    assert "--lang=ru" in child["QTWEBENGINE_CHROMIUM_FLAGS"]
    assert "QT_QUICK_BACKEND" not in child

    # Running it again does not duplicate anything.
    webmap.configure_environment("auto", child)
    assert flags_of(child["QTWEBENGINE_CHROMIUM_FLAGS"]).count("--disable-quic") == 1


def test_user_quick_backend_is_restored():
    env = {"QT_QUICK_BACKEND": "opengl"}

    webmap.configure_environment("software", env)
    assert env["QT_QUICK_BACKEND"] == "software"

    webmap.configure_environment("auto", env)
    assert env["QT_QUICK_BACKEND"] == "opengl"


def image(color, size=(200, 100)):
    img = QImage(size[0], size[1], QImage.Format.Format_RGB32)
    img.fill(QColor(color))
    return img


def test_looks_black():
    assert webmap.looks_black(image("#000000"))
    assert webmap.looks_black(image("#050505"))
    assert not webmap.looks_black(image("#1a2130"))
    assert not webmap.looks_black(QImage())

    # A dark page with some content (UI, map) is not "black".
    img = image("#000000")
    for x in range(0, 200):
        for y in range(0, 20):
            img.setPixelColor(x, y, QColor("#3b82f6"))
    assert not webmap.looks_black(img)


def test_profile_cache_lives_in_user_data_dir():
    pytest.importorskip("PyQt6.QtWebEngineCore")

    from config import data_dir

    profile = webmap.shared_profile()

    assert not profile.isOffTheRecord()
    assert profile.cachePath().startswith(data_dir())
    assert profile.persistentStoragePath().startswith(data_dir())
    assert profile.httpCacheMaximumSize() >= 256 * 1024 * 1024


def test_shutdown_is_safe_and_idempotent():
    pytest.importorskip("PyQt6.QtWebEngineWidgets")

    page = webmap.MapPage({"accent": "#3b82f6", "map_render": "auto"})
    page.ensure_loaded()
    assert page.view is not None

    page.shutdown()
    page.shutdown()
    assert page.view is None and page.profile is None

    # The shared profile is reused, never recreated.
    assert webmap.shared_profile() is webmap.shared_profile()
