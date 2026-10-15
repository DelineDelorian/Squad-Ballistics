"""Hotkeys.

A QShortcut only fires while the Squad Ballistics window has focus, which is
useless while playing. On Windows the keys are registered system-wide with
RegisterHotKey so they also work in game; elsewhere (or if another program
already owns the key) we fall back to a normal window shortcut.
"""

import sys

from PyQt6.QtCore import (
    Qt,
    QAbstractNativeEventFilter,
    QCoreApplication
)

from PyQt6.QtGui import (
    QShortcut,
    QKeySequence
)

# (key name, Windows virtual-key code, MainWindow method)
HOTKEYS = [
    ("F8", 0x77, "toggle_overlay"),
    ("F9", 0x78, "reset_offset"),
]

WM_HOTKEY = 0x0312
MOD_NOREPEAT = 0x4000


class _WindowsHotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, callbacks):
        super().__init__()

        from ctypes import wintypes

        self._msg_type = wintypes.MSG
        self.callbacks = callbacks

    def nativeEventFilter(self, event_type, message):
        if bytes(event_type) in (
            b"windows_generic_MSG",
            b"windows_dispatcher_MSG"
        ):
            msg = self._msg_type.from_address(int(message))

            if msg.message == WM_HOTKEY:
                callback = self.callbacks.get(msg.wParam)

                if callback:
                    callback()
                    return True, 0

        return False, 0


def _register_global(window, hotkeys):
    """Register hotkeys system-wide. Returns the names that failed."""
    import ctypes

    user32 = ctypes.windll.user32

    callbacks = {}
    failed = []

    for index, (name, vk, method) in enumerate(hotkeys, start=1):
        if user32.RegisterHotKey(None, index, MOD_NOREPEAT, vk):
            callbacks[index] = getattr(window, method)
        else:
            failed.append((name, vk, method))

    if callbacks:
        event_filter = _WindowsHotkeyFilter(callbacks)

        QCoreApplication.instance().installNativeEventFilter(
            event_filter
        )

        # Keep a reference, otherwise the filter is garbage collected.
        window._hotkey_filter = event_filter
        window._hotkey_ids = list(callbacks)

    return failed


def setup_hotkeys(window):
    local = HOTKEYS

    if sys.platform == "win32":
        try:
            local = _register_global(window, HOTKEYS)
        except Exception:
            local = HOTKEYS

    window._shortcuts = []

    for name, _vk, method in local:
        shortcut = QShortcut(
            QKeySequence(name),
            window
        )

        shortcut.setContext(
            Qt.ShortcutContext.ApplicationShortcut
        )

        shortcut.activated.connect(
            getattr(window, method)
        )

        window._shortcuts.append(shortcut)


def teardown_hotkeys(window):
    ids = getattr(window, "_hotkey_ids", [])

    if not ids or sys.platform != "win32":
        return

    import ctypes

    for hotkey_id in ids:
        ctypes.windll.user32.UnregisterHotKey(None, hotkey_id)

    window._hotkey_ids = []
