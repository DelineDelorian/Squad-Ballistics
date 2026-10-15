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
