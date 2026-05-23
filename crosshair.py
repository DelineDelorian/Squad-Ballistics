import math
from PyQt6.QtWidgets import QCheckBox

import qtawesome as qta

from PyQt6.QtCore import (
    Qt,
    QSize,
    QUrl
)

from PyQt6.QtGui import (
    QFont,
    QDoubleValidator,
    QIcon
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
    QMessageBox
)

from PyQt6.QtWebEngineWidgets import (
    QWebEngineView
)

from overlay import Overlay

from config import (
    load_config,
    save_config
)

from hotkeys import setup_hotkeys

BUTTON_STYLE = """
QPushButton {
    background-color: rgba(35,40,50,220);
    border-radius: 14px;
    border: none;
}

QPushButton:hover {
    background-color: rgba(55,60,75,220);
}
"""

class MainWindow(QMainWindow):
    def __init__(self, weapons):
        super().__init__()

        self.weapons = weapons

        self.config = load_config()

        self.overlay = Overlay(
            self.config
        )

        setup_hotkeys(self)

        self.setWindowTitle(
            "Squad Ballistics"
        )

        self.setWindowIcon(
            QIcon("assets/icon.ico")
        )

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
        """)

        root = QWidget()

        self.setCentralWidget(root)

        layout = QHBoxLayout(root)

        layout.setContentsMargins(0, 0, 0, 0)

        # =========================
        # SIDEBAR
        # =========================

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

        self.pages = QStackedWidget()

        # =========================
        # MAIN PAGE
        # =========================

        main_page = QWidget()

        main_layout = QVBoxLayout(main_page)

        main_layout.addStretch()

        container = QFrame()

        container.setFixedWidth(420)

        container.setStyleSheet("""
            background-color: rgba(25,30,40,220);
            border-radius: 20px;
        """)

        container_layout = QVBoxLayout(container)

        container_layout.setContentsMargins(
            24,
            24,
            24,
            24
        )

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

        validator = QDoubleValidator()

        self.weapon_box = QComboBox()

        self.weapon_box.addItems(
            list(self.weapons.keys())
        )

        self.distance_entry = QLineEdit()

        self.distance_entry.setPlaceholderText(
            "Distance"
        )

        self.distance_entry.setValidator(
            validator
        )

        self.height_entry = QLineEdit()

        self.height_entry.setPlaceholderText(
            "Height Difference"
        )

        self.height_entry.setValidator(
            validator
        )

        self.fov_entry = QLineEdit()

        self.fov_entry.setPlaceholderText(
            "FOV"
        )

        self.fov_entry.setText(
            str(self.config["fov"])
        )

        calc_btn = QPushButton(
            "CALCULATE"
        )

        calc_btn.setFixedHeight(42)

        calc_btn.clicked.connect(
            self.calculate
        )

        self.result_label = QLabel(
            "Ready"
        )

        self.result_label.setStyleSheet("""
            color: #00ff88;
            font-size: 18px;
            font-weight: bold;
        """)

        container_layout.addWidget(title)
        container_layout.addWidget(self.weapon_box)
        container_layout.addWidget(self.distance_entry)
        container_layout.addWidget(self.height_entry)
        container_layout.addWidget(self.fov_entry)
        container_layout.addWidget(calc_btn)
        container_layout.addWidget(self.result_label)

        main_layout.addWidget(
            container,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        main_layout.addStretch()

        # =========================
        # SETTINGS PAGE
        # =========================

        settings_page = QWidget()

        settings_layout = QVBoxLayout(settings_page)

        settings_layout.addStretch()

        settings_container = QFrame()

        settings_container.setFixedWidth(420)

        settings_container.setStyleSheet("""
            background-color: rgba(25,30,40,220);
            border-radius: 20px;
        """)

        settings_inner = QVBoxLayout(
            settings_container
        )

        settings_inner.setContentsMargins(
            24,
            24,
            24,
            24
        )

        settings_inner.setSpacing(15)

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

        settings_inner.addWidget(
            QLabel("DOT SIZE")
        )

        dot_slider = QSlider(
            Qt.Orientation.Horizontal
        )

        dot_slider.setRange(1, 20)

        dot_slider.setValue(
            self.config["dot_size"]
        )

        dot_slider.valueChanged.connect(
            self.change_dot_size
        )

        settings_inner.addWidget(
            dot_slider
        )

        settings_inner.addWidget(
            QLabel("OPACITY")
        )

        opacity_slider = QSlider(
            Qt.Orientation.Horizontal
        )

        opacity_slider.setRange(20, 255)

        opacity_slider.setValue(
            self.config["opacity"]
        )

        opacity_slider.valueChanged.connect(
            self.change_opacity
        )

        settings_inner.addWidget(
            opacity_slider
        )

        glow_checkbox = QCheckBox(
            "Glow / Bloom"
        )

        glow_checkbox.setChecked(
            self.config["glow_enabled"]
        )

        glow_checkbox.stateChanged.connect(
            self.toggle_glow
        )

        settings_inner.addWidget(
            glow_checkbox
        )

        lines_checkbox = QCheckBox(
            "Crosshair Lines"
        )

        lines_checkbox.setChecked(
            self.config["lines_enabled"]
        )

        lines_checkbox.stateChanged.connect(
            self.toggle_lines
        )

        settings_inner.addWidget(
            lines_checkbox
        )

        dot_checkbox = QCheckBox(
            "Center Dot"
        )

        dot_checkbox.setChecked(
            self.config["dot_enabled"]
        )

        dot_checkbox.stateChanged.connect(
            self.toggle_dot
        )

        settings_inner.addWidget(
            dot_checkbox
        )

        settings_layout.addWidget(
            settings_container,
            alignment=Qt.AlignmentFlag.AlignCenter
        )

        settings_layout.addStretch()

        settings_inner.addWidget(
                QLabel("LINE LENGTH")
            )

        length_slider = QSlider(
                Qt.Orientation.Horizontal
            )

        length_slider.setRange(1, 40)

        length_slider.setValue(
                self.config["line_length"]
            )

        length_slider.valueChanged.connect(
                self.change_line_length
            )

        settings_inner.addWidget(
                length_slider
            )
        
        settings_inner.addWidget(
            QLabel("LINE GAP")
        )

        gap_slider = QSlider(
            Qt.Orientation.Horizontal
        )

        gap_slider.setRange(0, 30)

        gap_slider.setValue(
            self.config["line_gap"]
        )

        gap_slider.valueChanged.connect(
            self.change_gap
        )

        settings_inner.addWidget(
            gap_slider
        )

        settings_inner.addWidget(
            QLabel("THICKNESS")
        )

        thickness_slider = QSlider(
            Qt.Orientation.Horizontal
        )

        thickness_slider.setRange(1, 10)

        thickness_slider.setValue(
            self.config["line_thickness"]
        )

        thickness_slider.valueChanged.connect(
            self.change_thickness
        )

        settings_inner.addWidget(
            thickness_slider
        )

        settings_inner.addWidget(
            QLabel("RED")
        )

        red_slider = QSlider(
            Qt.Orientation.Horizontal
        )

        red_slider.setRange(0, 255)

        red_slider.setValue(
            self.config["color"][0]
        )

        red_slider.valueChanged.connect(
            self.change_red
        )

        settings_inner.addWidget(
            red_slider
        )

        settings_inner.addWidget(
            QLabel("GREEN")
        )

        green_slider = QSlider(
            Qt.Orientation.Horizontal
        )

        green_slider.setRange(0, 255)

        green_slider.setValue(
            self.config["color"][1]
        )

        green_slider.valueChanged.connect(
            self.change_green
        )

        settings_inner.addWidget(
            green_slider
        )

        settings_inner.addWidget(
            QLabel("BLUE")
        )

        blue_slider = QSlider(
            Qt.Orientation.Horizontal
        )

        blue_slider.setRange(0, 255)

        blue_slider.setValue(
            self.config["color"][2]
        )

        blue_slider.valueChanged.connect(
            self.change_red
        )

        settings_inner.addWidget(
            blue_slider
        )

        # =========================
        # WEB PAGE
        # =========================

        web_page = QWidget()

        web_layout = QVBoxLayout(web_page)

        web_layout.setContentsMargins(
            20,
            20,
            20,
            20
        )

        browser = QWebEngineView()

        browser.load(
            QUrl(
                "https://squadcalc.app/?map=AlBasrah"
            )
        )

        browser.setStyleSheet("""
            border-radius: 20px;
        """)

        web_layout.addWidget(browser)

        self.pages.addWidget(main_page)
        self.pages.addWidget(settings_page)
        self.pages.addWidget(web_page)

        # =========================
        # BUTTONS
        # =========================

        def create_sidebar_button(icon):
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

            btn.setStyleSheet(
                BUTTON_STYLE
            )

            return btn

        home_btn = create_sidebar_button(
            "fa5s.home"
        )

        home_btn.clicked.connect(
            lambda: self.pages.setCurrentIndex(0)
        )

        sidebar_layout.addWidget(home_btn)

        settings_btn = create_sidebar_button(
            "fa5s.crosshairs"
        )

        settings_btn.clicked.connect(
            lambda: self.pages.setCurrentIndex(1)
        )

        sidebar_layout.addWidget(settings_btn)

        web_btn = create_sidebar_button(
            "fa5s.globe"
        )

        web_btn.clicked.connect(
            lambda: self.pages.setCurrentIndex(2)
        )

        sidebar_layout.addWidget(web_btn)

        sidebar_layout.addStretch()

        layout.addWidget(sidebar)
        layout.addWidget(self.pages)

    def change_line_length(self, value):
        self.config["line_length"] = value
        save_config(self.config)

    def change_gap(self, value):
        self.config["line_gap"] = value
        save_config(self.config)

    def change_thickness(self, value):
        self.config["line_thickness"] = value
        save_config(self.config)

    def change_red(self, value):
        self.config["color"][0] = value
        save_config(self.config)

    def change_green(self, value):
        self.config["color"][1] = value
        save_config(self.config)

    def change_blue(self, value):
        self.config["color"][2] = value
        save_config(self.config)

    def toggle_overlay(self):
        if self.overlay.isVisible():
            self.overlay.hide()
        else:
            self.overlay.show()

    def change_dot_size(self, value):
        self.config["dot_size"] = value

        save_config(self.config)

    def change_opacity(self, value):
        self.config["opacity"] = value

        save_config(self.config)
    
    def toggle_glow(self, state):
        self.config["glow_enabled"] = bool(state)

        save_config(self.config)

        self.overlay.update()
    
    def toggle_lines(self, state):
        self.config["lines_enabled"] = bool(state)

        save_config(self.config)

        self.overlay.update()
    
    def toggle_dot(self, state):
        self.config["dot_enabled"] = bool(state)

        save_config(self.config)

        self.overlay.update()

    def calculate(self):
        try:
            weapon_name = (
                self.weapon_box.currentText()
            )

            distance = float(
                self.distance_entry.text()
            )

            height = float(
                self.height_entry.text()
            )

            fov = float(
                self.fov_entry.text()
            )

            self.config["fov"] = fov

            save_config(self.config)

            velocity = self.weapons[
                weapon_name
            ]["velocity"]

            angle = self.calculate_angle(
                distance,
                height,
                velocity
            )

            offset = (
                angle * 18 * (90 / fov)
            )

            self.overlay.set_offset(
                offset
            )

            self.result_label.setText(
                f"{angle:.2f}°"
            )

        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                str(e)
            )

    def calculate_angle(
        self,
        distance,
        height_diff,
        velocity
    ):
        g = 9.81

        angle = math.atan(
            (
                velocity**2
                - math.sqrt(
                    velocity**4
                    - g * (
                        g * distance**2
                        + 2 * height_diff * velocity**2
                    )
                )
            )
            / (g * distance)
        )

        return math.degrees(angle)

    def closeEvent(self, event):
        self.overlay.close()
        event.accept()