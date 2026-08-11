"""The Rilleras Converter desktop UI."""

from __future__ import annotations

import queue
import threading
import traceback
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import __version__, core, i18n
from .core import (
    IMAGE_EXTS, OUT_IMAGE_FORMATS, PRESETS, Cancelled, ConversionError,
)
from .i18n import t
from .modes import (
    GROUPS, GROUP_BATCH, GROUP_IMAGE, GROUP_MAIN, GROUP_PDF,
    IN_DOCX, IN_FOLDER, IN_IMAGE_OR_FOLDER, IN_NONE, IN_PDF, MODES,
    OPT_COMPRESS, OPT_IMAGE_OUT, OPT_MERGE, OPT_PAGES, OPT_RECURSIVE,
    OPT_RENDER, OPT_ROTATE, OPT_SORT, OPT_SPLIT,
    OUT_DOCX, OUT_FOLDER, OUT_IMAGE, OUT_IMAGE_OR_FOLDER, OUT_PDF, OUT_TXT,
    group_heading, group_of, modes_in_group,
)
from .settings import load_settings, resource_path, save_settings, settings_dir
from .theme import (
    C, Card, F_H1, F_MONO, F_SMALL, F_TINY, ModeCard, NavButton,
    ScrollFrame, StatusPill, apply_theme,
)

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except Exception:
    HAS_DND = False

BaseTk = TkinterDnD.Tk if HAS_DND else tk.Tk

IMAGE_PATTERNS = "*.jpg *.jpeg *.png *.webp *.tif *.tiff *.bmp"


def log_time() -> str:
    return datetime.now().strftime("%H:%M:%S")


class App(BaseTk):
    def __init__(self):
        super().__init__()

        self._settings = load_settings()
        i18n.set_language(self._settings.get("language", i18n.DEFAULT_LANGUAGE))

        self.title(f"Rilleras Converter {__version__}")
        self.geometry("1120x780")
        self.minsize(980, 660)
        icon = resource_path("convert.ico")
        if icon.exists():
            try:
                self.iconbitmap(default=str(icon))
            except tk.TclError:
                pass

        apply_theme(self)

        self.ui_queue: queue.Queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker_thread: threading.Thread | None = None

        self._init_vars()

        self.merge_list: list[Path] = []
        self._mode_cards: dict[str, ModeCard] = {}
        self._nav_buttons: dict[str, NavButton] = {}
        self._current_view = ""
        self._current_group = group_of(self.mode_var.get())

        self._build_ui()
        self._select_view(self._current_group)
        self._on_mode_changed(persist=False)
        self._refresh_recent_inputs_ui()
        self._poll_queue()

        if HAS_DND:
            self._enable_dnd()

        self._log(t("log.ready"), kind="ok")
        if not HAS_DND:
            self._log(t("log.dnd_missing"), kind="muted")

    # ------------------------------------------------------------- state --

    def _init_vars(self):
        s = self._settings
        self.preset_var = tk.StringVar(value=s["last_preset"])
        self.mode_var = tk.StringVar(value=s["last_mode"] if s["last_mode"] in MODES else "pdf_to_word")
        self.in_path = tk.StringVar()
        self.out_path = tk.StringVar()
        self.language_var = tk.StringVar(
            value=i18n.LANGUAGES.get(i18n.get_language(), "English"))

        self.dpi_var = tk.StringVar(value=str(s["dpi"]))
        self.fmt_var = tk.StringVar(value=str(s["fmt"]))
        self.jpg_quality_var = tk.IntVar(value=int(s["jpg_quality"]))
        self.page_range_var = tk.StringVar(value=str(s["page_range"]))
        self.recursive_var = tk.BooleanVar(value=bool(s["recursive"]))
        self.sort_mode_var = tk.StringVar(value=str(s["sort_mode"]))

        self.batch_img_fmt_var = tk.StringVar(value=str(s.get("batch_img_fmt", "jpg")))
        self.resize_max_var = tk.StringVar(value=str(s.get("resize_max", "1600")))
        self.resize_quality_var = tk.StringVar(value=str(s.get("resize_quality", "80")))

        self.rotate_deg_var = tk.IntVar(value=int(s.get("rotate_deg", 90)))
        self.split_mode_var = tk.StringVar(value=str(s.get("split_mode", "each")))
        self.split_ranges_var = tk.StringVar(value=str(s.get("split_ranges", "1-3,4-7")))
        self.compress_mode_var = tk.StringVar(value=str(s.get("compress_mode", "clean")))
        self.compress_dpi_var = tk.StringVar(value=str(s.get("compress_dpi", "150")))

        self.remember_paths_var = tk.BooleanVar(value=bool(s.get("remember_paths", True)))
        self.open_output_after_run_var = tk.BooleanVar(value=bool(s.get("open_output_after_run", False)))
        self.confirm_overwrite_var = tk.BooleanVar(value=bool(s.get("confirm_overwrite", True)))

        self.recent_inputs = list(s.get("recent_inputs", []))
        self.recent_max = int(s.get("recent_max", 10) or 10)

        if self.remember_paths_var.get():
            self.in_path.set(s.get("last_in_path", ""))
            self.out_path.set(s.get("last_out_path", ""))

    # ---------------------------------------------------------------- UI --

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_header()

        body = tk.Frame(self, bg=C.BG_DEEP)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_sidebar(body)

        self.content = tk.Frame(body, bg=C.BG)
        self.content.grid(row=0, column=1, sticky="nsew")

        self._build_convert_view()
        self._build_settings_view()
        self._build_log_view()
        self._build_footer()

    def _build_header(self):
        head = tk.Frame(self, bg=C.BG_DEEP)
        head.grid(row=0, column=0, sticky="ew")
        head.columnconfigure(1, weight=1)

        left = tk.Frame(head, bg=C.BG_DEEP)
        left.grid(row=0, column=0, sticky="w", padx=(22, 0), pady=16)
        tk.Label(left, text="Rilleras", bg=C.BG_DEEP, fg=C.TEXT, font=F_H1).pack(side="left")
        tk.Label(left, text="Converter", bg=C.BG_DEEP, fg=C.ACCENT, font=F_H1).pack(side="left", padx=(6, 0))
        tk.Label(left, text=f"v{__version__}", bg=C.BG_DEEP, fg=C.TEXT_MUTED,
                 font=F_TINY).pack(side="left", padx=(10, 0), pady=(6, 0))

        right = tk.Frame(head, bg=C.BG_DEEP)
        right.grid(row=0, column=2, sticky="e", padx=(0, 22), pady=16)
        tk.Label(right, text=t("header.preset"), bg=C.BG_DEEP, fg=C.TEXT_MUTED,
                 font=F_SMALL).pack(side="left", padx=(0, 9))
        cb = ttk.Combobox(right, textvariable=self.preset_var, values=list(PRESETS.keys()),
                          state="readonly", width=30)
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda e: self._apply_preset(self.preset_var.get()))

        tk.Frame(self, bg=C.BORDER_SOFT, height=1).grid(row=0, column=0, sticky="sew")

    def _build_sidebar(self, parent):
        bar = tk.Frame(parent, bg=C.BG_DEEP, width=212)
        bar.grid(row=0, column=0, sticky="nsw")
        bar.grid_propagate(False)

        items = [
            (GROUP_MAIN, "🔁"),
            (GROUP_PDF, "📕"),
            (GROUP_IMAGE, "🎨"),
            (GROUP_BATCH, "📦"),
            ("settings", "⚙️"),
            ("log", "📋"),
        ]
        tk.Frame(bar, bg=C.BG_DEEP, height=8).pack(fill="x")
        for key, icon in items:
            if key == "settings":
                tk.Frame(bar, bg=C.BORDER_SOFT, height=1).pack(fill="x", padx=16, pady=10)
            btn = NavButton(bar, icon, t(f"nav.{key}"), command=lambda k=key: self._select_view(k))
            btn.pack(fill="x")
            self._nav_buttons[key] = btn

        foot = tk.Frame(bar, bg=C.BG_DEEP)
        foot.pack(side="bottom", fill="x", pady=14, padx=16)
        tk.Label(
            foot,
            text=t("sidebar.drop_hint") if HAS_DND else t("sidebar.dnd_off"),
            bg=C.BG_DEEP, fg=C.TEXT_MUTED, font=F_TINY, justify="left", anchor="w",
        ).pack(anchor="w")

        tk.Frame(parent, bg=C.BORDER_SOFT, width=1).grid(row=0, column=0, sticky="nse")

    # ---- convert view (mode grid + files + options) ----

    def _build_convert_view(self):
        self.convert_view = ScrollFrame(self.content)
        body = self.convert_view.body

        # The subtitle is retitled per group; it must be non-empty here so that
        # Card actually creates the label to write into later.
        self.mode_panel = Card(body, t("panel.choose"), " ")
        self.mode_panel.pack(fill="x", padx=24, pady=(20, 0))
        self.mode_grid = tk.Frame(self.mode_panel.body, bg=C.SURFACE)
        self.mode_grid.pack(fill="x")

        self._build_files_card(body)
        self._build_merge_card(body)
        self._build_options_card(body)

        tk.Frame(body, bg=C.BG, height=16).pack(fill="x")

    def _build_files_card(self, parent):
        self.files_card = Card(parent, t("card.files.title"), t("card.files.sub"))
        self.files_card.pack(fill="x", padx=24, pady=(16, 0))
        b = self.files_card.body
        b.columnconfigure(1, weight=1)

        tk.Label(b, text=t("field.recent"), bg=C.SURFACE, fg=C.TEXT_MUTED, font=F_SMALL)\
            .grid(row=0, column=0, sticky="w", pady=(0, 10))
        self.recent_cb = ttk.Combobox(b, values=[], state="readonly")
        self.recent_cb.grid(row=0, column=1, sticky="ew", padx=(14, 10), pady=(0, 10))
        self.recent_cb.bind("<<ComboboxSelected>>", lambda e: self._choose_recent_input())
        ttk.Button(b, text=t("btn.clear"), style="Card.TButton", command=self._clear_recent_inputs)\
            .grid(row=0, column=2, sticky="e", pady=(0, 10))

        self.lbl_in = tk.Label(b, text=t("field.input"), bg=C.SURFACE, fg=C.TEXT_DIM,
                               font=F_SMALL, anchor="w")
        self.lbl_in.grid(row=1, column=0, sticky="w", pady=6)
        self.entry_in = ttk.Entry(b, textvariable=self.in_path)
        self.entry_in.grid(row=1, column=1, sticky="ew", padx=(14, 10), pady=6)
        self.btn_browse_in = ttk.Button(b, text=t("btn.browse"), style="Card.TButton",
                                        command=self._browse_input)
        self.btn_browse_in.grid(row=1, column=2, sticky="e", pady=6)

        self.lbl_out = tk.Label(b, text=t("field.output"), bg=C.SURFACE, fg=C.TEXT_DIM,
                                font=F_SMALL, anchor="w")
        self.lbl_out.grid(row=2, column=0, sticky="w", pady=6)
        self.entry_out = ttk.Entry(b, textvariable=self.out_path)
        self.entry_out.grid(row=2, column=1, sticky="ew", padx=(14, 10), pady=6)
        ttk.Button(b, text=t("btn.browse"), style="Card.TButton", command=self._browse_output)\
            .grid(row=2, column=2, sticky="e", pady=6)

        self.mode_hint = tk.Label(b, text="", bg=C.SURFACE, fg=C.TEXT_MUTED,
                                  font=F_TINY, anchor="w", justify="left")
        self.mode_hint.grid(row=3, column=0, columnspan=3, sticky="w", pady=(10, 0))

        self.word_badge = tk.Label(b, text=t("badge.requires_word"),
                                   bg="#2A2418", fg=C.WARN, font=F_TINY, anchor="w")
        self._word_badge_row = 4  # gridded on demand by _on_mode_changed

    def _build_merge_card(self, parent):
        self.merge_card = Card(parent, t("card.merge.title"), t("card.merge.sub"))
        b = self.merge_card.body

        btns = tk.Frame(b, bg=C.SURFACE)
        btns.pack(fill="x", pady=(0, 10))
        for label, cmd in (
            (t("btn.add_pdfs"), self._merge_add),
            (t("btn.move_up"), lambda: self._merge_move(-1)),
            (t("btn.move_down"), lambda: self._merge_move(1)),
            (t("btn.remove"), self._merge_remove),
            (t("btn.clear"), self._merge_clear),
        ):
            ttk.Button(btns, text=label, style="Card.TButton", command=cmd)\
                .pack(side="left", padx=(0, 8))

        self.merge_box = tk.Listbox(
            b, height=7, bg=C.SURFACE_2, fg=C.TEXT, font=F_SMALL,
            selectbackground=C.ACCENT_DEEP, selectforeground="#FFFFFF",
            highlightthickness=1, highlightbackground=C.BORDER, highlightcolor=C.ACCENT,
            bd=0, activestyle="none",
        )
        self.merge_box.pack(fill="x")

    def _build_options_card(self, parent):
        self.options_card = Card(parent, t("card.options.title"), t("card.options.sub"))
        b = self.options_card.body
        self._option_rows: dict[str, tk.Frame] = {}

        def row(key: str) -> tk.Frame:
            f = tk.Frame(b, bg=C.SURFACE)
            self._option_rows[key] = f
            return f

        def label(parent_, text: str):
            return tk.Label(parent_, text=text, bg=C.SURFACE, fg=C.TEXT_MUTED, font=F_SMALL)

        def hint(parent_, text: str):
            return tk.Label(parent_, text=text, bg=C.SURFACE, fg=C.TEXT_MUTED, font=F_TINY)

        r = row(OPT_RENDER)
        label(r, t("opt.dpi")).pack(side="left")
        ttk.Entry(r, textvariable=self.dpi_var, width=7).pack(side="left", padx=(10, 22))
        label(r, t("opt.format")).pack(side="left")
        ttk.Combobox(r, textvariable=self.fmt_var, values=["png", "jpg"],
                     state="readonly", width=6).pack(side="left", padx=(10, 22))
        label(r, t("opt.jpg_quality")).pack(side="left")
        self.quality_value = tk.Label(r, text=str(self.jpg_quality_var.get()),
                                      bg=C.SURFACE, fg=C.ACCENT, font=F_SMALL, width=3)
        self.quality_value.pack(side="right")
        ttk.Scale(r, from_=50, to=95, orient="horizontal", variable=self.jpg_quality_var,
                  command=self._on_quality_slide).pack(side="left", padx=(10, 10),
                                                       fill="x", expand=True)

        r = row(OPT_PAGES)
        label(r, t("opt.pages")).pack(side="left")
        ttk.Entry(r, textvariable=self.page_range_var, width=22).pack(side="left", padx=(10, 12))
        hint(r, t("opt.pages_hint")).pack(side="left")

        r = row(OPT_RECURSIVE)
        ttk.Checkbutton(r, text=t("opt.recursive"), variable=self.recursive_var).pack(side="left")

        r = row(OPT_SORT)
        label(r, t("opt.sort")).pack(side="left")
        ttk.Combobox(r, textvariable=self.sort_mode_var, values=["natural", "name", "mtime"],
                     state="readonly", width=12).pack(side="left", padx=(10, 12))
        hint(r, t("opt.sort_hint")).pack(side="left")

        r = row(OPT_IMAGE_OUT)
        label(r, t("opt.save_as")).pack(side="left")
        ttk.Combobox(r, textvariable=self.batch_img_fmt_var, values=OUT_IMAGE_FORMATS,
                     state="readonly", width=7).pack(side="left", padx=(10, 22))
        label(r, t("opt.max_size")).pack(side="left")
        ttk.Entry(r, textvariable=self.resize_max_var, width=8).pack(side="left", padx=(10, 22))
        label(r, t("opt.quality")).pack(side="left")
        ttk.Entry(r, textvariable=self.resize_quality_var, width=6).pack(side="left", padx=(10, 0))

        r = row(OPT_ROTATE)
        label(r, t("opt.rotate_by")).pack(side="left")
        ttk.Combobox(r, textvariable=self.rotate_deg_var, values=[90, 180, 270],
                     state="readonly", width=6).pack(side="left", padx=(10, 8))
        hint(r, t("opt.degrees_cw")).pack(side="left")

        r = row(OPT_SPLIT)
        label(r, t("opt.split")).pack(side="left")
        ttk.Combobox(r, textvariable=self.split_mode_var, values=["each", "ranges"],
                     state="readonly", width=9).pack(side="left", padx=(10, 22))
        label(r, t("opt.ranges")).pack(side="left")
        ttk.Entry(r, textvariable=self.split_ranges_var, width=30).pack(side="left", padx=(10, 12))
        hint(r, t("opt.ranges_hint")).pack(side="left")

        r = row(OPT_COMPRESS)
        label(r, t("opt.method")).pack(side="left")
        ttk.Combobox(r, textvariable=self.compress_mode_var, values=["clean", "rebuild"],
                     state="readonly", width=9).pack(side="left", padx=(10, 22))
        label(r, t("opt.rebuild_dpi")).pack(side="left")
        ttk.Entry(r, textvariable=self.compress_dpi_var, width=8).pack(side="left", padx=(10, 12))
        hint(r, t("opt.compress_hint")).pack(side="left")

    # ---- settings view ----

    def _build_settings_view(self):
        self.settings_view = ScrollFrame(self.content)
        body = self.settings_view.body

        lang_card = Card(body, t("card.language"), "")
        lang_card.pack(fill="x", padx=24, pady=(20, 0))
        lb = lang_card.body
        self.language_cb = ttk.Combobox(lb, textvariable=self.language_var,
                                        values=list(i18n.LANGUAGES.values()),
                                        state="readonly", width=24)
        self.language_cb.pack(anchor="w")
        self.language_cb.bind("<<ComboboxSelected>>", lambda e: self._on_language_changed())
        tk.Label(lb, text=t("settings.language_hint"), bg=C.SURFACE, fg=C.TEXT_MUTED,
                 font=F_TINY, anchor="w").pack(anchor="w", pady=(8, 0))

        card = Card(body, t("card.behaviour"), "")
        card.pack(fill="x", padx=24, pady=(16, 0))
        for text, var in [
            (t("settings.remember_paths"), self.remember_paths_var),
            (t("settings.open_after"), self.open_output_after_run_var),
            (t("settings.confirm_overwrite"), self.confirm_overwrite_var),
        ]:
            ttk.Checkbutton(card.body, text=text, variable=var,
                            command=self._persist_settings).pack(anchor="w", pady=5)

        card2 = Card(body, t("card.storage"), "")
        card2.pack(fill="x", padx=24, pady=(16, 0))
        tk.Label(card2.body,
                 text=t("settings.file_location", path=settings_dir() / "settings.json"),
                 bg=C.SURFACE, fg=C.TEXT_MUTED, font=F_TINY, anchor="w",
                 justify="left").pack(anchor="w", pady=(0, 10))
        ttk.Button(card2.body, text=t("btn.open_settings_folder"), style="Card.TButton",
                   command=lambda: core.open_in_explorer(settings_dir())).pack(anchor="w")

        card3 = Card(body, t("card.about"), "")
        card3.pack(fill="x", padx=24, pady=(16, 20))
        dnd_state = t("about.dnd_on") if HAS_DND else t("about.dnd_off")
        for line in [
            t("about.version", version=__version__),
            t("about.dnd", state=dnd_state),
            t("about.word"),
            t("about.pdf2docx"),
        ]:
            tk.Label(card3.body, text=line, bg=C.SURFACE, fg=C.TEXT_DIM, font=F_SMALL,
                     anchor="w", justify="left").pack(anchor="w", pady=2)

    # ---- log view ----

    def _build_log_view(self):
        self.log_view = tk.Frame(self.content, bg=C.BG)

        card = Card(self.log_view, t("card.log.title"), "")
        card.pack(fill="both", expand=True, padx=24, pady=20)
        b = card.body

        bar = tk.Frame(b, bg=C.SURFACE)
        bar.pack(fill="x", pady=(0, 10))
        ttk.Button(bar, text=t("btn.clear"), style="Card.TButton",
                   command=self._clear_log).pack(side="left")
        ttk.Button(bar, text=t("btn.copy_all"), style="Card.TButton",
                   command=self._copy_log).pack(side="left", padx=(8, 0))

        wrap = tk.Frame(b, bg=C.SURFACE_2, highlightthickness=1,
                        highlightbackground=C.BORDER, bd=0)
        wrap.pack(fill="both", expand=True)

        self.log = tk.Text(wrap, wrap="word", bg=C.SURFACE_2, fg=C.TEXT_DIM,
                           insertbackground=C.ACCENT, font=F_MONO,
                           relief="flat", padx=12, pady=10, height=18)
        scroll = ttk.Scrollbar(wrap, orient="vertical", command=self.log.yview,
                               style="Vertical.TScrollbar")
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)

        for tag, colour in (("time", C.TEXT_MUTED), ("info", C.TEXT_DIM), ("ok", C.SUCCESS),
                            ("err", C.DANGER), ("muted", C.TEXT_MUTED)):
            self.log.tag_configure(tag, foreground=colour)
        self.log.configure(state="disabled")

    # ---- footer ----

    def _build_footer(self):
        self.progress = ttk.Progressbar(self, mode="determinate",
                                        style="Accent.Horizontal.TProgressbar")
        self.progress.grid(row=2, column=0, sticky="ew")

        foot = tk.Frame(self, bg=C.BG_DEEP)
        foot.grid(row=3, column=0, sticky="ew")
        foot.columnconfigure(1, weight=1)

        self.status = StatusPill(foot)
        self.status.set_state("idle", t("status.ready"))
        self.status.grid(row=0, column=0, sticky="w", padx=(22, 0), pady=14)

        self.detail = tk.Label(foot, text="", bg=C.BG_DEEP, fg=C.TEXT_MUTED, font=F_SMALL)
        self.detail.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=14)

        right = tk.Frame(foot, bg=C.BG_DEEP)
        right.grid(row=0, column=2, sticky="e", padx=(0, 22), pady=14)

        self.btn_open = ttk.Button(right, text=t("btn.open_output"),
                                   command=self._open_output, state="disabled")
        self.btn_open.pack(side="left", padx=(0, 10))
        self.btn_cancel = ttk.Button(right, text=t("btn.cancel"), command=self._cancel,
                                     state="disabled")
        self.btn_cancel.pack(side="left", padx=(0, 10))
        self.btn_run = ttk.Button(right, text=t("btn.run"), style="Accent.TButton",
                                  command=self._run)
        self.btn_run.pack(side="left")

    # ------------------------------------------------------- language ----

    def _on_language_changed(self):
        chosen = self.language_var.get()
        code = next((c for c, name in i18n.LANGUAGES.items() if name == chosen),
                    i18n.DEFAULT_LANGUAGE)
        if code == i18n.get_language():
            return
        i18n.set_language(code)
        self._persist_settings()
        self._rebuild_ui()
        self._log(t("log.language_changed", name=chosen), kind="muted")

    def _rebuild_ui(self):
        """Tear the window down and rebuild it in the newly chosen language.

        Every widget caches its text at creation time, so re-creating them is
        far more reliable than trying to re-label ~120 widgets individually.
        Tk variables are not widgets, so all user input survives untouched.
        """
        previous_log = self.log.get("1.0", "end").rstrip("\n")
        view = self._current_view

        for child in self.winfo_children():
            child.destroy()
        self._nav_buttons.clear()
        self._mode_cards.clear()

        self._build_ui()
        self._select_view(view if view in self._nav_buttons else self._current_group)
        self._on_mode_changed(persist=False)
        self._refresh_recent_inputs_ui()
        self._merge_refresh()
        self._on_quality_slide()

        if previous_log:
            self.log.configure(state="normal")
            self.log.insert("end", previous_log + "\n")
            self.log.see("end")
            self.log.configure(state="disabled")

        running = self.worker_thread is not None and self.worker_thread.is_alive()
        self._set_working(running)

    # ------------------------------------------------------ view switching --

    def _select_view(self, key: str):
        for name, btn in self._nav_buttons.items():
            btn.set_active(name == key)

        for view in (self.convert_view, self.settings_view, self.log_view):
            view.pack_forget()

        if key in GROUPS:
            self._current_group = key
            self._rebuild_mode_grid(key)
            if group_of(self.mode_var.get()) != key:
                self.mode_var.set(modes_in_group(key)[0].key)
                self._on_mode_changed()
            else:
                self._sync_mode_selection()
            self.convert_view.pack(fill="both", expand=True)
        elif key == "settings":
            self.settings_view.pack(fill="both", expand=True)
        else:
            self.log_view.pack(fill="both", expand=True)

        self._current_view = key

    def _rebuild_mode_grid(self, group: str):
        for child in self.mode_grid.winfo_children():
            child.destroy()
        self._mode_cards.clear()

        self._set_panel_heading(*group_heading(group))

        cols = 3
        for i in range(cols):
            self.mode_grid.columnconfigure(i, weight=1, uniform="modes")

        for idx, spec in enumerate(modes_in_group(group)):
            card = ModeCard(self.mode_grid, spec, command=self._on_mode_card_clicked)
            card.grid(row=idx // cols, column=idx % cols, sticky="nsew",
                      padx=(0 if idx % cols == 0 else 6, 0), pady=(0, 8))
            self._mode_cards[spec.key] = card

        self._sync_mode_selection()

    def _set_panel_heading(self, title: str, subtitle: str):
        # Card builds its header lazily; find the labels and retitle them.
        header = self.mode_panel.winfo_children()[0]
        labels = [w for w in header.winfo_children() if isinstance(w, tk.Label)]
        if labels:
            labels[0].configure(text=title)
        if len(labels) > 1:
            labels[1].configure(text=subtitle)

    def _sync_mode_selection(self):
        current = self.mode_var.get()
        for key, card in self._mode_cards.items():
            card.set_selected(key == current)

    def _on_mode_card_clicked(self, key: str):
        if self.mode_var.get() != key:
            self.mode_var.set(key)
        self._on_mode_changed()

    def _on_mode_changed(self, persist: bool = True):
        spec = MODES[self.mode_var.get()]
        self._sync_mode_selection()

        self.mode_hint.configure(text=f"{spec.input_label}   →   {spec.output_label}")

        show_input = spec.input_kind != IN_NONE
        state = "normal" if show_input else "disabled"
        self.entry_in.configure(state=state)
        self.btn_browse_in.configure(state=state)
        self.lbl_in.configure(fg=C.TEXT_DIM if show_input else C.TEXT_MUTED)

        if spec.requires_word:
            self.word_badge.grid(row=self._word_badge_row, column=0, columnspan=3,
                                 sticky="w", pady=(10, 0))
        else:
            self.word_badge.grid_remove()

        for frame in self._option_rows.values():
            frame.pack_forget()
        wanted = [k for k in (OPT_RENDER, OPT_PAGES, OPT_IMAGE_OUT, OPT_SORT,
                              OPT_RECURSIVE, OPT_ROTATE, OPT_SPLIT, OPT_COMPRESS)
                  if k in spec.options]
        for key in wanted:
            self._option_rows[key].pack(fill="x", pady=7)

        # Re-pack both cards in order so the merge list always sits above options.
        self.merge_card.pack_forget()
        self.options_card.pack_forget()
        if OPT_MERGE in spec.options:
            self.merge_card.pack(fill="x", padx=24, pady=(16, 0))
        if wanted:
            self.options_card.pack(fill="x", padx=24, pady=(16, 0))

        if persist:
            self._persist_settings()

    def _on_quality_slide(self, _value=None):
        self.quality_value.configure(text=str(int(self.jpg_quality_var.get())))

    # ----------------------------------------------------------- dnd/recent --

    def _enable_dnd(self):
        def on_drop(event):
            paths = self._parse_dnd_files(event.data)
            if not paths:
                return
            p = Path(paths[0])
            self.in_path.set(str(p))
            self._add_recent_input(p)

            suggestion = None
            if p.is_dir():
                suggestion = "images_to_pdf"
            else:
                ext = p.suffix.lower()
                if ext in core.DOCX_EXTS:
                    suggestion = "word_to_pdf"
                elif ext in core.PDF_EXTS:
                    suggestion = "pdf_to_word"
                elif ext in IMAGE_EXTS:
                    suggestion = "image_to_image"

            if suggestion:
                self.mode_var.set(suggestion)
                self._select_view(group_of(suggestion))
                self._on_mode_changed()
            self._log(t("log.loaded", path=p), kind="info")

        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", on_drop)

    def _parse_dnd_files(self, data: str) -> list[str]:
        parts, buf, in_brace = [], "", False
        for ch in data:
            if ch == "{":
                in_brace, buf = True, ""
            elif ch == "}":
                in_brace = False
                parts.append(buf)
                buf = ""
            elif ch == " " and not in_brace:
                if buf:
                    parts.append(buf)
                    buf = ""
            else:
                buf += ch
        if buf:
            parts.append(buf)
        return [p.strip() for p in parts if p.strip()]

    def _refresh_recent_inputs_ui(self):
        self.recent_cb["values"] = self.recent_inputs

    def _add_recent_input(self, p: Path):
        sp = str(p)
        self.recent_inputs = [x for x in self.recent_inputs if x != sp]
        self.recent_inputs.insert(0, sp)
        self.recent_inputs = self.recent_inputs[: max(1, self.recent_max)]
        self._refresh_recent_inputs_ui()
        self._persist_settings()

    def _choose_recent_input(self):
        chosen = self.recent_cb.get()
        if chosen:
            self.in_path.set(chosen)

    def _clear_recent_inputs(self):
        self.recent_inputs = []
        self._refresh_recent_inputs_ui()
        self.recent_cb.set("")
        self._persist_settings()

    # ------------------------------------------------------------ presets --

    def _apply_preset(self, name: str):
        p = PRESETS.get(name)
        if not p:
            return
        self.dpi_var.set(str(p["dpi"]))
        self.fmt_var.set(p["fmt"])
        self.jpg_quality_var.set(int(p["jpg_quality"]))
        self._on_quality_slide()
        self._log(t("log.preset_applied", name=name), kind="muted")
        self._persist_settings()

    def _persist_settings(self):
        remember = bool(self.remember_paths_var.get())
        data = dict(
            language=i18n.get_language(),
            remember_paths=remember,
            open_output_after_run=bool(self.open_output_after_run_var.get()),
            confirm_overwrite=bool(self.confirm_overwrite_var.get()),
            recent_inputs=list(self.recent_inputs),
            recent_max=int(self.recent_max),

            last_mode=self.mode_var.get(),
            last_preset=self.preset_var.get(),

            dpi=self.dpi_var.get(),
            fmt=self.fmt_var.get(),
            jpg_quality=int(self.jpg_quality_var.get()),
            page_range=self.page_range_var.get(),
            recursive=bool(self.recursive_var.get()),
            sort_mode=self.sort_mode_var.get(),

            batch_img_fmt=self.batch_img_fmt_var.get(),
            resize_max=self.resize_max_var.get(),
            resize_quality=self.resize_quality_var.get(),

            rotate_deg=int(self.rotate_deg_var.get()),
            split_mode=self.split_mode_var.get(),
            split_ranges=self.split_ranges_var.get(),
            compress_mode=self.compress_mode_var.get(),
            compress_dpi=self.compress_dpi_var.get(),

            last_in_path=self.in_path.get() if remember else "",
            last_out_path=self.out_path.get() if remember else "",
        )
        save_settings(data)

    # -------------------------------------------------------- merge list --

    def _merge_add(self):
        files = filedialog.askopenfilenames(title=t("dlg.select_pdfs_merge"),
                                            filetypes=[(t("filetype.pdf"), "*.pdf")])
        for f in files:
            p = Path(f)
            if p.exists() and p.suffix.lower() == ".pdf":
                self.merge_list.append(p)
        self._merge_refresh()

    def _merge_clear(self):
        self.merge_list = []
        self._merge_refresh()

    def _merge_remove(self):
        for i in reversed(list(self.merge_box.curselection())):
            del self.merge_list[i]
        self._merge_refresh()

    def _merge_move(self, delta: int):
        sel = list(self.merge_box.curselection())
        if len(sel) != 1:
            return
        i = sel[0]
        j = i + delta
        if not (0 <= j < len(self.merge_list)):
            return
        self.merge_list[i], self.merge_list[j] = self.merge_list[j], self.merge_list[i]
        self._merge_refresh()
        self.merge_box.selection_set(j)

    def _merge_refresh(self):
        self.merge_box.delete(0, tk.END)
        for p in self.merge_list:
            self.merge_box.insert(tk.END, str(p))

    # ---------------------------------------------------------- browsing --

    def _initial_dir(self) -> str:
        current = self.in_path.get().strip().strip('"')
        if current:
            p = Path(current)
            candidate = p if p.is_dir() else p.parent
            if candidate.exists():
                return str(candidate)
        return ""

    def _browse_input(self):
        spec = MODES[self.mode_var.get()]
        initial = self._initial_dir()
        p = ""

        if spec.input_kind == IN_NONE:
            messagebox.showinfo(t("dlg.merge_title"), t("dlg.merge_use_list"))
            return
        if spec.input_kind == IN_DOCX:
            p = filedialog.askopenfilename(title=t("dlg.select_word"),
                                           filetypes=[(t("filetype.word"), "*.docx")],
                                           initialdir=initial)
        elif spec.input_kind == IN_PDF:
            p = filedialog.askopenfilename(title=t("dlg.select_pdf"),
                                           filetypes=[(t("filetype.pdf"), "*.pdf")],
                                           initialdir=initial)
        elif spec.input_kind == IN_FOLDER:
            p = filedialog.askdirectory(title=t("dlg.select_folder"), initialdir=initial)
        elif spec.input_kind == IN_IMAGE_OR_FOLDER:
            if messagebox.askyesno(t("dlg.choose_input"), t("dlg.folder_or_file")):
                p = filedialog.askdirectory(title=t("dlg.select_images_folder"),
                                            initialdir=initial)
            else:
                p = filedialog.askopenfilename(title=t("dlg.select_image"),
                                               filetypes=[(t("filetype.images"), IMAGE_PATTERNS)],
                                               initialdir=initial)

        if p:
            self.in_path.set(p)
            self._add_recent_input(Path(p))
            self._persist_settings()

    def _browse_output(self):
        spec = MODES[self.mode_var.get()]
        initial = self._initial_dir()
        kind = spec.output_kind
        p = ""

        if kind == OUT_IMAGE_OR_FOLDER:
            in_txt = self.in_path.get().strip().strip('"')
            in_p = Path(in_txt) if in_txt else None
            kind = OUT_FOLDER if (in_p and in_p.is_dir()) else OUT_IMAGE

        if kind == OUT_FOLDER:
            p = filedialog.askdirectory(title=t("dlg.select_out_folder"), initialdir=initial)
        elif kind == OUT_PDF:
            p = filedialog.asksaveasfilename(title=t("dlg.save_pdf"), defaultextension=".pdf",
                                             filetypes=[(t("filetype.pdf"), "*.pdf")],
                                             initialdir=initial)
        elif kind == OUT_DOCX:
            p = filedialog.asksaveasfilename(title=t("dlg.save_docx"), defaultextension=".docx",
                                             filetypes=[(t("filetype.word"), "*.docx")],
                                             initialdir=initial)
        elif kind == OUT_TXT:
            p = filedialog.asksaveasfilename(title=t("dlg.save_txt"), defaultextension=".txt",
                                             filetypes=[(t("filetype.text"), "*.txt")],
                                             initialdir=initial)
        elif kind == OUT_IMAGE:
            if spec.key == "image_to_image":
                ext = "." + self.batch_img_fmt_var.get().lower()
                p = filedialog.asksaveasfilename(title=t("dlg.save_image"), defaultextension=ext,
                                                 filetypes=[(t("filetype.image"), "*" + ext)],
                                                 initialdir=initial)
            else:
                p = filedialog.asksaveasfilename(
                    title=t("dlg.save_image"), defaultextension=".png",
                    filetypes=[("PNG", "*.png"), ("JPG", "*.jpg")], initialdir=initial)

        if p:
            self.out_path.set(p)
            self._persist_settings()

    # ------------------------------------------------------------ logging --

    def _log(self, msg: str, kind: str = "info"):
        self.log.configure(state="normal")
        self.log.insert("end", f"[{log_time()}] ", ("time",))
        self.log.insert("end", msg + "\n", (kind,))
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _copy_log(self):
        self.clipboard_clear()
        self.clipboard_append(self.log.get("1.0", "end").strip())
        self._log(t("log.copied"), kind="muted")

    # ---------------------------------------------------------- run flow --

    def _set_working(self, working: bool):
        self.btn_run.config(state="disabled" if working else "normal")
        self.btn_cancel.config(state="normal" if working else "disabled")
        if working:
            self.btn_open.config(state="disabled")

    def _cancel(self):
        self.cancel_event.set()
        self._log(t("log.cancel_requested"), kind="muted")

    def _open_output(self):
        out = self.out_path.get().strip().strip('"')
        if out:
            core.open_in_explorer(Path(out))

    def _resolve_paths(self):
        """Validate the current selection and return (spec, in_path, out_path)."""
        spec = MODES[self.mode_var.get()]
        in_txt = self.in_path.get().strip().strip('"')
        out_txt = self.out_path.get().strip().strip('"')

        in_p: Path | None = None
        if spec.input_kind == IN_NONE:
            if not self.merge_list:
                raise ConversionError(t("err.merge_empty"))
        else:
            if not in_txt:
                raise ConversionError(t("err.input_required"))
            in_p = Path(in_txt)
            if not in_p.exists():
                raise ConversionError(t("err.input_missing", path=in_p))
            if spec.input_kind == IN_DOCX and in_p.suffix.lower() != ".docx":
                raise ConversionError(t("err.input_docx"))
            if spec.input_kind == IN_PDF and in_p.suffix.lower() != ".pdf":
                raise ConversionError(t("err.input_pdf"))
            if spec.input_kind == IN_FOLDER and not in_p.is_dir():
                raise ConversionError(t("err.input_folder"))

        if not out_txt:
            raise ConversionError(t("err.output_required"))
        out_p = Path(out_txt)

        kind = spec.output_kind
        if kind == OUT_IMAGE_OR_FOLDER:
            kind = OUT_FOLDER if (in_p and in_p.is_dir()) else OUT_IMAGE

        if kind == OUT_FOLDER:
            if out_p.suffix:
                raise ConversionError(t("err.output_folder_expected", name=out_p.name))
        elif kind == OUT_PDF:
            out_p = out_p.with_suffix(".pdf")
        elif kind == OUT_DOCX:
            out_p = out_p.with_suffix(".docx")
        elif kind == OUT_TXT:
            out_p = out_p.with_suffix(".txt")
        elif kind == OUT_IMAGE:
            if spec.key == "image_to_image":
                want = "." + self.batch_img_fmt_var.get().lower()
                if out_p.suffix.lower() != want:
                    out_p = out_p.with_suffix(want)
            elif out_p.suffix.lower() not in (".png", ".jpg", ".jpeg"):
                raise ConversionError(t("err.output_image_ext"))

        # numeric sanity for the options this mode actually uses
        if OPT_RENDER in spec.options:
            dpi = self._as_int(self.dpi_var.get(), t("opt.dpi"))
            if not (72 <= dpi <= 600):
                raise ConversionError(t("err.dpi_range"))
            if self.fmt_var.get().lower() not in ("png", "jpg"):
                raise ConversionError(t("err.format_png_jpg"))
        if OPT_IMAGE_OUT in spec.options:
            if self.batch_img_fmt_var.get().lower() not in OUT_IMAGE_FORMATS:
                raise ConversionError(t("err.choose_out_format",
                                        formats=", ".join(OUT_IMAGE_FORMATS)))
            self._as_int(self.resize_quality_var.get(), t("opt.quality"))
            if self.resize_max_var.get().strip():
                self._as_int(self.resize_max_var.get(), t("opt.max_size"))
        if OPT_COMPRESS in spec.options and self.compress_mode_var.get() == "rebuild":
            self._as_int(self.compress_dpi_var.get(), t("opt.rebuild_dpi"))

        return spec, in_p, out_p

    @staticmethod
    def _as_int(text: str, field: str) -> int:
        try:
            return int(str(text).strip())
        except ValueError as exc:
            raise ConversionError(t("err.whole_number", field=field, value=text)) from exc

    def _confirm_overwrite(self, out_p: Path, is_folder_output: bool) -> bool:
        if not self.confirm_overwrite_var.get():
            return True
        if is_folder_output:
            if out_p.exists() and out_p.is_dir():
                try:
                    has_any = any(out_p.iterdir())
                except Exception:
                    has_any = True
                if has_any:
                    return messagebox.askyesno(
                        t("dlg.folder_not_empty"),
                        t("dlg.folder_not_empty_body", path=out_p))
            return True
        if out_p.exists() and out_p.is_file():
            return messagebox.askyesno(t("dlg.overwrite_file"),
                                       t("dlg.overwrite_file_body", path=out_p))
        return True

    def _run(self):
        try:
            spec, in_p, out_p = self._resolve_paths()
        except ConversionError as e:
            self.status.set_state("error", t("status.check_settings"))
            self._log(str(e), kind="err")
            messagebox.showerror(t("dlg.cannot_run"), str(e))
            return

        folder_output = not out_p.suffix
        if not self._confirm_overwrite(out_p, folder_output):
            self.status.set_state("idle", t("status.cancelled"))
            return

        self.out_path.set(str(out_p))
        self.cancel_event.clear()
        self.progress["value"] = 0
        self.progress["maximum"] = 100
        self.status.set_state("working", t("status.working"))
        self.detail.configure(text=spec.title)
        self._set_working(True)
        self._persist_settings()
        self._log(t("log.starting", title=spec.title), kind="info")

        params = self._snapshot_params(spec, in_p, out_p)
        self.worker_thread = threading.Thread(target=self._worker, args=(params,), daemon=True)
        self.worker_thread.start()

    def _snapshot_params(self, spec, in_p, out_p) -> dict:
        """Copy every Tk variable we need up front.

        Tk variables must not be read from a background thread, so the worker
        only ever sees this plain dict.
        """
        def num(text, default: int) -> int:
            # Fields the current mode does not use are never validated, so they
            # may hold anything; fall back rather than crashing the run.
            try:
                return int(str(text).strip())
            except (TypeError, ValueError):
                return default

        return dict(
            spec=spec,
            in_p=in_p,
            out_p=out_p,
            merge_list=list(self.merge_list),
            dpi=num(self.dpi_var.get(), 300),
            fmt=self.fmt_var.get().lower(),
            jpg_quality=int(self.jpg_quality_var.get()),
            page_range=self.page_range_var.get().strip() or "all",
            recursive=bool(self.recursive_var.get()),
            sort_mode=self.sort_mode_var.get(),
            img_fmt=self.batch_img_fmt_var.get().lower(),
            resize_max=num(self.resize_max_var.get(), 0),
            resize_quality=num(self.resize_quality_var.get(), 80),
            rotate_deg=num(self.rotate_deg_var.get(), 90),
            split_mode=self.split_mode_var.get(),
            split_ranges=self.split_ranges_var.get(),
            compress_mode=self.compress_mode_var.get(),
            compress_dpi=num(self.compress_dpi_var.get(), 150),
        )

    def _worker(self, p: dict):
        def progress_cb(done, total):
            self.ui_queue.put(("progress", done, total))

        def log_cb(m):
            self.ui_queue.put(("log", m, "info"))

        cb = dict(progress_cb=progress_cb, cancel_event=self.cancel_event, log_cb=log_cb)
        spec, in_p, out_p = p["spec"], p["in_p"], p["out_p"]
        key = spec.key

        try:
            if key == "pdf_to_word":
                core.pdf_to_word(in_p, out_p, page_range=p["page_range"], **cb)

            elif key == "images_to_word":
                core.images_to_word(in_p, out_p, recursive=p["recursive"],
                                    sort_mode=p["sort_mode"], **cb)

            elif key == "word_to_pdf":
                core.word_to_pdf(in_p, out_p, log_cb=log_cb)
                progress_cb(1, 1)

            elif key == "word_to_images":
                core.word_to_images(in_p, out_p, p["dpi"], p["fmt"], p["jpg_quality"],
                                    page_range=p["page_range"], **cb)

            elif key == "pdf_to_images":
                core.pdf_to_images(in_p, out_p, p["dpi"], p["fmt"], p["jpg_quality"],
                                   page_range=p["page_range"], only_pages_with_images=False, **cb)

            elif key == "pdf_to_images_only_img_pages":
                core.pdf_to_images(in_p, out_p, p["dpi"], p["fmt"], p["jpg_quality"],
                                   page_range=p["page_range"], only_pages_with_images=True, **cb)

            elif key == "images_to_pdf":
                core.images_to_pdf(in_p, out_p, recursive=p["recursive"],
                                   sort_mode=p["sort_mode"], **cb)

            elif key == "pdf_to_long_image":
                out_fmt = "jpg" if out_p.suffix.lower() in (".jpg", ".jpeg") else "png"
                core.pdf_to_long_image(in_p, out_p, p["dpi"], out_fmt, p["jpg_quality"],
                                       page_range=p["page_range"], **cb)

            elif key == "pdf_to_text":
                core.pdf_to_text(in_p, out_p, page_range=p["page_range"], **cb)

            elif key == "image_to_image":
                core.image_to_image(in_p, out_p, p["img_fmt"], recursive=p["recursive"],
                                    max_size=p["resize_max"] or None,
                                    quality=p["resize_quality"], **cb)

            elif key == "merge_pdfs":
                core.merge_pdfs(p["merge_list"], out_p, **cb)

            elif key == "split_pdf":
                core.split_pdf(in_p, out_p, mode=p["split_mode"], ranges=p["split_ranges"], **cb)

            elif key == "rotate_pdf":
                core.rotate_pdf(in_p, out_p, p["rotate_deg"], page_range=p["page_range"], **cb)

            elif key == "compress_pdf":
                if p["compress_mode"] == "clean":
                    core.compress_pdf_clean(in_p, out_p, log_cb=log_cb)
                    progress_cb(1, 1)
                else:
                    core.compress_pdf_rebuild(in_p, out_p, p["compress_dpi"], **cb)

            elif key == "batch_image_convert":
                core.batch_image_convert(in_p, out_p, p["img_fmt"], recursive=p["recursive"], **cb)

            elif key == "batch_image_resize":
                core.batch_image_resize(in_p, out_p, p["img_fmt"], p["resize_max"] or 1600,
                                        p["resize_quality"], recursive=p["recursive"], **cb)

            elif key == "images_to_pdf_per_subfolder":
                core.images_to_pdf_per_subfolder(in_p, out_p, recursive=p["recursive"],
                                                 sort_mode=p["sort_mode"], **cb)

            elif key == "batch_word_pdf":
                core.batch_word_convert(in_p, out_p, "pdf", p["dpi"], p["fmt"],
                                        p["jpg_quality"], **cb)

            elif key == "batch_word_images":
                core.batch_word_convert(in_p, out_p, "images", p["dpi"], p["fmt"],
                                        p["jpg_quality"], **cb)

            else:
                raise ConversionError(t("err.unknown_mode", key=key))

            self.ui_queue.put(("done", str(out_p)))

        except Cancelled:
            self.ui_queue.put(("cancelled", ""))
        except ConversionError as e:
            self.ui_queue.put(("error", str(e)))
        except Exception as e:
            # Unexpected failures keep their traceback in the log, so a bad PDF
            # is diagnosable instead of just "an error occurred".
            self.ui_queue.put(("log", traceback.format_exc().rstrip(), "err"))
            self.ui_queue.put(("error", f"{type(e).__name__}: {e}"))

    def _poll_queue(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                tag = msg[0]

                if tag == "log":
                    self._log(msg[1], kind=msg[2] if len(msg) > 2 else "info")

                elif tag == "progress":
                    done, total = msg[1], max(1, msg[2])
                    self.progress["value"] = int((done / total) * 100)
                    self.detail.configure(text=t("status.progress", done=done, total=total))

                elif tag == "done":
                    self._set_working(False)
                    self.progress["value"] = 100
                    self.status.set_state("done", t("status.finished"))
                    self.detail.configure(text=msg[1])
                    self.btn_open.config(state="normal")
                    self._log(t("log.finished", path=msg[1]), kind="ok")
                    if self.open_output_after_run_var.get():
                        try:
                            self._open_output()
                        except Exception:
                            pass

                elif tag == "cancelled":
                    self._set_working(False)
                    self.progress["value"] = 0
                    self.status.set_state("idle", t("status.cancelled"))
                    self.detail.configure(text="")
                    self._log(t("log.cancelled"), kind="muted")

                elif tag == "error":
                    self._set_working(False)
                    self.status.set_state("error", t("status.failed"))
                    self.detail.configure(text=t("status.see_log"))
                    self._log(msg[1], kind="err")
                    messagebox.showerror(t("dlg.failed"), msg[1])

        except queue.Empty:
            pass
        self.after(100, self._poll_queue)


def main():
    App().mainloop()
