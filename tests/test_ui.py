import os

import pytest

pytest.importorskip("PyQt6.QtWidgets")
pytest.importorskip("qtawesome")

from PyQt6.QtWidgets import QApplication

import config
from ballistics import load_weapons
from conftest import ROOT


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def window(app, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config, "CONFIG_PATH", str(tmp_path / "config.json"))

    from crosshair import MainWindow

    win = MainWindow(load_weapons(os.path.join(ROOT, "weapons.json")))
    win.overlay.config["animated"] = False
    yield win
    win.close()


def select(window, name):
    window.weapon_box.setCurrentIndex(window.weapon_box.findData(name))


def test_every_weapon_through_ui(window):
    for name, weapon in window.weapons.items():
        select(window, name)

        distance = max(weapon.min_distance + 5, weapon.max_range() * 0.3)

        window.distance_entry.setText(f"{distance:.0f}")
        window.height_entry.setText("")
        window.fov_entry.setText("90")
        window.calculate()

        assert window.last_solution is not None, name
        assert window.last_solution.reachable, (
            name, window.details_label.text()
        )
        assert "°" in window.result_label.text(), name

        expected = window.current_offset()
        if abs(expected) < window.overlay.height():
            assert window.overlay.offset == pytest.approx(expected), name


def test_comma_decimal_and_errors(window):
    select(window, "SPG-9")

    window.distance_entry.setText("350,5")
    window.height_entry.setText("-3,5")
    window.calculate()
    assert window.last_solution.distance == pytest.approx(350.5)
    assert window.last_solution.height_diff == pytest.approx(-3.5)

    window.distance_entry.setText("")
    window.calculate()
    assert "distance" in window.result_label.text().lower()

    window.distance_entry.setText("100000")
    window.calculate()
    assert window.result_label.text() == "Unreachable"
    assert window.overlay.target_offset == 0


def test_reset_and_toggle(window):
    select(window, "SPG-9")
    window.distance_entry.setText("500")
    window.calculate()
    assert window.overlay.target_offset > 0

    window.reset_offset()
    assert window.overlay.target_offset == 0

    visible = window.overlay.isVisible()
    window.toggle_overlay()
    assert window.overlay.isVisible() != visible


def test_settings_update_config(window):
    window.set_setting(("color", 2), 200)
    assert window.config["color"][2] == 200

    window.set_setting("t_style", True)
    assert window.overlay.config["t_style"] is True

    # Paint every element without crashing.
    for key in ("circle_enabled", "glow_enabled", "lines_enabled"):
        window.set_setting(key, True)
    window.overlay.repaint()

    # Off-screen aim point is drawn as an edge arrow.
    window.overlay.set_offset(1e9)
    window.overlay.repaint()
