# PyInstaller build: pyinstaller SquadBallistics.spec
#
# Produces a single file, dist/SquadBallistics.exe. Settings, caches and
# logs are kept in the user's profile (%APPDATA% / %LOCALAPPDATA%), never
# next to the .exe.

import importlib.util

a = Analysis(
    ["app.py"],
    datas=[
        ("weapons.json", "."),
        ("assets", "assets"),
    ],
    hiddenimports=["PyQt6.QtWebEngineWidgets"],
)

pyz = PYZ(a.pure)

extra = []

# Shown by the bootloader while the single .exe unpacks itself (a few
# seconds), closed by app.py once the app window appears. Needs Tcl/Tk in
# the Python used for the build.
if importlib.util.find_spec("tkinter") is not None:
    splash = Splash(
        "assets/splash.png",
        binaries=a.binaries,
        datas=a.datas,
        always_on_top=True,
    )
    extra = [splash, splash.binaries]

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    *extra,
    name="SquadBallistics",
    console=False,
    icon="assets/icon.ico",
    upx=False,
)
