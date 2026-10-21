import os

import updater

from conftest import ROOT


def test_version_matches_version_file():
    with open(os.path.join(ROOT, "version.txt")) as f:
        assert f.read().strip() == updater.CURRENT_VERSION


def test_version_compare():
    assert updater.is_newer("1.1.1", "1.1.0")
    assert updater.is_newer("1.2", "1.1.9")
    assert updater.is_newer("v2.0.0", "1.9.9")
    assert not updater.is_newer("1.1.0", "1.1.0")
    # Never "update" to an older version.
    assert not updater.is_newer("1.0.2", "1.1.0")


def test_no_update_check_from_source():
    assert updater.check_for_updates() is None


def test_release_asset_is_single_exe():
    assert updater.EXE_URL.endswith("/releases/latest/download/SquadBallistics.exe")


def test_update_script_swaps_exe_and_always_restarts():
    script = updater.update_script(
        r"C:\Temp\SquadBallistics.new.exe",
        r"C:\Users\Иван\Desktop\SquadBallistics.exe"
    )

    lines = script.split("\r\n")

    # Windows line endings and UTF-8 for non-ASCII paths.
    assert "\n" not in script.replace("\r\n", "")
    assert lines[1] == "chcp 65001 >nul"

    move = next(line for line in lines if line.startswith("move "))
    assert r'"C:\Temp\SquadBallistics.new.exe"' in move
    assert r'"C:\Users\Иван\Desktop\SquadBallistics.exe"' in move

    # Retries while the old .exe is locked, then restarts in any case.
    assert "goto retry" in script
    assert lines.index(":start") > lines.index(move)
    assert any(
        line.startswith('start "" "C:\\Users') for line in lines
    )


def test_old_folder_cleanup_only_when_frozen(tmp_path, monkeypatch):
    internal = tmp_path / "_internal"
    internal.mkdir()
    (internal / "weapons.json").write_text("{}")
    (internal / "base_library.zip").write_text("")

    exe = tmp_path / "SquadBallistics.exe"
    exe.write_text("")

    monkeypatch.setattr(updater.sys, "executable", str(exe))

    # Running from source: nothing is touched.
    updater.remove_old_install_files()
    assert internal.exists()

    monkeypatch.setattr(updater, "is_frozen", lambda: True)

    # A folder build that still uses _internal: nothing is touched.
    monkeypatch.setattr(updater.sys, "_MEIPASS", str(internal), raising=False)
    updater.remove_old_install_files()
    assert internal.exists()

    # Single-file build extracted elsewhere: the leftovers go away.
    monkeypatch.setattr(updater.sys, "_MEIPASS", str(tmp_path / "tmp"))
    updater.remove_old_install_files()
    assert not internal.exists()


def test_cleanup_ignores_foreign_folders(tmp_path, monkeypatch):
    internal = tmp_path / "_internal"
    internal.mkdir()
    (internal / "something.txt").write_text("not ours")

    monkeypatch.setattr(updater.sys, "executable", str(tmp_path / "x.exe"))
    monkeypatch.setattr(updater, "is_frozen", lambda: True)
    monkeypatch.setattr(updater.sys, "_MEIPASS", str(tmp_path / "tmp"),
                        raising=False)

    updater.remove_old_install_files()
    assert internal.exists()
