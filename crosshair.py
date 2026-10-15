import os

import qtawesome as qta

from PyQt6.QtCore import (
    Qt,
    QSize,
    QUrl,
    QTimer,
    QRegularExpression
)

from PyQt6.QtGui import (
    QFont,
    QIcon,
    QDesktopServices,
    QRegularExpressionValidator
)

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QStackedWidget,
    QFrame,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QScrollArea
)

from ballistics import (
    solve,
    screen_offset
)

from config import (
    load_config,
    save_config
)

from hotkeys import (
    setup_hotkeys,
    teardown_hotkeys
)

from overlay import Overlay

from utils import resource_path

SQUADCALC_URL = "https://squadcalc.app/?map=AlBasrah"

ARC_OPTIONS = [
    ("auto", "Arc: weapon default"),
    ("low", "Low arc (direct)"),
    ("high", "High arc (indirect)")
]

BUTTON_STYLE = """
QPushButton {
    background-color: rgba(35,40,50,220);
    border-radius: 14px;
    border: none;
}

QPushButton:hover {
    background-color: rgba(55,60,75,220);
}

QPushButton:checked {
    background-color: #3b82f6;
}
"""

SECONDARY_BUTTON_STYLE = """
QPushButton {
    background-color: rgba(35,40,50,220);
    border: 1px solid #2d3440;
}

QPushButton:hover {
    background-color: rgba(55,60,75,220);
}
"""

CARD_STYLE = """
QFrame#card {
    background-color: rgba(25,30,40,220);
    border-radius: 20px;
}
"""

OK_COLOR = "#00ff88"
ERROR_COLOR = "#ff5c5c"
MUTED_COLOR = "#8b93a7"


def number_validator(allow_negative):
    sign = "-?" if allow_negative else ""

    return QRegularExpressionValidator(
        QRegularExpression(rf"^{sign}\d{{0,6}}([.,]\d{{0,3}})?$")
    )


def parse_number(text, name, default=None):
    text = text.strip().replace(",", ".")

    if not text or text in ("-", "."):
        if default is not None:
            return default
        raise ValueError(f"Enter {name}")

    try:
        return float(text)
    except ValueError:
        raise ValueError(f"{name.capitalize()} must be a number")


class MainWindow(QMainWindow):
    def __init__(self, weapons):
        super().__init__()

        self.weapons = weapons

        self.config = load_config()

        self.last_solution = None

        self.overlay = Overlay(
            self.config
        )

        self.save_timer = QTimer(self)

        self.save_timer.setSingleShot(True)

        self.save_timer.setInterval(400)

        self.save_timer.timeout.connect(
            lambda: save_config(self.config)
        )

        setup_hotkeys(self)

        self.setWindowTitle(
            "Squad Ballistics"
        )

        icon_path = resource_path("assets/icon.ico")

        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.resize(1400, 850)

        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(
                    x1:0,
                    y1:0,
                    x2:1,
                    y2:1,
                    stop:0 #0b1018,
                    stop:1 #121826
                );
            }

            QWidget {
                color: white;
                font-family: Segoe UI;
                font-size: 14px;
            }

            QLabel {
                color: white;
                background: transparent;
            }

            QLineEdit {
                background-color: rgba(35,40,50,220);
                border: 1px solid #2d3440;
                border-radius: 12px;
                padding: 12px;
                color: white;
            }

            QComboBox {
                background-color: rgba(35,40,50,220);
                border: 1px solid #2d3440;
                border-radius: 12px;
                padding: 12px;
                color: white;
            }

            QComboBox QAbstractItemView {
                background-color: #1a1f2a;
                selection-background-color: #3b82f6;
            }

            QPushButton {
                background-color: #3b82f6;
                border: none;
                border-radius: 12px;
                padding: 12px;
                color: white;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #2563eb;
            }

            QSlider::groove:horizontal {
                height: 6px;
                background: #252a33;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: #3b82f6;
                width: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }

            QCheckBox {
                spacing: 10px;
                color: white;
                font-size: 14px;
                background: transparent;
            }

            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }

            QCheckBox::indicator:unchecked {
                border-radius: 6px;
                border: 2px solid #3b82f6;
                background: transparent;
            }

            QCheckBox::indicator:checked {
                border-radius: 6px;
                border: 2px solid #3b82f6;
                background: #3b82f6;
            }

            QScrollArea {
                background: transparent;
                border: none;
            }

            QWidget#scrollContent {
                background: transparent;
            }

            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                margin: 4px;
            }

            QScrollBar::handle:vertical {
                background: #2d3440;
                border-radius: 3px;
                min-height: 30px;
            }

            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
                height: 0;
            }
        """ + CARD_STYLE)

        root = QWidget()

        self.setCentralWidget(root)

        layout = QHBoxLayout(root)

        layout.setContentsMargins(0, 0, 0, 0)

        self.pages = QStackedWidget()

        self.pages.addWidget(self.build_main_page())
        self.pages.addWidget(self.build_settings_page())
        self.pages.addWidget(self.build_web_page())

        layout.addWidget(self.build_sidebar())
        layout.addWidget(self.pages)

        self.update_weapon_info()

    # =========================
    # SIDEBAR
    # =========================

    def build_sidebar(self):
        sidebar = QFrame()

        sidebar.setFixedWidth(70)

        sidebar.setStyleSheet("""
            background-color: rgba(15,18,24,240);
        """)

        sidebar_layout = QVBoxLayout(sidebar)

        sidebar_layout.setContentsMargins(
            10,
            20,
            10,
            20
        )

        sidebar_layout.setSpacing(18)

        self.sidebar_buttons = []

        for index, (icon, tooltip) in enumerate([
            ("fa5s.home", "Ballistics"),
            ("fa5s.crosshairs", "Crosshair"),
            ("fa5s.globe", "SquadCalc")
        ]):
            btn = QPushButton()

            btn.setIcon(
                qta.icon(
                    icon,
                    color="white"
                )
            )

            btn.setIconSize(
                QSize(24, 24)
            )

            btn.setFixedSize(52, 52)

            btn.setCheckable(True)

            btn.setToolTip(tooltip)

            btn.setStyleSheet(
                BUTTON_STYLE
            )

            btn.clicked.connect(
                lambda _checked, i=index: self.set_page(i)
            )

            sidebar_layout.addWidget(btn)

            self.sidebar_buttons.append(btn)

        sidebar_layout.addStretch()

        self.sidebar_buttons[0].setChecked(True)

        return sidebar

    def set_page(self, index):
        self.pages.setCurrentIndex(index)

        for i, btn in enumerate(self.sidebar_buttons):
            btn.setChecked(i == index)

        if index == 2:
            self.load_web_page()

    # =========================
    # MAIN PAGE
    # =========================

    def make_card(self):
        card = QFrame()

        card.setObjectName("card")

        card.setFixedWidth(440)

        card_layout = QVBoxLayout(card)

        card_layout.setContentsMargins(
            24,
            24,
            24,
            24
        )

        return card, card_layout

    def build_main_page(self):
        main_page = QWidget()

        main_layout = QVBoxLayout(main_page)

        main_layout.addStretch()

        container, container_layout = self.make_card()

        container_layout.setSpacing(12)

        title = QLabel(
            "BALLISTICS"
        )

        title.setFont(
            QFont(
                "Segoe UI",
                18,
                QFont.Weight.Bold
            )
        )

        self.weapon_box = QComboBox()

        self.populate_weapons()

        self.weapon_box.currentIndexChanged.connect(
            self.on_weapon_changed
        )

        self.weapon_info = QLabel()

        self.weapon_info.setWordWrap(True)

        self.weapon_info.setStyleSheet(
            f"color: {MUTED_COLOR}; font-size: 12px;"
        )

        self.arc_box = QComboBox()

        for key, label in ARC_OPTIONS:
            self.arc_box.addItem(label, key)

        arc_index = self.arc_box.findData(
            self.config.get("arc", "auto")
        )

        self.arc_box.setCurrentIndex(max(0, arc_index))

        self.arc_box.currentIndexChanged.connect(
            self.on_arc_changed
        )

        self.distance_entry = QLineEdit()

        self.distance_entry.setPlaceholderText(
            "Distance to target"
        )

        self.distance_entry.setValidator(
            number_validator(allow_negative=False)
        )

        self.height_entry = QLineEdit()

        self.height_entry.setPlaceholderText(
            "0  (target higher = +, lower = −)"
        )

        self.height_entry.setValidator(
            number_validator(allow_negative=True)
        )

        self.fov_entry = QLineEdit()

        self.fov_entry.setPlaceholderText(
            "Horizontal FOV (in-game setting / zoomed)"
        )

        self.fov_entry.setValidator(
            number_validator(allow_negative=False)
        )

        self.fov_entry.setText(
            f"{self.config['fov']:g}"
        )

        for entry in (
            self.distance_entry,
            self.height_entry,
            self.fov_entry
        ):
            entry.returnPressed.connect(lambda: self.calculate())

        calc_btn = QPushButton(
            "CALCULATE"
        )

        calc_btn.setFixedHeight(42)

        calc_btn.clicked.connect(
            lambda: self.calculate()
        )

        reset_btn = QPushButton(
            "RESET AIM"
        )

        reset_btn.setFixedHeight(42)

        reset_btn.setStyleSheet(SECONDARY_BUTTON_STYLE)

        reset_btn.clicked.connect(
            lambda: self.reset_offset()
        )

        buttons = QHBoxLayout()

        buttons.addWidget(calc_btn, 2)
        buttons.addWidget(reset_btn, 1)

        self.result_label = QLabel(
            "Ready"
        )

        self.result_label.setStyleSheet(f"""
            color: {OK_COLOR};
            font-size: 18px;
            font-weight: bold;
        """)

        self.details_label = QLabel()

        self.details_label.setWordWrap(True)

        self.details_label.setStyleSheet(
            f"color: {MUTED_COLOR}; font-size: 12px;"
        )

        hint = QLabel(
            "F8 — overlay on/off   ·   F9 — reset aim"
        )

        hint.setStyleSheet(
            f"color: {MUTED_COLOR}; font-size: 11px;"
        )

        container_layout.addWidget(title)
        container_layout.addWidget(self.weapon_box)
        container_layout.addWidget(self.weapon_info)
        container_layout.addWidget(self.arc_box)
        for caption, entry in (
            ("Distance, m", self.distance_entry),
            ("Height, m", self.height_entry),
            ("FOV", self.fov_entry)
        ):
            container_layout.addLayout(
                self.labelled_row(caption, entry)
            )
        container_layout.addLayout(buttons)
        container_layout.addWidget(self.result_label)
        container_layout.addWidget(self.details_label)
        container_layout.addWidget(hint)

        main_layout.addWidget(
            container,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        main_layout.addStretch()

        return main_page

    def labelled_row(self, caption, widget):
        row = QHBoxLayout()

        label = QLabel(caption)

        label.setFixedWidth(100)

        label.setStyleSheet(f"color: {MUTED_COLOR};")

        row.addWidget(label)
        row.addWidget(widget)

        return row

    def populate_weapons(self):
        """Fill the weapon list grouped by category."""
        groups = {}

        for name, weapon in self.weapons.items():
            groups.setdefault(weapon.category, []).append(name)

        for category, names in groups.items():
            if self.weapon_box.count():
                self.weapon_box.insertSeparator(
                    self.weapon_box.count()
                )

            for name in names:
                self.weapon_box.addItem(name, name)

        last = self.weapon_box.findData(
            self.config.get("last_weapon", "")
        )

        if last >= 0:
            self.weapon_box.setCurrentIndex(last)

    def current_weapon(self):
        return self.weapons.get(self.weapon_box.currentData())

    def on_weapon_changed(self, *_):
        weapon = self.current_weapon()

        if weapon is None:
            return

        self.config["last_weapon"] = weapon.name

        self.schedule_save()

        self.update_weapon_info()

        self.recalculate_if_ready()

    def on_arc_changed(self, *_):
        self.config["arc"] = self.arc_box.currentData()

        self.schedule_save()

        self.recalculate_if_ready()

    def update_weapon_info(self):
        weapon = self.current_weapon()

        if weapon is None:
            self.weapon_info.setText("")
            return

        parts = [
            f"{weapon.velocity:g} m/s",
            f"gravity ×{weapon.gravity:g}",
            f"max ~{weapon.max_range():.0f} m",
            f"default: {weapon.arc} arc"
        ]

        if weapon.min_distance:
            parts.append(f"min {weapon.min_distance:g} m")

        text = "  ·  ".join(parts)

        if weapon.note:
            text += f"\n{weapon.note}"

        self.weapon_info.setText(text)

    def recalculate_if_ready(self):
        if self.distance_entry.text().strip():
            self.calculate(show_errors=False)

    def show_error(self, message):
        self.result_label.setStyleSheet(f"""
            color: {ERROR_COLOR};
            font-size: 18px;
            font-weight: bold;
        """)

        self.result_label.setText(message)

    def show_result(self, text):
        self.result_label.setStyleSheet(f"""
            color: {OK_COLOR};
            font-size: 18px;
            font-weight: bold;
        """)

        self.result_label.setText(text)

    def calculate(self, show_errors=True):
        self.details_label.setText("")

        weapon = self.current_weapon()

        try:
            if weapon is None:
                raise ValueError("Select a weapon")

            distance = parse_number(
                self.distance_entry.text(),
                "distance"
            )

            height = parse_number(
                self.height_entry.text(),
                "height difference",
                default=0.0
            )

            fov = parse_number(
                self.fov_entry.text(),
                "FOV"
            )

            if not 1 <= fov <= 179:
                raise ValueError("FOV must be between 1 and 179")

            solution = solve(
                weapon,
                distance,
                height,
                self.arc_box.currentData()
            )

        except ValueError as e:
            if show_errors:
                self.show_error(str(e))
            return

        if self.config["fov"] != fov:
            self.config["fov"] = fov
            self.schedule_save()

        self.last_solution = solution

        if not solution.reachable:
            self.show_error("Unreachable")

            self.details_label.setText(solution.reason)

            self.overlay.reset_offset()

            return

        self.apply_offset()

        if weapon.unit == "mil":
            self.show_result(
                f"{solution.mils:.0f} mil   ({solution.angle:.2f}°)"
            )
        else:
            self.show_result(
                f"{solution.angle:.2f}°   ({solution.mils:.0f} mil)"
            )

        details = [
            f"{solution.arc.capitalize()} arc",
            f"flight {solution.time_of_flight:.1f} s"
        ]

        other = "high" if solution.arc == "low" else "low"

        if other in solution.alternatives:
            details.append(
                f"{other} arc: {solution.alternatives[other]:.2f}°"
            )

        offset = self.current_offset()

        if abs(offset) > self.overlay.height() / 2:
            details.append(
                "aim point is off-screen — use the angle"
            )
        else:
            details.append(f"offset {offset:.0f} px")

        self.details_label.setText("  ·  ".join(details))

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

    def apply_offset(self):
        self.overlay.set_offset(self.current_offset())

    def reset_offset(self):
        self.last_solution = None

        self.overlay.reset_offset()

        self.show_result("Ready")

        self.details_label.setText("")

    def toggle_overlay(self):
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.show()

    # =========================
    # SETTINGS PAGE
    # =========================

    def build_settings_page(self):
        settings_page = QWidget()

        page_layout = QVBoxLayout(settings_page)

        page_layout.setContentsMargins(0, 20, 0, 20)

        scroll = QScrollArea()

        scroll.setWidgetResizable(True)

        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        content = QWidget()

        content.setObjectName("scrollContent")

        content_layout = QVBoxLayout(content)

        settings_container, settings_inner = self.make_card()

        settings_inner.setSpacing(10)

        settings_title = QLabel(
            "CROSSHAIR"
        )

        settings_title.setFont(
            QFont(
                "Segoe UI",
                18,
                QFont.Weight.Bold
            )
        )

        settings_inner.addWidget(
            settings_title
        )

        for label, key in [
            ("Center Dot", "dot_enabled"),
            ("Crosshair Lines", "lines_enabled"),
            ("T-Style (no bottom line)", "t_style"),
            ("Circle", "circle_enabled"),
            ("Dot Outline", "outline_enabled"),
            ("Glow / Bloom", "glow_enabled"),
            ("Smooth Animation", "animated")
        ]:
            self.add_toggle(settings_inner, label, key)

        self.add_slider(settings_inner, "DOT SIZE", 1, 20, "dot_size")
        self.add_slider(settings_inner, "OPACITY", 20, 255, "opacity")
        self.add_slider(settings_inner, "LINE LENGTH", 1, 40, "line_length")
        self.add_slider(settings_inner, "LINE GAP", 0, 30, "line_gap")
        self.add_slider(settings_inner, "THICKNESS", 1, 10, "line_thickness")
        self.add_slider(settings_inner, "OUTLINE", 1, 5, "outline_thickness")
        self.add_slider(settings_inner, "CIRCLE RADIUS", 5, 80, "circle_radius")

        for index, name in enumerate(("RED", "GREEN", "BLUE")):
            self.add_slider(
                settings_inner,
                name,
                0,
                255,
                ("color", index)
            )

        self.add_slider(
            settings_inner,
            "OFFSET CALIBRATION %",
            50,
            150,
            "offset_scale",
            on_change=self.apply_offset
        )

        content_layout.addWidget(
            settings_container,
            alignment=Qt.AlignmentFlag.AlignHCenter
        )

        content_layout.addStretch()

        scroll.setWidget(content)

        scroll.viewport().setAutoFillBackground(False)

        page_layout.addWidget(scroll)

        return settings_page

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

        self.overlay.update()

        self.schedule_save()

    def add_toggle(self, layout, label, key):
        checkbox = QCheckBox(label)

        checkbox.setChecked(bool(self.config[key]))

        checkbox.toggled.connect(
            lambda checked: self.set_setting(key, checked)
        )

        layout.addWidget(checkbox)

        return checkbox

    def add_slider(
        self,
        layout,
        label,
        minimum,
        maximum,
        key,
        on_change=None
    ):
        header = QHBoxLayout()

        name_label = QLabel(label)

        value_label = QLabel()

        value_label.setStyleSheet(f"color: {MUTED_COLOR};")

        header.addWidget(name_label)
        header.addStretch()
        header.addWidget(value_label)

        slider = QSlider(
            Qt.Orientation.Horizontal
        )

        slider.setRange(minimum, maximum)

        value = int(self.get_setting(key))

        slider.setValue(max(minimum, min(maximum, value)))

        value_label.setText(str(slider.value()))

        def handle(new_value):
            value_label.setText(str(new_value))

            self.set_setting(key, new_value)

            if on_change:
                on_change()

        slider.valueChanged.connect(handle)

        layout.addLayout(header)
        layout.addWidget(slider)

        return slider

    def schedule_save(self):
        self.save_timer.start()

    # =========================
    # WEB PAGE
    # =========================

    def build_web_page(self):
        web_page = QWidget()

        self.web_layout = QVBoxLayout(web_page)

        self.web_layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        self.browser = None

        return web_page

    def load_web_page(self):
        """Create the embedded browser on first use (it is heavy)."""
        if self.browser is not None:
            return

        try:
            from PyQt6.QtWebEngineWidgets import QWebEngineView
        except ImportError:
            self.browser = False

            label = QLabel(
                "Embedded browser is not available (PyQt6-WebEngine "
                "is not installed)."
            )

            open_btn = QPushButton("OPEN SQUADCALC IN BROWSER")

            open_btn.clicked.connect(
                lambda: QDesktopServices.openUrl(QUrl(SQUADCALC_URL))
            )

            self.web_layout.addStretch()
            self.web_layout.addWidget(
                label,
                alignment=Qt.AlignmentFlag.AlignCenter
            )
            self.web_layout.addWidget(
                open_btn,
                alignment=Qt.AlignmentFlag.AlignCenter
            )
            self.web_layout.addStretch()
            return

        self.browser = QWebEngineView()

        self.browser.load(
            QUrl(SQUADCALC_URL)
        )

        self.web_layout.addWidget(self.browser)

    def closeEvent(self, event):
        if self.save_timer.isActive():
            self.save_timer.stop()

        save_config(self.config)

        teardown_hotkeys(self)

        self.overlay.close()

        event.accept()
