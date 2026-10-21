"""Colors and the application stylesheet."""

ACCENTS = [
    "#3b82f6",  # blue
    "#22c55e",  # green
    "#f59e0b",  # amber
    "#ef4444",  # red
    "#a855f7",  # purple
    "#c8b98f",  # sand
]

BG = "#0b0f16"
SURFACE = "#121824"
SURFACE_2 = "#1a2130"
BORDER = "#232b3a"
TEXT = "#e8ecf3"
MUTED = "#8590a6"
DANGER = "#ff6b6b"


def shade(color, factor):
    """Lighten (>1) or darken (<1) a #rrggbb color."""
    color = color.lstrip("#")
    r, g, b = (int(color[i:i + 2], 16) for i in (0, 2, 4))

    def f(c):
        return max(0, min(255, int(c * factor)))

    return f"#{f(r):02x}{f(g):02x}{f(b):02x}"


def stylesheet(accent):
    hover = shade(accent, 0.85)

    return f"""
    QMainWindow, QWidget#root {{
        background: {BG};
    }}

    QWidget {{
        color: {TEXT};
        font-family: "Segoe UI", "Inter", sans-serif;
        font-size: 13px;
    }}

    QLabel {{
        background: transparent;
    }}

    QLabel[role="title"] {{
        font-size: 15px;
        font-weight: 600;
    }}

    QLabel[role="section"] {{
        color: {MUTED};
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
        padding-top: 6px;
    }}

    QLabel[role="muted"] {{
        color: {MUTED};
    }}

    QLabel[role="small"] {{
        color: {MUTED};
        font-size: 11px;
    }}

    QLabel[role="big"] {{
        color: {accent};
        font-size: 40px;
        font-weight: 700;
    }}

    QLabel[role="big"][state="error"] {{
        color: {DANGER};
        font-size: 26px;
    }}

    QLabel[role="sub"] {{
        color: {MUTED};
        font-size: 15px;
    }}

    QLabel[role="stat_value"] {{
        font-size: 16px;
        font-weight: 600;
    }}

    QLabel[role="step_num"] {{
        background: {SURFACE_2};
        border-radius: 10px;
        color: {accent};
        font-weight: 700;
        min-width: 20px;
        max-width: 20px;
        min-height: 20px;
        max-height: 20px;
        qproperty-alignment: AlignCenter;
    }}

    QFrame#card {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 16px;
    }}

    QFrame#stat {{
        background: {SURFACE_2};
        border-radius: 10px;
    }}

    QFrame#sidebar {{
        background: {SURFACE};
        border-right: 1px solid {BORDER};
    }}

    QLineEdit {{
        background: {SURFACE_2};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 9px 12px;
        selection-background-color: {accent};
    }}

    QLineEdit:focus {{
        border: 1px solid {accent};
    }}

    QComboBox {{
        background: {SURFACE_2};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 7px 12px;
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox QAbstractItemView {{
        background: {SURFACE_2};
        border: 1px solid {BORDER};
        selection-background-color: {accent};
        outline: none;
    }}

    QPushButton {{
        background: {accent};
        border: none;
        border-radius: 10px;
        padding: 9px 14px;
        font-weight: 600;
    }}

    QPushButton:hover {{
        background: {hover};
    }}

    QPushButton[flat_style="true"] {{
        background: {SURFACE_2};
        border: 1px solid {BORDER};
        font-weight: 500;
    }}

    QPushButton[flat_style="true"]:hover {{
        border: 1px solid {accent};
    }}

    QPushButton#picker {{
        background: {SURFACE_2};
        border: 1px solid {BORDER};
        text-align: left;
        padding: 10px 12px;
        font-size: 14px;
        font-weight: 600;
    }}

    QPushButton#picker:hover {{
        border: 1px solid {accent};
    }}

    QPushButton#segment {{
        background: transparent;
        border-radius: 8px;
        color: {MUTED};
        font-weight: 600;
        padding: 7px 10px;
    }}

    QPushButton#segment:hover {{
        color: {TEXT};
    }}

    QPushButton#segment:checked {{
        background: {accent};
        color: white;
    }}

    QFrame#segments {{
        background: {SURFACE_2};
        border: 1px solid {BORDER};
        border-radius: 10px;
    }}

    QPushButton#nav {{
        background: transparent;
        border-radius: 12px;
        padding: 0;
    }}

    QPushButton#nav:hover {{
        background: {SURFACE_2};
    }}

    QPushButton#nav:checked {{
        background: {SURFACE_2};
        border-left: 3px solid {accent};
    }}

    QPushButton#swatch {{
        border-radius: 11px;
        min-width: 22px;
        max-width: 22px;
        min-height: 22px;
        max-height: 22px;
        padding: 0;
    }}

    QPushButton#swatch:checked {{
        border: 2px solid {TEXT};
    }}

    QSlider::groove:horizontal {{
        height: 4px;
        background: {BORDER};
        border-radius: 2px;
    }}

    QSlider::sub-page:horizontal {{
        background: {accent};
        border-radius: 2px;
    }}

    QSlider::handle:horizontal {{
        background: {TEXT};
        width: 14px;
        height: 14px;
        margin: -5px 0;
        border-radius: 7px;
    }}

    QScrollArea, QWidget#scrollContent {{
        background: transparent;
        border: none;
    }}

    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 4px;
    }}

    QScrollBar::handle:vertical {{
        background: {BORDER};
        border-radius: 3px;
        min-height: 30px;
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
        height: 0;
    }}

    QListWidget {{
        background: {SURFACE_2};
        border: none;
        outline: none;
    }}

    QListWidget::item {{
        padding: 6px 10px;
        border-radius: 6px;
    }}

    QListWidget::item:selected {{
        background: {accent};
    }}

    QListWidget::item:hover:!selected {{
        background: {BORDER};
    }}

    QFrame#popup {{
        background: {SURFACE_2};
        border: 1px solid {BORDER};
        border-radius: 12px;
    }}

    QToolTip {{
        background: {SURFACE_2};
        color: {TEXT};
        border: 1px solid {BORDER};
        padding: 4px 8px;
    }}
    """
