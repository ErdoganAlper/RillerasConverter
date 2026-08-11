"""Settings persistence.

``SETTINGS_FILE`` is monkeypatched to a temp path in every test — otherwise the
suite would overwrite the real settings.json sitting next to the app.
"""

from __future__ import annotations

import json

import pytest

from rilleras import settings as settings_module


@pytest.fixture()
def settings_file(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", path)
    return path


def test_defaults_when_no_file(settings_file):
    loaded = settings_module.load_settings()
    assert loaded["language"] == "en"
    assert loaded["remember_paths"] is True


def test_round_trip(settings_file):
    settings_module.save_settings({"language": "tr", "dpi": "150"})
    loaded = settings_module.load_settings()

    assert loaded["language"] == "tr"
    assert loaded["dpi"] == "150"
    # keys absent from the file still come back from the defaults
    assert "sort_mode" in loaded


def test_unknown_language_falls_back(settings_file):
    settings_file.write_text(json.dumps({"language": "klingon"}), encoding="utf-8")
    assert settings_module.load_settings()["language"] == "en"


def test_unknown_preset_falls_back(settings_file):
    settings_file.write_text(json.dumps({"last_preset": "Nonexistent"}), encoding="utf-8")
    loaded = settings_module.load_settings()
    from rilleras.core import PRESETS

    assert loaded["last_preset"] in PRESETS


def test_corrupt_file_falls_back_to_defaults(settings_file):
    settings_file.write_text("{not valid json", encoding="utf-8")
    loaded = settings_module.load_settings()
    assert loaded["language"] == "en"
    assert loaded["recent_inputs"] == []


def test_wrong_types_are_repaired(settings_file):
    settings_file.write_text(
        json.dumps({"recent_inputs": "not-a-list", "recent_max": "oops"}), encoding="utf-8")
    loaded = settings_module.load_settings()

    assert loaded["recent_inputs"] == []
    assert loaded["recent_max"] == 10


def test_settings_dir_is_the_repo_when_running_from_source():
    assert settings_module.settings_dir() == settings_module.app_dir()


def test_frozen_build_stores_settings_in_appdata(tmp_path, monkeypatch):
    """An installed copy may live in Program Files, which is read-only."""
    monkeypatch.setattr(settings_module.sys, "frozen", True, raising=False)
    monkeypatch.setenv("APPDATA", str(tmp_path))

    target = settings_module.settings_dir()

    assert target == tmp_path / "RillerasConverter"
    assert target.is_dir()  # created on demand


def test_frozen_build_falls_back_when_appdata_is_unusable(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_module.sys, "frozen", True, raising=False)
    monkeypatch.delenv("APPDATA", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)

    # No writable profile folder: fall back rather than raising.
    assert settings_module.settings_dir() == settings_module.app_dir()


def test_save_failure_is_swallowed(settings_file, monkeypatch):
    """A read-only install folder must not crash the app on exit."""
    def boom(*_args, **_kwargs):
        raise PermissionError("read-only")

    monkeypatch.setattr(type(settings_file), "write_text", boom)
    settings_module.save_settings({"language": "tr"})  # must not raise
