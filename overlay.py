from PyQt6.QtCore import Qt, QTimer

from PyQt6.QtGui import (
    QColor,
    QPainter,
    QBrush,
    QPen
)

from PyQt6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QEasingCurve
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
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TransparentForMouseEvents
        )

        screen = QApplication.primaryScreen().geometry()

        self.setGeometry(screen)

        self.center_x = screen.width() // 2
        self.center_y = screen.height() // 2

        self.offset = 0
        
        self.target_offset = 0
        self.animation_timer = QTimer()

        self.animation_timer.timeout.connect(
            self.animate_offset
        )

        self.animation_timer.start(16)

        def animate_offset(self):
            self.offset += (
                self.target_offset - self.offset
            ) * 0.12

            if abs(
                self.target_offset - self.offset
            ) < 0.01:
                self.offset = self.target_offset

            self.update()

        self.animation = QPropertyAnimation(
            self,
            b"windowOpacity"
        )

        self.animation.setDuration(120)

        self.animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        self.timer = QTimer()

        self.timer.timeout.connect(
            self.update
        )

        fps = config["fps"]

        self.timer.start(
            int(1000 / fps)
        )

        self.show()

    def set_offset(self, value):
        self.target_offset = value

    def animate_offset(self):
        self.offset += (
            self.target_offset - self.offset
        ) * 0.12

        if abs(
            self.target_offset - self.offset
        ) < 0.01:

            self.offset = self.target_offset

        self.update()

    def paintEvent(self, event):
        painter = QPainter()

        painter.begin(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        r, g, b = self.config["color"]

        opacity = self.config["opacity"]

        dot_size = self.config["dot_size"]

        color = QColor(
            r,
            g,
            b,
            opacity
        )

        x = self.center_x
        y = int(self.center_y + self.offset)
        cfg = self.config

        if cfg["glow_enabled"]:

            glow = QColor(
                g,
                b,
                80
            )

            painter.setBrush(
                QBrush(glow)
            )

            painter.setPen(Qt.PenStyle.NoPen)

            painter.drawEllipse(
                x - dot_size - 5,
                y - dot_size - 5,
                (dot_size + 5) * 2,
                (dot_size + 5) * 2
            )
        if cfg["dot_enabled"]:

            painter.setBrush(
                QBrush(color)
            )

            painter.setPen(
                QPen(
                    QColor("white"),
                    cfg["outline_thickness"]
                )
            )

            painter.drawEllipse(
                x - dot_size,
                y - dot_size,
                dot_size * 2,
                dot_size * 2
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
                x - radius,
                y - radius,
                radius * 2,
                radius * 2
            )
        
        painter.end()