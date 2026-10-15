# PyInstaller build: pyinstaller SquadBallistics.spec
# Produces dist/SquadBallistics/ (zip that folder as SquadBallistics.zip
# for the auto-updater).

a = Analysis(
    ["app.py"],
    datas=[
        ("weapons.json", "."),
        ("assets", "assets"),
    ],
    hiddenimports=["PyQt6.QtWebEngineWidgets"],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SquadBallistics",
    console=False,
    icon="assets/icon.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="SquadBallistics",
)
