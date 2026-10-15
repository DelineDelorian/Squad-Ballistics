from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QProgressBar
)


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.setFixedSize(420, 220)

        self.setStyleSheet("""
            background-color: #070707;
            border: 1px solid #2d2b24;
            border-radius: 18px;
        """)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(
            30,
            30,
            30,
            30
        )

        title = QLabel(
            "Squad Ballistics"
        )

        title.setStyleSheet("""
            font-size: 26px;
            font-weight: bold;
            color: #f2f2ee;
        """)

        layout.addWidget(title)

        self.status = QLabel(
            "Checking updates..."
        )

        self.status.setStyleSheet("""
            color: #c8b98f;
            font-size: 14px;
        """)

        layout.addWidget(self.status)

        self.progress = QProgressBar()

        self.progress.setRange(0, 100)

        self.progress.setValue(0)

        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: #151512;
                border: 1px solid #2d2b24;
                border-radius: 10px;
                height: 20px;
                color: #f2f2ee;
                text-align: center;
            }

            QProgressBar::chunk {
                background-color: #c8b98f;
                border-radius: 10px;
            }
        """)

        layout.addWidget(self.progress)
