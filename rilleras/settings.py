"""Persisted user settings (settings.json next to the app)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .core import PRESETS


def app_dir() -> Path:
    """Folder the app 'lives' in — next to the .exe when frozen, else the repo root."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def resource_path(name: str) -> Path:
    """Locate a bundled resource, both frozen (PyInstaller _MEIPASS) and from source."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")) / name
    return app_dir() / name


SETTINGS_FILE = app_dir() / "settings.json"

DEFAULT_SETTINGS = {
    "remember_paths": True,
    "open_output_after_run": False,
    "confirm_overwrite": True,
    "recent_inputs": [],
    "recent_max": 10,

    "last_mode": "word_to_images",
    "last_preset": list(PRESETS.keys())[0],
    "last_in_path": "",
    "last_out_path": "",

    "dpi": "300",
    "fmt": "png",
    "jpg_quality": 90,
    "page_range": "all",
    "recursive": True,
    "sort_mode": "natural",

    "batch_img_fmt": "jpg",
    "resize_max": "1600",
    "resize_quality": "80",
    "rotate_deg": 90,
    "split_mode": "each",
    "split_ranges": "1-3,4-7",
    "compress_mode": "clean",
    "compress_dpi": "150",
}


def load_settings() -> dict:
    data = {}
    if SETTINGS_FILE.exists():
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    merged = dict(DEFAULT_SETTINGS)
    merged.update(data if isinstance(data, dict) else {})

    if merged.get("last_preset") not in PRESETS:
        merged["last_preset"] = list(PRESETS.keys())[0]
    if not isinstance(merged.get("recent_inputs"), list):
        merged["recent_inputs"] = []
    try:
        merged["recent_max"] = int(merged.get("recent_max", 10))
    except Exception:
        merged["recent_max"] = 10

    return merged


def save_settings(data: dict):
    try:
        SETTINGS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass
