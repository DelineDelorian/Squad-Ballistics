import copy
import math
import os
import sys

import qtawesome as qta

from PyQt6.QtCore import (
    Qt,
    QProcess,
    QSize,
    QTimer,
    QUrl
)

from PyQt6.QtGui import (
    QDesktopServices,
    QGuiApplication,
    QIcon,
    QPixmap
)

from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget
)

import theme

from ballistics import (
    solve,
    screen_offset,
    trajectory
)

from config import (
    DEFAULT_CONFIG,
    DISTANCE_STEPS,
    RANGES,
    config_dir,
    load_config,
    save_config
)

from hotkeys import (
    ACTIONS,
    KEYS,
    setup_hotkeys,
    teardown_hotkeys
)

from i18n import (
    LANGUAGES,
    set_language,
    tr,
    weapon_note
)

from overlay import Overlay

from updater import CURRENT_VERSION

from utils import resource_path

from webmap import MapPage, open_external

from widgets import (
    CrosshairPreview,
    NumberEdit,
    Segmented,
    SliderRow,
    StatTile,
    Swatches,
    Toggle,
    TrajectoryView,
    WeaponPicker,
    card,
    format_angle,
    label,
    repolish
)

CROSSHAIR_COLORS = [
    "#00ff00",
    "#00ffff",
    "#ffff00",
    "#ff00ff",
    "#ff3030",
    "#ffffff",
]

PRESETS = {
    "classic": {
        "dot_enabled": True, "lines_enabled": True, "t_style": False,
        "circle_enabled": False, "dot_size": 3, "line_length": 14,
        "line_gap": 6, "line_thickness": 2,
    },
    "dot": {
        "dot_enabled": True, "lines_enabled": False,
        "circle_enabled": False, "dot_size": 4,
    },
    "circle": {
        "dot_enabled": True, "lines_enabled": False,
        "circle_enabled": True, "dot_size": 2, "circle_radius": 16,
    },
    "t": {
        "dot_enabled": False, "lines_enabled": True, "t_style": True,
        "circle_enabled": False, "line_length": 12, "line_gap": 5,
        "line_thickness": 2,
    },
    "cross": {
        "dot_enabled": False, "lines_enabled": True, "t_style": False,
        "circle_enabled": False, "line_length": 10, "line_gap": 0,
        "line_thickness": 2,
    },
}


def scrolled(widget, width=None):
    """Wrap a widget in a transparent vertical scroll area."""
    scroll = QScrollArea()

    scroll.setWidgetResizable(True)

    scroll.setFrameShape(QFrame.Shape.NoFrame)

    scroll.setHorizontalScrollBarPolicy(
        Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    )

    content = QWidget()

    content.setObjectName("scrollContent")

    layout = QVBoxLayout(content)

    layout.setContentsMargins(0, 0, 0, 0)

    layout.addWidget(widget)

    if width:
        # Room for the scrollbar so the content is never clipped.
        scroll.setFixedWidth(width + 14)

        layout.setContentsMargins(0, 0, 14, 0)

        layout.addStretch()

    scroll.setWidget(content)

    scroll.viewport().setAutoFillBackground(False)

    return scroll


class MainWindow(QMainWindow):
    def __init__(self, weapons):
        super().__init__()

        self.weapons = weapons

        self.config = load_config()

        set_language(self.config["language"])

        self.last_solution = None

        self.current_steps = []

        # Created once and kept across UI rebuilds, so the map is not
        # reloaded when the language or accent changes.
        self.map_page = None

        self.overlay = Overlay(
            self.config
        )

        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(400)
        self.save_timer.timeout.connect(
            lambda: save_config(self.config)
        )

        self.calc_timer = QTimer(self)
        self.calc_timer.setSingleShot(True)
        self.calc_timer.setInterval(120)
        self.calc_timer.timeout.connect(
            lambda: self.calculate(show_errors=False)
        )

        self.setWindowTitle("Squad Ballistics")

        icon_path = resource_path("assets/icon.ico")

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.resize(1180, 780)

        self.setMinimumSize(900, 600)

        if self.config["main_on_top"]:
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        self.build_ui()

        # Only after the UI exists: a hotkey may fire right away.
        setup_hotkeys(self)

    # =========================
    # LAYOUT
    # =========================

    @property
    def accent(self):
        return self.config.get("accent") or theme.ACCENTS[0]

    def build_ui(self):
        self.setStyleSheet(theme.stylesheet(self.accent))

        root = QWidget()

        root.setObjectName("root")

        layout = QHBoxLayout(root)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(0)

        self.controls = {}

        self.pages = QStackedWidget()

        self.pages.addWidget(self.build_calc_page())
        self.pages.addWidget(self.build_crosshair_page())
        self.pages.addWidget(self.build_settings_page())
        self.pages.addWidget(self.build_web_page())

        layout.addWidget(self.build_sidebar())
        layout.addWidget(self.pages)

        self.setCentralWidget(root)

        self.on_weapon_changed(self.picker.current, user=False)

    def rebuild(self):
        """Recreate the UI (language / accent change), keeping the inputs."""
        page = self.pages.currentIndex()

        texts = (
            self.distance_entry.text(),
            self.height_entry.text(),
            self.fov_entry.text()
        )

        if self.map_page is not None:
            # Detach the map so it survives the old pages being deleted.
            self.pages.removeWidget(self.map_page)
            self.map_page.setParent(None)

        self.build_ui()

        self.distance_entry.setText(texts[0])
        self.height_entry.setText(texts[1])
        self.fov_entry.setText(texts[2])

        self.set_page(page)

        self.recalculate_if_ready()

    def build_sidebar(self):
        sidebar = QFrame()

        sidebar.setObjectName("sidebar")

        sidebar.setFixedWidth(64)

        layout = QVBoxLayout(sidebar)

        layout.setContentsMargins(8, 14, 8, 14)

        layout.setSpacing(8)

        logo_path = resource_path("assets/icon.ico")

        if os.path.exists(logo_path):
            logo = label("")
            logo.setPixmap(
                QPixmap(logo_path).scaled(
                    32, 32,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo)
            layout.addSpacing(10)

        self.nav_buttons = []

        for index, (icon, key) in enumerate([
            ("fa5s.bullseye", "nav_calc"),
            ("fa5s.crosshairs", "nav_crosshair"),
            ("fa5s.sliders-h", "nav_settings"),
            ("fa5s.map", "nav_web")
        ]):
            button = QPushButton()

            button.setObjectName("nav")

            button.setIcon(qta.icon(icon, color=theme.TEXT))

            button.setIconSize(QSize(20, 20))

            button.setFixedSize(48, 44)

            button.setCheckable(True)

            button.setToolTip(tr(key))

            button.setCursor(Qt.CursorShape.PointingHandCursor)

            button.clicked.connect(
                lambda _checked, i=index: self.set_page(i)
            )

            layout.addWidget(button)

            self.nav_buttons.append(button)

        layout.addStretch()

        version = label(f"v{CURRENT_VERSION}", "small")

        version.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(version)

        self.nav_buttons[0].setChecked(True)

        return sidebar

    def set_page(self, index):
        if index == 3 and self.config["map_external"]:
            open_external()
            index = self.pages.currentIndex()

        self.pages.setCurrentIndex(index)

        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)

        if index == 3:
            self.map_page.ensure_loaded()

    # =========================
    # CALCULATOR PAGE
    # =========================

    def visible_weapons(self):
        show_mods = self.config["show_mods"]

        visible = {
            name: weapon
            for name, weapon in self.weapons.items()
            if show_mods or not weapon.mod
        }

        # A database with only mod weapons still has to show something.
        return visible or dict(self.weapons)

    def weapon_groups(self):
        groups = {}

        for name, weapon in self.visible_weapons().items():
            groups.setdefault(weapon.category, []).append(name)

        return list(groups.items())

    def recent_weapons(self):
        visible = self.visible_weapons()

        return [
            name for name in self.config["recent_weapons"]
            if name in visible
        ]

    def build_calc_page(self):
        page = QWidget()

        layout = QHBoxLayout(page)

        layout.setContentsMargins(24, 24, 24, 24)

        layout.setSpacing(18)

        layout.addWidget(self.build_target_card(), 0)
        layout.addWidget(self.build_solution_card(), 1)

        return scrolled(page)

    def build_target_card(self):
        frame, layout = card()

        frame.setFixedWidth(380)

        layout.addWidget(label(tr("target"), "title"))

        layout.addWidget(label(tr("weapon").upper(), "section"))

        self.picker = WeaponPicker()

        self.picker.set_data(self.weapon_groups(), self.recent_weapons())

        visible = self.visible_weapons()

        current = self.config["last_weapon"]

        if current not in visible:
            current = next(iter(visible))

        self.picker.set_current(current, emit=False)

        self.picker.changed.connect(self.on_weapon_changed)

        layout.addWidget(self.picker)

        self.weapon_info = label("", "small")

        self.weapon_info.setWordWrap(True)

        layout.addWidget(self.weapon_info)

        self.arc_control = Segmented(
            [
                ("auto", tr("arc_auto")),
                ("low", tr("arc_low")),
                ("high", tr("arc_high"))
            ],
            self.config["arc"]
        )

        self.arc_control.changed.connect(self.on_arc_changed)

        layout.addWidget(self.arc_control)

        self.distance_entry = NumberEdit(
            allow_negative=False,
            step=self.config["distance_step"]
        )

        self.height_entry = NumberEdit(allow_negative=True, step=1)

        self.height_entry.setPlaceholderText(tr("height_hint"))

        self.fov_entry = NumberEdit(allow_negative=False, step=1)

        self.fov_entry.setPlaceholderText(tr("fov_hint"))

        self.fov_entry.set_value(self.config["fov"])

        for caption, entry in (
            (tr("distance"), self.distance_entry),
            (tr("height"), self.height_entry),
            (tr("fov"), self.fov_entry)
        ):
            layout.addWidget(label(caption.upper(), "section"))

            layout.addWidget(entry)

            entry.textEdited.connect(self.on_input_edited)

            entry.stepped.connect(self.calc_timer.start)

            entry.returnPressed.connect(lambda: self.calculate())

        buttons = QHBoxLayout()

        self.calc_button = QPushButton(tr("calculate"))

        self.calc_button.clicked.connect(lambda: self.calculate())

        self.calc_button.setVisible(not self.config["auto_calc"])

        reset_button = QPushButton(tr("reset_aim"))

        reset_button.setProperty("flat_style", True)

        reset_button.clicked.connect(lambda: self.reset_offset())

        buttons.addWidget(self.calc_button, 2)
        buttons.addWidget(reset_button, 1)

        layout.addSpacing(4)
        layout.addLayout(buttons)

        layout.addStretch()

        hotkeys = self.config["hotkeys"]

        hints = [
            f"{hotkeys[action]} — {tr('hk_' + action)}"
            for action in ACTIONS
            if hotkeys.get(action)
        ]

        hint = label("   ·   ".join(hints), "small")

        hint.setWordWrap(True)

        layout.addWidget(hint)

        return frame

    def build_solution_card(self):
        frame, layout = card()

        header = QHBoxLayout()

        header.addWidget(label(tr("solution"), "title"))

        header.addStretch()

        self.solution_weapon = label("", "small")

        header.addWidget(self.solution_weapon)

        layout.addLayout(header)

        self.big_label = label(tr("ready"), "big")

        self.sub_label = label("", "sub")

        self.sub_label.setWordWrap(True)

        layout.addWidget(self.big_label)
        layout.addWidget(self.sub_label)

        grid = QGridLayout()

        grid.setSpacing(8)

        self.stats = {}

        for index, key in enumerate([
            "stat_tof",
            "stat_apex",
            "stat_impact",
            "stat_offset",
            "stat_velocity",
            "stat_alt"
        ]):
            tile = StatTile(tr(key))

            grid.addWidget(tile, index // 3, index % 3)

            self.stats[key] = tile

        layout.addLayout(grid)

        self.trajectory_view = TrajectoryView(self.accent)

        layout.addWidget(self.trajectory_view, 1)

        layout.addWidget(label(tr("how_to").upper(), "section"))

        self.steps_layout = QVBoxLayout()

        self.steps_layout.setSpacing(6)

        layout.addLayout(self.steps_layout)

        self.note_label = label("", "small")

        self.note_label.setWordWrap(True)

        layout.addWidget(self.note_label)

        return frame

    def current_weapon(self):
        return self.weapons.get(self.picker.current)

    def select_weapon(self, name):
        self.picker.set_current(name)

    def on_weapon_changed(self, name, user=True):
        weapon = self.weapons.get(name)

        if weapon is None:
            return

        if user:
            self.config["last_weapon"] = name

            recent = [n for n in self.config["recent_weapons"] if n != name]

            self.config["recent_weapons"] = [name] + recent[:4]

            self.picker.set_data(self.weapon_groups(), self.recent_weapons())

            self.schedule_save()

        self.update_weapon_info(weapon)

        self.solution_weapon.setText(name)

        self.recalculate_if_ready()

    def update_weapon_info(self, weapon):
        parts = [
            tr("chip_velocity", v=f"{weapon.velocity:g}"),
            tr("chip_gravity", g=f"{weapon.gravity:g}"),
        ]

        max_range = weapon.max_range()

        if math.isinf(max_range):
            parts.append(tr("chip_range_inf"))
        elif max_range < 5000:
            # Beyond that the number is a physics limit, not a useful range.
            parts.append(tr("chip_range", r=f"{max_range:.0f}"))

        if weapon.has_boost:
            parts.append(
                tr(
                    "chip_boost",
                    a=weapon.acceleration,
                    t=weapon.acceleration_time
                )
            )

        if weapon.min_distance:
            parts.append(tr("chip_min", m=f"{weapon.min_distance:g}"))

        if weapon.mod:
            parts.append(tr("chip_mod", mod=weapon.mod))

        self.weapon_info.setText("  ·  ".join(parts))

    def on_arc_changed(self, key):
        self.config["arc"] = key

        self.schedule_save()

        self.recalculate_if_ready()

    def on_input_edited(self, *_):
        if self.config["auto_calc"]:
            self.calc_timer.start()

    def recalculate_if_ready(self):
        if self.distance_entry.text().strip():
            self.calculate(show_errors=False)

    def primary_unit(self, weapon):
        mode = self.config["unit_mode"]

        if mode in ("deg", "mil"):
            return mode

        return weapon.unit

    def set_big(self, text, error=False):
        self.big_label.setText(text)

        self.big_label.setProperty("state", "error" if error else "")

        repolish(self.big_label)

    def status_text(self):
        return self.big_label.text()

    def clear_result(self, text=None, error=False):
        self.set_big(text or tr("ready"), error)

        self.sub_label.setText("")

        for tile in self.stats.values():
            tile.set("—")

        self.trajectory_view.clear()

        self.set_steps([])

        self.note_label.setText("")

    def set_steps(self, steps):
        self.current_steps = list(steps)

        # Detach the old rows right away; deleteLater alone would leave them
        # visible until the event loop runs.
        while self.steps_layout.count():
            widget = self.steps_layout.takeAt(0).widget()

            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

        for index, text in enumerate(steps, start=1):
            row = QWidget()

            row_layout = QHBoxLayout(row)

            row_layout.setContentsMargins(0, 0, 0, 0)

            row_layout.setSpacing(10)

            number = label(str(index), "step_num")

            row_layout.addWidget(number, 0, Qt.AlignmentFlag.AlignTop)

            body = label(text)

            body.setWordWrap(True)

            row_layout.addWidget(body, 1)

            self.steps_layout.addWidget(row)

    def read_inputs(self):
        distance = self.distance_entry.value()

        if distance is None:
            raise ValueError(tr("enter_distance"))

        if distance <= 0:
            raise ValueError(tr("bad_distance"))

        height = self.height_entry.value(0.0)

        fov = self.fov_entry.value()

        low, high = RANGES["fov"]

        if fov is None or not low <= fov <= high:
            raise ValueError(tr("bad_fov"))

        return distance, height, fov

    def calculate(self, show_errors=True):
        weapon = self.current_weapon()

        if weapon is None:
            return

        try:
            distance, height, fov = self.read_inputs()

            solution = solve(
                weapon,
                distance,
                height,
                self.config["arc"]
            )
        except ValueError as e:
            self.last_solution = None

            self.overlay.reset_offset()

            self.overlay.set_info("")

            if show_errors:
                self.clear_result(str(e), error=True)
            else:
                self.clear_result()

            return

        if self.config["fov"] != fov:
            self.config["fov"] = fov
            self.schedule_save()

        self.last_solution = solution

        if not solution.reachable:
            self.show_unreachable(weapon, solution)
            return

        self.show_solution(weapon, solution, fov)

    def show_unreachable(self, weapon, solution):
        self.overlay.reset_offset()

        self.overlay.set_info("")

        self.clear_result(tr("unreachable"), error=True)

        if solution.reason_code == "out_of_range":
            text = tr("how_unreachable_range", max=f"{weapon.max_range():.0f}")
        elif solution.reason_code == "too_close":
            text = tr("how_unreachable_close", min=f"{weapon.min_distance:g}")
        else:
            low, high = weapon.elevation_limits
            text = tr(
                "how_unreachable_limit",
                angle=f"{solution.angle:.1f}",
                low=f"{low:g}",
                high=f"{high:g}"
            )

        self.sub_label.setText(text)

    def show_solution(self, weapon, solution, fov):
        unit = self.primary_unit(weapon)
        other = "deg" if unit == "mil" else "mil"

        offset = self.current_offset()

        offscreen = self.overlay.is_offscreen(offset)

        self.overlay.set_offset(offset)

        self.overlay.set_info(
            f"{solution.distance:.0f} {tr('unit_m')}  ·  "
            f"{format_angle(solution.angle, unit)}"
        )

        self.set_big(format_angle(solution.angle, unit))

        self.sub_label.setText(format_angle(solution.angle, other))

        s = tr("unit_s")
        m = tr("unit_m")

        self.stats["stat_tof"].set(f"{solution.time_of_flight:.1f} {s}")
        self.stats["stat_apex"].set(f"{solution.apex:.0f} {m}")
        self.stats["stat_impact"].set(f"{solution.impact_angle:.1f}°")
        self.stats["stat_velocity"].set(
            f"{solution.velocity:.0f} {tr('unit_mps')}"
        )

        if offscreen:
            self.stats["stat_offset"].set(tr("off_screen"))
        else:
            self.stats["stat_offset"].set(f"{offset:.0f} {tr('unit_px')}")

        other_arc = "high" if solution.arc == "low" else "low"

        # The other arc only matters for weapons aimed by elevation; for
        # direct fire it is a useless near-vertical lob.
        alt = None

        if weapon.aim == "elevation":
            alt = solution.alternatives.get(other_arc)

            if alt is not None and abs(alt - solution.angle) < 0.01:
                alt = None

        alt_path = []

        if alt is None:
            self.stats["stat_alt"].set("—")
        else:
            self.stats["stat_alt"].set(format_angle(alt, unit))

            alt_path = trajectory(
                weapon,
                solve(weapon, solution.distance, solution.height_diff, other_arc)
            )

        self.trajectory_view.set_data(
            trajectory(weapon, solution),
            alt_path,
            (solution.distance, solution.height_diff)
        )

        angle_text = format_angle(solution.angle, unit)

        tof = f"{solution.time_of_flight:.1f}"

        if weapon.aim == "overlay":
            if offscreen:
                steps = [tr("how_overlay_offscreen", angle=angle_text)]
            else:
                toggle_key = self.config["hotkeys"].get("toggle_overlay")

                steps = [
                    tr("how_overlay_1", angle=angle_text),
                    tr("how_overlay_2", fov=f"{fov:g}")
                ]

                if toggle_key:
                    steps[0] = (
                        tr("how_overlay_on", hotkey=toggle_key)
                        + " " + steps[0]
                    )

            steps.append(
                tr(
                    "how_tof_moving",
                    tof=tof,
                    lead=f"{solution.time_of_flight * 10:.0f}"
                )
            )
        else:
            steps = [
                tr("how_elevation_1"),
                tr("how_elevation_2", angle=angle_text),
                tr("how_tof_adjust", tof=tof)
            ]

        self.set_steps(steps)

        self.note_label.setText(weapon_note(weapon))

    def current_offset(self):
        solution = self.last_solution

        if solution is None or not solution.reachable:
            return 0.0

        return screen_offset(
            solution.angle,
            self.config["fov"],
            self.overlay.screen_width(),
            self.config["offset_scale"] / 100
        )

    def reset_offset(self):
        self.last_solution = None

        self.overlay.reset_offset()

        self.overlay.set_info("")

        self.clear_result()

    def toggle_overlay(self):
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.show()

    def distance_up(self):
        self.distance_entry.add(self.config["distance_step"])
        self.calculate(show_errors=False)

    def distance_down(self):
        self.distance_entry.add(-self.config["distance_step"])
        self.calculate(show_errors=False)

    # =========================
    # CROSSHAIR PAGE
    # =========================

    def build_crosshair_page(self):
        page = QWidget()

        layout = QHBoxLayout(page)

        layout.setContentsMargins(24, 24, 24, 24)

        layout.setSpacing(18)

        settings, settings_layout = card()

        settings_layout.addWidget(label(tr("nav_crosshair"), "title"))

        settings_layout.addWidget(label(tr("shape").upper(), "section"))

        for text, key in [
            ("opt_dot", "dot_enabled"),
            ("opt_lines", "lines_enabled"),
            ("opt_t", "t_style"),
            ("opt_circle", "circle_enabled"),
        ]:
            self.add_toggle(settings_layout, tr(text), key)

        settings_layout.addWidget(label(tr("size").upper(), "section"))

        for text, key in [
            ("sl_dot", "dot_size"),
            ("sl_length", "line_length"),
            ("sl_gap", "line_gap"),
            ("sl_thickness", "line_thickness"),
            ("sl_circle", "circle_radius"),
        ]:
            self.add_slider(settings_layout, tr(text), key)

        settings_layout.addWidget(label(tr("effects").upper(), "section"))

        for text, key in [
            ("opt_outline", "outline_enabled"),
            ("opt_glow", "glow_enabled"),
            ("opt_animated", "animated"),
            ("opt_info", "info_enabled"),
        ]:
            self.add_toggle(settings_layout, tr(text), key)

        self.add_slider(settings_layout, tr("sl_outline"), "outline_thickness")

        outline_row = QHBoxLayout()

        outline_row.addWidget(label(tr("outline_color")))

        outline_row.addStretch()

        outline_control = Segmented(
            [("white", tr("white")), ("black", tr("black"))],
            self.config["outline_color"]
        )

        outline_control.changed.connect(
            lambda value: self.set_setting("outline_color", value)
        )

        outline_row.addWidget(outline_control)

        settings_layout.addLayout(outline_row)

        layout.addWidget(scrolled(settings, 380), 0)

        # Preview, presets and color
        side, side_layout = card()

        side_layout.addWidget(label(tr("preview"), "title"))

        self.preview = CrosshairPreview(self.config)

        side_layout.addWidget(self.preview, 1)

        side_layout.addWidget(label(tr("presets").upper(), "section"))

        presets = QHBoxLayout()

        for key in PRESETS:
            button = QPushButton(tr(f"preset_{key}"))

            button.setProperty("flat_style", True)

            button.clicked.connect(
                lambda _checked, k=key: self.apply_preset(k)
            )

            presets.addWidget(button)

        side_layout.addLayout(presets)

        side_layout.addWidget(label(tr("color").upper(), "section"))

        current_color = "#{:02x}{:02x}{:02x}".format(*self.config["color"])

        self.color_swatches = Swatches(CROSSHAIR_COLORS, current_color)

        self.color_swatches.picked.connect(self.pick_crosshair_color)

        side_layout.addWidget(self.color_swatches)

        for index, name in enumerate(("R", "G", "B")):
            self.add_slider(
                side_layout, name, ("color", index), limits=(0, 255)
            )

        self.add_slider(side_layout, tr("sl_opacity"), "opacity")

        layout.addWidget(side, 1)

        return page

    def add_toggle(self, layout, text, key, on_change=None):
        toggle = Toggle(text, self.accent, bool(self.get_setting(key)))

        def handle(checked):
            self.set_setting(key, checked)

            if on_change:
                on_change(checked)

        toggle.toggled.connect(handle)

        layout.addWidget(toggle)

        self.controls[key] = toggle

        return toggle

    def add_slider(self, layout, text, key, limits=None, on_change=None,
                   suffix=""):
        low, high = limits or RANGES[key]

        row = SliderRow(text, low, high, self.get_setting(key), suffix)

        def handle(value):
            self.set_setting(key, value)

            if on_change:
                on_change()

        row.changed.connect(handle)

        layout.addWidget(row)

        self.controls[key] = row

        return row

    def sync_controls(self):
        for key, control in self.controls.items():
            value = self.get_setting(key)

            control.blockSignals(True)

            if isinstance(control, Toggle):
                control.setChecked(bool(value))
                control.update()
            elif isinstance(control, SliderRow):
                control.slider.blockSignals(True)
                control.slider.setValue(int(value))
                control.update_label(control.slider.value())
                control.slider.blockSignals(False)

            control.blockSignals(False)

    def apply_preset(self, key):
        for name, value in PRESETS[key].items():
            self.config[name] = value

        self.sync_controls()

        self.refresh_crosshair()

    def pick_crosshair_color(self, color):
        color = color.lstrip("#")

        self.config["color"] = [int(color[i:i + 2], 16) for i in (0, 2, 4)]

        self.sync_controls()

        self.refresh_crosshair()

    def get_setting(self, key):
        if isinstance(key, tuple):
            name, index = key
            return self.config[name][index]

        return self.config[key]

    def set_setting(self, key, value):
        if isinstance(key, tuple):
            name, index = key
            self.config[name][index] = value
        else:
            self.config[key] = value

        self.refresh_crosshair()

    def refresh_crosshair(self):
        self.overlay.update()

        self.preview.update()

        self.color_swatches.set_current(
            "#{:02x}{:02x}{:02x}".format(*self.config["color"])
        )

        self.schedule_save()

    # =========================
    # SETTINGS PAGE
    # =========================

    def build_settings_page(self):
        page = QWidget()

        column = QVBoxLayout(page)

        column.setContentsMargins(24, 24, 24, 24)

        column.setSpacing(18)

        column.addWidget(self.build_interface_card())
        column.addWidget(self.build_calc_settings_card())
        column.addWidget(self.build_overlay_card())
        column.addWidget(self.build_map_card())
        column.addWidget(self.build_hotkeys_card())
        column.addWidget(self.build_about_card())

        column.addStretch()

        wrapper = QWidget()

        outer = QHBoxLayout(wrapper)

        outer.setContentsMargins(0, 0, 0, 0)

        page.setMaximumWidth(640)

        outer.addStretch()

        outer.addWidget(page, 1)

        outer.addStretch()

        return scrolled(wrapper)

    def setting_row(self, layout, text, widget):
        row = QHBoxLayout()

        row.addWidget(label(text))

        row.addStretch()

        row.addWidget(widget)

        layout.addLayout(row)

    def combo(self, items, current, on_change):
        box = QComboBox()

        for value, text in items:
            box.addItem(text, value)

        index = box.findData(current)

        box.setCurrentIndex(max(0, index))

        box.setMinimumWidth(180)

        box.currentIndexChanged.connect(
            lambda _i: on_change(box.currentData())
        )

        return box

    def build_interface_card(self):
        frame, layout = card()

        layout.addWidget(label(tr("s_interface"), "title"))

        languages = [("auto", tr("s_lang_auto"))] + list(LANGUAGES.items())

        self.setting_row(
            layout,
            tr("s_language"),
            self.combo(languages, self.config["language"], self.set_language)
        )

        accent_row = QHBoxLayout()

        accent_row.addWidget(label(tr("s_accent")))

        accent_row.addStretch()

        swatches = Swatches(theme.ACCENTS, self.accent)

        swatches.picked.connect(self.set_accent)

        accent_row.addWidget(swatches)

        layout.addLayout(accent_row)

        self.add_toggle(
            layout,
            tr("s_on_top"),
            "main_on_top",
            self.set_on_top
        )

        return frame

    def build_calc_settings_card(self):
        frame, layout = card()

        layout.addWidget(label(tr("s_calc"), "title"))

        units = Segmented(
            [
                ("auto", tr("s_units_auto")),
                ("deg", tr("s_units_deg")),
                ("mil", tr("s_units_mil"))
            ],
            self.config["unit_mode"]
        )

        units.changed.connect(self.set_unit_mode)

        self.setting_row(layout, tr("s_units"), units)

        self.setting_row(
            layout,
            tr("s_step"),
            self.combo(
                [(step, f"{step} {tr('unit_m')}") for step in DISTANCE_STEPS],
                self.config["distance_step"],
                self.set_distance_step
            )
        )

        self.add_toggle(
            layout,
            tr("s_auto_calc"),
            "auto_calc",
            lambda checked: self.calc_button.setVisible(not checked)
        )

        self.add_toggle(
            layout,
            tr("s_mods"),
            "show_mods",
            lambda _checked: self.refresh_weapon_list()
        )

        return frame

    def build_overlay_card(self):
        frame, layout = card()

        layout.addWidget(label(tr("s_overlay"), "title"))

        screens = [
            (index, f"{index + 1}: {screen.name()} "
                    f"({screen.geometry().width()}×{screen.geometry().height()})")
            for index, screen in enumerate(QGuiApplication.screens())
        ]

        self.setting_row(
            layout,
            tr("s_monitor"),
            self.combo(screens, self.config["monitor"], self.set_monitor)
        )

        # Moving the center changes what counts as off-screen.
        self.add_slider(
            layout, tr("s_offset_x"), "center_offset_x",
            on_change=self.recalculate_if_ready,
            suffix=f" {tr('unit_px')}"
        )

        self.add_slider(
            layout, tr("s_offset_y"), "center_offset_y",
            on_change=self.recalculate_if_ready,
            suffix=f" {tr('unit_px')}"
        )

        self.add_slider(
            layout, tr("s_calibration"), "offset_scale",
            on_change=self.recalculate_if_ready, suffix="%"
        )

        return frame

    def build_hotkeys_card(self):
        frame, layout = card()

        layout.addWidget(label(tr("s_hotkeys"), "title"))

        keys = [("", tr("hk_none"))] + [(key, key) for key in KEYS]

        for action in ACTIONS:
            self.setting_row(
                layout,
                tr(f"hk_{action}"),
                self.combo(
                    keys,
                    self.config["hotkeys"].get(action, ""),
                    lambda key, a=action: self.set_hotkey(a, key)
                )
            )

        hint = label(tr("s_hotkeys_hint"), "small")

        hint.setWordWrap(True)

        layout.addWidget(hint)

        return frame

    def build_about_card(self):
        frame, layout = card()

        layout.addWidget(label(tr("s_about"), "title"))

        layout.addWidget(label(tr("s_version", v=CURRENT_VERSION), "muted"))

        row = QHBoxLayout()

        open_button = QPushButton(tr("s_open_config"))

        open_button.setProperty("flat_style", True)

        open_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(config_dir()))
        )

        reset_button = QPushButton(tr("s_reset"))

        reset_button.setProperty("flat_style", True)

        reset_button.clicked.connect(self.reset_settings)

        row.addWidget(open_button)
        row.addWidget(reset_button)
        row.addStretch()

        layout.addLayout(row)

        return frame

    def set_language(self, code):
        self.config["language"] = code

        set_language(code)

        self.schedule_save()

        self.rebuild()

    def set_accent(self, color):
        self.config["accent"] = color

        self.schedule_save()

        self.rebuild()

    def set_on_top(self, checked):
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, checked)

        self.show()

    def set_unit_mode(self, mode):
        self.config["unit_mode"] = mode

        self.schedule_save()

        self.recalculate_if_ready()

    def set_distance_step(self, step):
        self.config["distance_step"] = step

        self.distance_entry.step = step

        self.schedule_save()

    def set_monitor(self, index):
        self.config["monitor"] = index

        self.overlay.move_to_screen()

        self.schedule_save()

        self.recalculate_if_ready()

    def set_hotkey(self, action, key):
        teardown_hotkeys(self)

        # A key can only do one thing.
        for other, bound in self.config["hotkeys"].items():
            if key and bound == key and other != action:
                self.config["hotkeys"][other] = ""

        self.config["hotkeys"][action] = key

        setup_hotkeys(self)

        self.schedule_save()

        self.rebuild()

    def refresh_weapon_list(self):
        visible = self.visible_weapons()

        self.picker.set_data(self.weapon_groups(), self.recent_weapons())

        if self.picker.current not in visible:
            self.picker.set_current(next(iter(visible)))

    def reset_settings(self):
        answer = QMessageBox.question(
            self,
            "Squad Ballistics",
            tr("s_reset_confirm")
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        teardown_hotkeys(self)

        # The overlay keeps a reference to this dict, so update it in place.
        self.config.clear()

        self.config.update(copy.deepcopy(DEFAULT_CONFIG))

        set_language(self.config["language"])

        setup_hotkeys(self)

        self.overlay.move_to_screen()

        self.set_on_top(False)

        save_config(self.config)

        self.rebuild()

    def schedule_save(self):
        self.save_timer.start()

    # =========================
    # MAP PAGE
    # =========================

    def build_web_page(self):
        if self.map_page is None:
            self.map_page = MapPage(self.config)

            self.map_page.compat_requested.connect(
                lambda: self.set_map_render("software")
            )
        else:
            self.map_page.retranslate()

        return self.map_page

    def build_map_card(self):
        frame, layout = card()

        layout.addWidget(label(tr("s_map"), "title"))

        render = Segmented(
            [
                ("auto", tr("s_map_render_auto")),
                ("software", tr("s_map_render_software"))
            ],
            self.config["map_render"]
        )

        render.changed.connect(self.set_map_render)

        self.setting_row(layout, tr("s_map_render"), render)

        hint = label(tr("s_map_render_hint"), "small")

        hint.setWordWrap(True)

        layout.addWidget(hint)

        self.add_toggle(layout, tr("s_map_external"), "map_external")

        clear_button = QPushButton(tr("s_map_clear"))

        clear_button.setProperty("flat_style", True)

        def clear_cache():
            profile = self.map_page.profile if self.map_page else None

            if profile is not None:
                profile.clearHttpCache()

            clear_button.setText(tr("s_map_cleared"))

        clear_button.clicked.connect(clear_cache)

        row = QHBoxLayout()

        row.addWidget(clear_button)

        row.addStretch()

        layout.addLayout(row)

        return frame

    def set_map_render(self, mode):
        if mode == self.config["map_render"]:
            return

        self.config["map_render"] = mode

        save_config(self.config)

        answer = QMessageBox.question(
            self,
            tr("restart_title"),
            tr("restart_text")
        )

        if answer == QMessageBox.StandardButton.Yes:
            self.restart()
        else:
            self.rebuild()

    def restart(self):
        """Start a new instance and quit (Chromium flags need a restart)."""
        if getattr(sys, "frozen", False):
            program, arguments = sys.executable, sys.argv[1:]
        else:
            program = sys.executable
            arguments = [os.path.abspath(sys.argv[0])] + sys.argv[1:]

        self.close()

        QProcess.startDetached(program, arguments)

        QApplication.quit()

    def closeEvent(self, event):
        if self.save_timer.isActive():
            self.save_timer.stop()

        save_config(self.config)

        teardown_hotkeys(self)

        if self.map_page is not None:
            self.map_page.shutdown()

        self.overlay.close()

        event.accept()
