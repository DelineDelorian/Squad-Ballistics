import os

import pytest

pytest.importorskip("PyQt6.QtWidgets")
pytest.importorskip("qtawesome")

from PyQt6.QtWidgets import QApplication

import config
from ballistics import load_weapons, solve
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
    win.config["animated"] = False
    yield win
    win.close()


def reachable_distance(weapon):
    for fraction in (0.3, 0.6, 0.85):
        distance = max(
            weapon.min_distance + 5,
            min(weapon.max_range() * fraction, 1500)
        )
        if solve(weapon, distance).reachable:
            return distance


def test_every_weapon_through_ui(window):
    for name, weapon in window.weapons.items():
        window.select_weapon(name)

        distance = reachable_distance(weapon)

        window.distance_entry.setText(f"{distance:.0f}")
        window.height_entry.setText("")
        window.fov_entry.setText("90")
        window.calculate()

        assert window.last_solution is not None, name
        assert window.last_solution.reachable, (name, window.status_text())
        assert any(c in window.status_text() for c in ("°", "mil", "мил"))
        assert window.steps_layout.count() >= 2, name

        expected = window.current_offset()
        if abs(expected) < window.overlay.height():
            assert window.overlay.offset == pytest.approx(expected), name


def test_comma_decimal_and_errors(window):
    window.select_weapon("SPG-9 · HEAT")

    window.distance_entry.setText("350,5")
    window.height_entry.setText("-3,5")
    window.calculate()
    assert window.last_solution.distance == pytest.approx(350.5)
    assert window.last_solution.height_diff == pytest.approx(-3.5)

    window.distance_entry.setText("")
    window.calculate()
    assert window.last_solution is None
    assert window.big_label.property("state") == "error"

    window.distance_entry.setText("100000")
    window.calculate()
    assert not window.last_solution.reachable
    assert window.overlay.target_offset == 0


def test_reset_toggle_and_distance_keys(window):
    window.select_weapon("SPG-9 · HEAT")
    window.distance_entry.setText("500")
    window.calculate()
    assert window.overlay.target_offset > 0
    assert "500 m" in window.overlay.info_text

    window.config["distance_step"] = 25
    window.distance_up()
    assert window.last_solution.distance == 525
    window.distance_down()
    window.distance_down()
    assert window.last_solution.distance == 475

    window.reset_offset()
    assert window.overlay.target_offset == 0
    assert window.overlay.info_text == ""

    visible = window.overlay.isVisible()
    window.toggle_overlay()
    assert window.overlay.isVisible() != visible


def test_unit_mode_and_arc(window):
    window.select_weapon("Mortar (M252 / 2B14 / L16 / Type 63)")
    window.distance_entry.setText("800")
    window.calculate()
    assert "mil" in window.status_text() or "мил" in window.status_text()

    window.set_unit_mode("deg")
    assert "°" in window.status_text()

    window.on_arc_changed("low")
    assert not window.last_solution.reachable


def test_mods_hidden_by_default(window):
    mods = [n for n, w in window.weapons.items() if w.mod]
    assert mods

    assert not any(n in window.visible_weapons() for n in mods)

    window.config["show_mods"] = True
    assert all(n in window.visible_weapons() for n in mods)


def test_recent_weapons(window):
    window.select_weapon("RPG-29")
    window.select_weapon("AT-4")

    assert window.config["recent_weapons"][:2] == ["AT-4", "RPG-29"]
    assert window.config["last_weapon"] == "AT-4"


def test_presets_and_colors(window):
    window.apply_preset("circle")
    assert window.config["circle_enabled"] is True
    assert window.controls["circle_enabled"].isChecked()

    window.pick_crosshair_color("#ff00ff")
    assert window.config["color"] == [255, 0, 255]
    assert window.controls[("color", 1)].slider.value() == 0

    window.set_setting(("color", 2), 200)
    assert window.config["color"][2] == 200

    for key in ("circle_enabled", "glow_enabled", "lines_enabled",
                "outline_enabled"):
        window.set_setting(key, True)
    window.set_setting("outline_color", "black")
    window.overlay.repaint()
    window.preview.repaint()

    # Off-screen aim point is drawn as an edge arrow.
    window.overlay.set_offset(1e9)
    window.overlay.repaint()


def test_language_and_accent_rebuild(window):
    window.select_weapon("SPG-9 · HEAT")
    window.distance_entry.setText("400")
    window.calculate()

    window.set_language("en")
    assert window.distance_entry.text() == "400"
    assert window.last_solution.reachable

    window.set_language("ru")
    window.set_accent("#22c55e")
    assert window.config["accent"] == "#22c55e"
    assert window.distance_entry.text() == "400"


def test_hotkey_rebinding(window):
    window.set_hotkey("distance_up", "PgUp")
    assert window.config["hotkeys"]["distance_up"] == "PgUp"

    # Binding a key that is already used moves it.
    window.set_hotkey("reset_offset", "PgUp")
    assert window.config["hotkeys"]["reset_offset"] == "PgUp"
    assert window.config["hotkeys"]["distance_up"] == ""
