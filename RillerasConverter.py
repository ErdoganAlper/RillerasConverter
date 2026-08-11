"""Rilleras Converter — launcher.

Keeps only stdlib imports at module level so that missing third-party packages
can be installed automatically before the real app is imported. That is what
makes a plain `python RillerasConverter.py` work on a fresh machine.
"""

from __future__ import annotations

import importlib
import importlib.util
import queue
import subprocess
import sys
import threading
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent

# import name -> pip requirement. Order matters only for readability.
REQUIRED = [
    ("fitz", "PyMuPDF>=1.24.0"),
    ("PIL", "Pillow>=10.2.0"),
    ("img2pdf", "img2pdf>=0.5.1"),
    ("pdf2docx", "pdf2docx>=0.5.8"),
    ("docx", "python-docx>=1.1.0"),
    ("docx2pdf", "docx2pdf>=0.1.8"),
]
# Nice to have; the app degrades gracefully without it.
OPTIONAL = [("tkinterdnd2", "tkinterdnd2>=0.4.2")]


class _NullStream:
    """pythonw.exe / PyInstaller --windowed give us no stdout at all."""

    def write(self, _):
        return 0

    def flush(self):
        return None


if sys.stdout is None:
    sys.stdout = _NullStream()
if sys.stderr is None:
    sys.stderr = _NullStream()


def _missing(pairs) -> list[tuple[str, str]]:
    out = []
    for module, requirement in pairs:
        try:
            found = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError):
            found = False
        if not found:
            out.append((module, requirement))
    return out


def _pip_install(requirements: list[str], on_line) -> bool:
    """Install into the running interpreter, streaming output to ``on_line``."""
    cmd = [sys.executable, "-m", "pip", "install", "--disable-pip-version-check", *requirements]
    on_line("> " + " ".join(requirements))
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception as e:
        on_line(f"Could not start pip: {e}")
        return False

    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.rstrip()
        if line:
            on_line(line)
    return proc.wait() == 0


def _install_window(missing: list[tuple[str, str]], optional: list[tuple[str, str]]) -> bool:
    """Show a small progress window while pip runs. Returns True on success."""
    import tkinter as tk
    from tkinter import ttk

    BG, SURFACE, TEXT, MUTED, ACCENT = "#0C0E14", "#181C28", "#E8ECF6", "#6E7994", "#6C8CFF"

    root = tk.Tk()
    root.title("Rilleras Converter — first run setup")
    root.configure(bg=BG)
    root.geometry("640x400")
    root.resizable(False, False)

    tk.Label(root, text="Installing required components",
             bg=BG, fg=TEXT, font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=24, pady=(22, 2))
    tk.Label(root, text="This happens once. It needs an internet connection.",
             bg=BG, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w", padx=24)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("Setup.Horizontal.TProgressbar", troughcolor=SURFACE, background=ACCENT,
                    bordercolor=SURFACE, lightcolor=ACCENT, darkcolor=ACCENT, thickness=6)

    bar = ttk.Progressbar(root, mode="indeterminate", style="Setup.Horizontal.TProgressbar")
    bar.pack(fill="x", padx=24, pady=16)
    bar.start(12)

    log = tk.Text(root, bg=SURFACE, fg=MUTED, font=("Consolas", 8), relief="flat",
                  padx=12, pady=10, height=14, wrap="none")
    log.pack(fill="both", expand=True, padx=24, pady=(0, 20))
    log.configure(state="disabled")

    ui: queue.Queue = queue.Queue()
    result = {"ok": False, "done": False}

    def worker():
        ok = _pip_install([req for _, req in missing], ui.put)
        if ok and optional:
            ui.put("")
            ui.put("Installing optional extras…")
            # Failure here is fine — the app runs without drag & drop.
            _pip_install([req for _, req in optional], ui.put)
        result["ok"] = ok
        result["done"] = True

    threading.Thread(target=worker, daemon=True).start()

    def pump():
        try:
            while True:
                line = ui.get_nowait()
                log.configure(state="normal")
                log.insert("end", line + "\n")
                log.see("end")
                log.configure(state="disabled")
        except queue.Empty:
            pass

        if result["done"]:
            bar.stop()
            root.after(400, root.destroy)
            return
        root.after(100, pump)

    root.after(100, pump)
    root.mainloop()
    return result["ok"]


def _fatal(message: str):
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Rilleras Converter", message)
        root.destroy()
    except Exception:
        print(message)
    sys.exit(1)


def ensure_dependencies():
    """Install anything missing, so a fresh checkout just runs."""
    if getattr(sys, "frozen", False):
        return  # the .exe already bundles everything

    missing = _missing(REQUIRED)
    optional_missing = _missing(OPTIONAL)
    if not missing:
        return

    names = "\n".join(f"  • {req}" for _, req in missing)
    ok = _install_window(missing, optional_missing)
    importlib.invalidate_caches()

    still_missing = _missing(REQUIRED)
    if still_missing:
        reqs = " ".join(req for _, req in still_missing)
        _fatal(
            "Some components could not be installed automatically:\n\n"
            f"{names}\n\n"
            "Check your internet connection, then install them manually with:\n\n"
            f"    {Path(sys.executable).name} -m pip install {reqs}\n"
        )
    if not ok:
        # pip reported failure but the imports resolved anyway — carry on.
        pass


def main():
    ensure_dependencies()
    if str(APP_ROOT) not in sys.path:
        sys.path.insert(0, str(APP_ROOT))
    try:
        from rilleras.app import main as run_app
    except Exception as e:  # pragma: no cover - startup diagnostics
        import traceback

        _fatal(f"Rilleras Converter failed to start.\n\n{e}\n\n{traceback.format_exc()}")
        return
    run_app()


if __name__ == "__main__":
    main()
