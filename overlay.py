import math

from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPointF
)

from PyQt6.QtGui import (
    QColor,
    QPainter,
    QBrush,
    QPen,
    QPolygonF
)

from PyQt6.QtWidgets import (
    QWidget,
    QApplication
)


class Overlay(QWidget):
    def __init__(self, config):
        super().__init__()

        self.config = config

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

        self.setGeometry(
            QApplication.primaryScreen().geometry()
        )

        self.offset = 0.0

        self.target_offset = 0.0

        # The animation timer only runs while the aim point is moving.
        self.animation_timer = QTimer(self)

        self.animation_timer.timeout.connect(
            self.animate_offset
        )

        self.show()

    @property
    def center_x(self):
        return self.width() // 2

    @property
    def center_y(self):
        return self.height() // 2

    def screen_width(self):
        return self.width()

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
        y = round(self.center_y + self.offset)

        margin = 20

        if not margin <= y <= self.height() - margin:
            # The aim point is off-screen (very high angle shot):
            # show an arrow on the edge pointing towards it.
            self.draw_edge_arrow(painter, color, x, y < margin)
            painter.end()
            return

        dot_size = cfg["dot_size"]

        if cfg["glow_enabled"]:

            glow = QColor(r, g, b, min(80, cfg["opacity"]))

            painter.setBrush(
                QBrush(glow)
            )

            painter.setPen(Qt.PenStyle.NoPen)

            painter.drawEllipse(
                QPointF(x, y),
                dot_size + 5,
                dot_size + 5
            )

        if cfg["dot_enabled"]:

            painter.setBrush(
                QBrush(color)
            )

            if cfg["outline_enabled"]:
                painter.setPen(
                    QPen(
                        QColor("white"),
                        cfg["outline_thickness"]
                    )
                )
            else:
                painter.setPen(Qt.PenStyle.NoPen)

            painter.drawEllipse(
                QPointF(x, y),
                dot_size,
                dot_size
            )

        if cfg["lines_enabled"]:

            painter.setPen(
                QPen(
                    color,
                    cfg["line_thickness"]
                )
            )

            length = cfg["line_length"]

            gap = cfg["line_gap"]

            # TOP

            painter.drawLine(
                x,
                y - gap,
                x,
                y - gap - length
            )

            # BOTTOM

            if not cfg["t_style"]:

                painter.drawLine(
                    x,
                    y + gap,
                    x,
                    y + gap + length
                )

            # LEFT

            painter.drawLine(
                x - gap,
                y,
                x - gap - length,
                y
            )

            # RIGHT

            painter.drawLine(
                x + gap,
                y,
                x + gap + length,
                y
            )

        if cfg["circle_enabled"]:

            painter.setBrush(
                Qt.BrushStyle.NoBrush
            )

            painter.setPen(
                QPen(
                    color,
                    2
                )
            )

            radius = cfg["circle_radius"]

            painter.drawEllipse(
                QPointF(x, y),
                radius,
                radius
            )

        painter.end()

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
