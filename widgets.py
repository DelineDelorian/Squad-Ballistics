"""Reusable widgets for the main window."""

import re

from PyQt6.QtCore import (
    Qt,
    QEvent,
    QPointF,
    QRectF,
    QSize,
    pyqtSignal
)

from PyQt6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QValidator
)

from PyQt6.QtWidgets import (
    QAbstractButton,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget
)

import theme
from ballistics import MILS_PER_DEGREE
from i18n import tr, category_name
from overlay import paint_crosshair


def label(text, role=None):
    widget = QLabel(text)

    if role:
        widget.setProperty("role", role)

    return widget


def repolish(widget):
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def card():
    frame = QFrame()

    frame.setObjectName("card")

    layout = QVBoxLayout(frame)

    layout.setContentsMargins(20, 18, 20, 20)

    layout.setSpacing(10)

    return frame, layout


class Toggle(QAbstractButton):
    """Minimal on/off switch with a text label."""

    def __init__(self, text, accent, checked=False):
        super().__init__()

        self.setText(text)

        self.setCheckable(True)

        self.setChecked(checked)

        self.accent = QColor(accent)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def sizeHint(self):
        width = self.fontMetrics().horizontalAdvance(self.text())
        return QSize(width + 52, 26)

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        track = QRectF(0, 4, 34, 18)

        painter.setPen(Qt.PenStyle.NoPen)

        painter.setBrush(
            self.accent if self.isChecked() else QColor(theme.BORDER)
        )

        painter.drawRoundedRect(track, 9, 9)

        knob_x = track.right() - 16 if self.isChecked() else track.left() + 2

        painter.setBrush(QColor("white"))

        painter.drawEllipse(QRectF(knob_x, 6, 14, 14))

        painter.setPen(QColor(theme.TEXT))

        painter.drawText(
            QRectF(46, 0, self.width() - 46, self.height()),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self.text()
        )


class Segmented(QFrame):
    """Row of mutually exclusive buttons (like a segmented control)."""

    changed = pyqtSignal(str)

    def __init__(self, options, current):
        super().__init__()

        self.setObjectName("segments")

        layout = QHBoxLayout(self)

        layout.setContentsMargins(3, 3, 3, 3)

        layout.setSpacing(2)

        self.group = QButtonGroup(self)

        self.buttons = {}

        for key, text in options:
            button = QPushButton(text)

            button.setObjectName("segment")

            button.setCheckable(True)

            button.setChecked(key == current)

            button.clicked.connect(
                lambda _checked, k=key: self.changed.emit(k)
            )

            self.group.addButton(button)

            layout.addWidget(button)

            self.buttons[key] = button


class NumberValidator(QValidator):
    """Validates a decimal number and normalises what the user typed.

    With a Russian keyboard layout the "." and "," keys produce "ю" and "б",
    and the numpad decimal key produces ",". All of them become ".", so a
    fractional number can be typed on any layout. A typographic minus is
    accepted as "-".
    """

    SEPARATORS = ",юбЮБ"
    MINUSES = "−–—"

    def __init__(self, allow_negative, parent=None):
        super().__init__(parent)

        sign = "-?" if allow_negative else ""

        self.pattern = re.compile(rf"{sign}\d{{0,6}}(\.\d{{0,3}})?")

    def normalize(self, text):
        for char in self.SEPARATORS:
            text = text.replace(char, ".")

        for char in self.MINUSES:
            text = text.replace(char, "-")

        return text.replace(" ", "").lstrip("+")

    def validate(self, text, pos):
        normalized = self.normalize(text)

        # Keep the cursor where it was relative to the remaining characters.
        pos = len(self.normalize(text[:pos]))

        if not self.pattern.fullmatch(normalized):
            return QValidator.State.Invalid, text, pos

        if normalized in ("", "-", ".", "-."):
            return QValidator.State.Intermediate, normalized, pos

        return QValidator.State.Acceptable, normalized, pos


class NumberEdit(QLineEdit):
    """Line edit for numbers.

    Accepts "." or "," on any keyboard layout. The mouse wheel steps the
    value (Shift: x0.1, Ctrl: x10); "-" anywhere flips the sign.
    """

    stepped = pyqtSignal()

    def __init__(self, allow_negative=False, step=10):
        super().__init__()

        self.step = step

        self.allow_negative = allow_negative

        self.setValidator(NumberValidator(allow_negative, self))

    def value(self, default=None):
        """The number, or `default` while the field is empty/incomplete."""
        text = self.text().strip().replace(",", ".")

        try:
            return float(text)
        except ValueError:
            return default

    def set_value(self, value):
        self.setText(f"{value:g}")

    def add(self, delta):
        value = round((self.value() or 0.0) + delta, 3)

        if not self.allow_negative:
            value = max(0.0, value)

        self.set_value(value)

    def keyPressEvent(self, event):
        flip = (
            self.allow_negative
            and event.text() in ("-",) + tuple(NumberValidator.MINUSES)
            and self.cursorPosition() > 0
            and self.value() is not None
        )

        if flip:
            text = self.text()
            position = self.cursorPosition()

            if text.startswith("-"):
                self.setText(text[1:])
                self.setCursorPosition(position - 1)
            else:
                self.setText("-" + text)
                self.setCursorPosition(position + 1)

            self.textEdited.emit(self.text())
            return

        super().keyPressEvent(event)

    def wheelEvent(self, event):
        steps = event.angleDelta().y() / 120

        if not steps:
            return

        step = self.step

        modifiers = event.modifiers()

        if modifiers & Qt.KeyboardModifier.ShiftModifier:
            step = step / 10
        elif modifiers & Qt.KeyboardModifier.ControlModifier:
            step = step * 10

        self.add(steps * step)

        self.stepped.emit()

        event.accept()


class _PickerPopup(QFrame):
    picked = pyqtSignal(str)

    def __init__(self, parent):
        super().__init__(parent, Qt.WindowType.Popup)

        self.setObjectName("popup")

        layout = QVBoxLayout(self)

        layout.setContentsMargins(8, 8, 8, 8)

        layout.setSpacing(6)

        self.search = QLineEdit()

        self.search.setPlaceholderText(tr("search"))

        self.search.textChanged.connect(self.refill)

        self.search.returnPressed.connect(self.pick_current)

        self.search.installEventFilter(self)

        self.list = QListWidget()

        self.list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.list.setTextElideMode(Qt.TextElideMode.ElideRight)

        self.list.itemActivated.connect(self.pick_item)

        self.list.itemClicked.connect(self.pick_item)

        layout.addWidget(self.search)
        layout.addWidget(self.list)

        self.groups = []
        self.recent = []

    def set_data(self, groups, recent):
        self.groups = groups
        self.recent = recent

    def header(self, text):
        item = QListWidgetItem(text.upper())

        item.setFlags(Qt.ItemFlag.NoItemFlags)

        font = QFont()
        font.setPointSize(8)
        font.setBold(True)

        item.setFont(font)

        item.setForeground(QColor(theme.MUTED))

        self.list.addItem(item)

    def refill(self):
        self.list.clear()

        query = self.search.text().strip().lower()

        first = None

        sections = []

        if not query and self.recent:
            sections.append((tr("recent"), self.recent))

        for category, names in self.groups:
            matching = [n for n in names if query in n.lower()]

            if matching:
                sections.append((category_name(category), matching))

        for title, names in sections:
            self.header(title)

            for name in names:
                item = QListWidgetItem(name)

                item.setData(Qt.ItemDataRole.UserRole, name)

                self.list.addItem(item)

                if first is None:
                    first = item

        if first is None:
            self.header(tr("nothing_found"))
        else:
            self.list.setCurrentItem(first)

    def pick_item(self, item):
        name = item.data(Qt.ItemDataRole.UserRole)

        if name:
            self.picked.emit(name)
            self.hide()

    def pick_current(self):
        item = self.list.currentItem()

        if item is not None:
            self.pick_item(item)

    def move_selection(self, direction):
        """Move to the next selectable row, skipping category headers."""
        row = self.list.currentRow()

        while True:
            row += direction

            if not 0 <= row < self.list.count():
                return

            item = self.list.item(row)

            if item.flags() & Qt.ItemFlag.ItemIsSelectable:
                self.list.setCurrentItem(item)
                return

    def eventFilter(self, watched, event):
        if watched is self.search and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Down:
                self.move_selection(1)
                return True

            if event.key() == Qt.Key.Key_Up:
                self.move_selection(-1)
                return True

        return super().eventFilter(watched, event)


class WeaponPicker(QPushButton):
    """Button showing the current weapon; opens a searchable list."""

    changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setObjectName("picker")

        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.current = None

        self.popup = _PickerPopup(self)

        self.popup.picked.connect(self.set_current)

        self.clicked.connect(self.open_popup)

    def set_data(self, groups, recent):
        self.popup.set_data(groups, recent)

    def set_current(self, name, emit=True):
        self.current = name

        self.setText(f"{name}   ▾")

        if emit:
            self.changed.emit(name)

    def open_popup(self):
        self.popup.search.clear()

        self.popup.refill()

        width = max(self.width(), 360)

        self.popup.resize(width, 440)

        # Below the button, but kept inside the screen.
        position = self.mapToGlobal(self.rect().bottomLeft())

        screen = QGuiApplication.screenAt(position)

        if screen is not None:
            area = screen.availableGeometry()

            if position.y() + self.popup.height() > area.bottom():
                position.setY(
                    max(area.top(), position.y() - self.height()
                        - self.popup.height())
                )

            position.setX(
                max(area.left(),
                    min(position.x(), area.right() - self.popup.width()))
            )

        self.popup.move(position)

        self.popup.show()

        self.popup.search.setFocus()


class Swatches(QWidget):
    """Row of round color buttons."""

    picked = pyqtSignal(str)

    def __init__(self, colors, current=None):
        super().__init__()

        layout = QHBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(8)

        self.group = QButtonGroup(self)

        self.buttons = {}

        for color in colors:
            button = QPushButton()

            button.setObjectName("swatch")

            button.setCheckable(True)

            button.setChecked(
                current is not None and color.lower() == current.lower()
            )

            button.setStyleSheet(f"background: {color};")

            button.setCursor(Qt.CursorShape.PointingHandCursor)

            button.clicked.connect(
                lambda _checked, c=color: self.picked.emit(c)
            )

            self.group.addButton(button)

            layout.addWidget(button)

            self.buttons[color.lower()] = button

        layout.addStretch()

    def set_current(self, color):
        """Check the matching swatch, or none for a custom color."""
        self.group.setExclusive(False)

        for key, button in self.buttons.items():
            button.setChecked(key == color.lower())

        self.group.setExclusive(True)


class SliderRow(QWidget):
    changed = pyqtSignal(int)

    def __init__(self, text, minimum, maximum, value, suffix=""):
        super().__init__()

        self.suffix = suffix

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(4)

        header = QHBoxLayout()

        header.addWidget(label(text))

        header.addStretch()

        self.value_label = label("", "muted")

        header.addWidget(self.value_label)

        self.slider = QSlider(Qt.Orientation.Horizontal)

        self.slider.setRange(minimum, maximum)

        self.slider.setValue(max(minimum, min(maximum, int(value))))

        self.slider.valueChanged.connect(self.on_change)

        layout.addLayout(header)
        layout.addWidget(self.slider)

        self.update_label(self.slider.value())

    def update_label(self, value):
        self.value_label.setText(f"{value}{self.suffix}")

    def on_change(self, value):
        self.update_label(value)
        self.changed.emit(value)


class StatTile(QFrame):
    def __init__(self, caption):
        super().__init__()

        self.setObjectName("stat")

        layout = QVBoxLayout(self)

        layout.setContentsMargins(12, 8, 12, 10)

        layout.setSpacing(2)

        layout.addWidget(label(caption, "small"))

        self.value = label("—", "stat_value")

        layout.addWidget(self.value)

    def set(self, text):
        self.value.setText(text)


class TrajectoryView(QWidget):
    """Side view of the shot: weapon, target and both possible arcs."""

    def __init__(self, accent):
        super().__init__()

        self.accent = QColor(accent)

        self.main = []
        self.alt = []
        self.target = None

        self.setMinimumHeight(170)

    def set_data(self, main, alt, target):
        self.main = main
        self.alt = alt
        self.target = target
        self.update()

    def clear(self):
        self.set_data([], [], None)

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(8, 18, -8, -22)

        painter.setPen(QPen(QColor(theme.BORDER), 1))

        painter.setBrush(QColor(theme.SURFACE_2))

        painter.drawRoundedRect(QRectF(self.rect()).adjusted(0, 0, -1, -1), 10, 10)

        if not self.main or self.target is None:
            painter.setPen(QColor(theme.MUTED))
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "—"
            )
            return

        points = self.main + self.alt + [(0.0, 0.0), self.target]

        max_x = max(p[0] for p in points) or 1.0
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)

        if max_y - min_y < 1e-6:
            max_y += 1
            min_y -= 1

        pad = (max_y - min_y) * 0.08
        min_y -= pad
        max_y += pad

        def map_point(p):
            return QPointF(
                rect.left() + p[0] / max_x * rect.width(),
                rect.bottom() - (p[1] - min_y) / (max_y - min_y) * rect.height()
            )

        # Zero line (weapon height)
        zero = map_point((0, 0)).y()

        painter.setPen(QPen(QColor(theme.BORDER), 1, Qt.PenStyle.DashLine))

        painter.drawLine(QPointF(rect.left(), zero), QPointF(rect.right(), zero))

        def draw_path(samples, pen):
            path = QPainterPath(map_point(samples[0]))

            for sample in samples[1:]:
                path.lineTo(map_point(sample))

            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

        if self.alt:
            draw_path(
                self.alt,
                QPen(QColor(theme.MUTED), 1.5, Qt.PenStyle.DashLine)
            )

        draw_path(self.main, QPen(self.accent, 2.5))

        # Apex marker, only when the shell really climbs above both ends.
        apex = max(self.main, key=lambda p: p[1])

        apex_point = map_point(apex)

        if apex[1] - max(0.0, self.target[1]) < 1:
            apex = None

        small = QFont(self.font())
        small.setPointSize(8)
        painter.setFont(small)

        if apex is not None:
            painter.setPen(Qt.PenStyle.NoPen)

            painter.setBrush(self.accent)

            painter.drawEllipse(apex_point, 3.5, 3.5)

            painter.setPen(QColor(theme.MUTED))

            painter.drawText(
                QRectF(apex_point.x() - 60, apex_point.y() - 18, 120, 14),
                Qt.AlignmentFlag.AlignCenter,
                f"{apex[1]:.0f} {tr('unit_m')}"
            )

        # Weapon and target
        shooter = map_point((0, 0))
        target = map_point(self.target)

        painter.setPen(Qt.PenStyle.NoPen)

        painter.setBrush(QColor(theme.TEXT))

        painter.drawEllipse(shooter, 4, 4)

        painter.setBrush(QColor(theme.DANGER))

        painter.drawEllipse(target, 5, 5)

        painter.setPen(QColor(theme.MUTED))

        painter.drawText(
            QRectF(rect.left(), rect.bottom() + 4, rect.width(), 14),
            Qt.AlignmentFlag.AlignRight,
            f"{self.target[0]:.0f} {tr('unit_m')}"
        )


class CrosshairPreview(QWidget):
    """Live preview of the overlay crosshair on a game-like background."""

    def __init__(self, config):
        super().__init__()

        self.config = config

        self.setMinimumSize(260, 220)

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(self.rect()).adjusted(0, 0, -1, -1)

        sky = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        sky.setColorAt(0, QColor("#4b5a6b"))
        sky.setColorAt(0.55, QColor("#8a8f86"))
        sky.setColorAt(0.56, QColor("#5b5a45"))
        sky.setColorAt(1, QColor("#3a3a2c"))

        path = QPainterPath()
        path.addRoundedRect(rect, 12, 12)

        painter.setClipPath(path)

        painter.fillRect(rect, sky)

        paint_crosshair(
            painter,
            self.config,
            rect.center().x(),
            rect.center().y()
        )


def format_angle(degrees, unit):
    if unit == "mil":
        return f"{degrees * MILS_PER_DEGREE:.0f} {tr('mil')}"
    return f"{degrees:.2f}°"

