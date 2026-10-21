import math

from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPointF,
    QRectF
)

from PyQt6.QtGui import (
    QColor,
    QPainter,
    QBrush,
    QPen,
    QPolygonF,
    QFont,
    QGuiApplication
)

from PyQt6.QtWidgets import QWidget


def paint_crosshair(painter, cfg, x, y):
    """Draw the configured crosshair centred on (x, y).

    Shared by the overlay and the preview on the crosshair page.
    """
    r, g, b = cfg["color"]

    color = QColor(r, g, b, cfg["opacity"])

    outline = QColor(
        "black" if cfg.get("outline_color") == "black" else "white"
    )
    outline.setAlpha(cfg["opacity"])

    outline_width = cfg["outline_thickness"]

    dot_size = cfg["dot_size"]

    if cfg["glow_enabled"]:
        painter.setPen(Qt.PenStyle.NoPen)

        for spread, alpha in ((dot_size + 9, 25), (dot_size + 5, 55)):
            painter.setBrush(QBrush(QColor(r, g, b, min(alpha, cfg["opacity"]))))
            painter.drawEllipse(QPointF(x, y), spread, spread)

    if cfg["lines_enabled"]:
        length = cfg["line_length"]
        gap = cfg["line_gap"]

        lines = [
            (x, y - gap, x, y - gap - length),
            (x - gap, y, x - gap - length, y),
            (x + gap, y, x + gap + length, y),
        ]

        if not cfg["t_style"]:
            lines.append((x, y + gap, x, y + gap + length))

        passes = []

        if cfg["outline_enabled"]:
            passes.append(
                QPen(
                    outline,
                    cfg["line_thickness"] + outline_width * 2,
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.FlatCap
                )
            )

        passes.append(
            QPen(
                color,
                cfg["line_thickness"],
                Qt.PenStyle.SolidLine,
                Qt.PenCapStyle.FlatCap
            )
        )

        for pen in passes:
            painter.setPen(pen)

            for x1, y1, x2, y2 in lines:
                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

    if cfg["circle_enabled"]:
        painter.setBrush(Qt.BrushStyle.NoBrush)

        radius = cfg["circle_radius"]

        if cfg["outline_enabled"]:
            painter.setPen(QPen(outline, 2 + outline_width * 2))
            painter.drawEllipse(QPointF(x, y), radius, radius)

        painter.setPen(QPen(color, 2))
        painter.drawEllipse(QPointF(x, y), radius, radius)

    if cfg["dot_enabled"]:
        painter.setBrush(QBrush(color))

        if cfg["outline_enabled"]:
            painter.setPen(QPen(outline, outline_width))
        else:
            painter.setPen(Qt.PenStyle.NoPen)

        painter.drawEllipse(QPointF(x, y), dot_size, dot_size)


class Overlay(QWidget):
    def __init__(self, config):
        super().__init__()

        self.config = config

        self.info_text = ""

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowTransparentForInput
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_ShowWithoutActivating
        )

        self.offset = 0.0

        self.target_offset = 0.0

        # The animation timer only runs while the aim point is moving.
        self.animation_timer = QTimer(self)

        self.animation_timer.timeout.connect(
            self.animate_offset
        )

        self.move_to_screen()

        self.show()

    def move_to_screen(self):
        screens = QGuiApplication.screens()

        index = int(self.config.get("monitor", 0))

        if 0 <= index < len(screens):
            screen = screens[index]
        else:
            screen = QGuiApplication.primaryScreen()

        self.setGeometry(screen.geometry())

        self.update()

    @property
    def center_x(self):
        return self.width() / 2 + self.config.get("center_offset_x", 0)

    @property
    def center_y(self):
        return self.height() / 2 + self.config.get("center_offset_y", 0)

    # Distance from the screen edge inside which the mark is still drawn.
    EDGE_MARGIN = 20

    def screen_width(self):
        return self.width()

    def is_offscreen(self, offset):
        """Whether the aim mark for `offset` falls outside the screen."""
        y = self.center_y + offset

        return not self.EDGE_MARGIN <= y <= self.height() - self.EDGE_MARGIN

    def set_info(self, text):
        self.info_text = text
        self.update()

    def set_offset(self, value):
        value = float(value)

        if math.isnan(value):
            value = 0.0

        # Off-screen offsets only need to keep their direction.
        limit = self.height() * 2
        self.target_offset = max(-limit, min(limit, value))

        if not self.config.get("animated", True):
            self.offset = self.target_offset
            self.animation_timer.stop()
            self.update()
            return

        fps = max(10, min(240, int(self.config.get("fps", 60))))

        self.animation_timer.start(int(1000 / fps))

    def reset_offset(self):
        self.set_offset(0)

    def animate_offset(self):
        self.offset += (
            self.target_offset - self.offset
        ) * 0.12

        if abs(
            self.target_offset - self.offset
        ) < 0.01:

            self.offset = self.target_offset

            self.animation_timer.stop()

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        cfg = self.config

        r, g, b = cfg["color"]

        color = QColor(r, g, b, cfg["opacity"])

        x = self.center_x
        y = self.center_y + self.offset

        if self.is_offscreen(self.offset):
            # The aim point is off-screen (very high angle shot):
            # show an arrow on the edge pointing towards it.
            top = y < self.EDGE_MARGIN

            self.draw_edge_arrow(painter, color, x, top)

            # Keep the label next to the arrow.
            y = 50 if top else self.height() - 50
        else:
            paint_crosshair(painter, cfg, x, y)

        if cfg.get("info_enabled", True) and self.info_text:
            self.draw_info(painter, color, x, y)

        painter.end()

    def draw_info(self, painter, color, x, y):
        font = QFont("Segoe UI", 10)
        font.setBold(True)
        painter.setFont(font)

        reach = max(
            self.config["circle_radius"] if self.config["circle_enabled"] else 0,
            self.config["line_gap"] + self.config["line_length"]
            if self.config["lines_enabled"] else 0,
            self.config["dot_size"] + 6
        )

        rect = QRectF(x + reach + 10, y - 10, 400, 20)

        painter.setPen(QColor(0, 0, 0, 180))
        painter.drawText(
            rect.translated(1, 1),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self.info_text
        )

        painter.setPen(color)
        painter.drawText(
            rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            self.info_text
        )

    def draw_edge_arrow(self, painter, color, x, top):
        size = 14

        if top:
            tip = 8
            base = tip + size
        else:
            tip = self.height() - 8
            base = tip - size

        painter.setPen(Qt.PenStyle.NoPen)

        painter.setBrush(QBrush(color))

        painter.drawPolygon(
            QPolygonF([
                QPointF(x, tip),
                QPointF(x - size, base),
                QPointF(x + size, base)
            ])
        )
