"""Dark theme + custom widgets.

Tk's stock widgets look like Windows 95, so this module does two things:
configure the ttk 'clam' theme (the only built-in theme that honours colour
options for most elements), and provide a handful of plain-``tk`` widgets for
the pieces ttk simply cannot style — selectable cards, sidebar nav, scrolling
panes.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class C:
    """Colour palette. One place to retune the whole app."""

    BG_DEEP = "#0C0E14"      # window background, behind everything
    BG = "#12151E"           # page background
    SURFACE = "#181C28"      # cards
    SURFACE_2 = "#212636"    # raised / hovered cards, inputs
    SURFACE_3 = "#2A3145"    # pressed
    BORDER = "#2C3346"
    BORDER_SOFT = "#222839"

    TEXT = "#E8ECF6"
    TEXT_DIM = "#A8B2C8"
    TEXT_MUTED = "#6E7994"

    ACCENT = "#6C8CFF"
    ACCENT_HOVER = "#8AA3FF"
    ACCENT_DEEP = "#3F5BD9"
    ACCENT_SOFT = "#1D2440"

    SUCCESS = "#3DD68C"
    DANGER = "#FF6B6B"
    WARN = "#FFC46B"


FONT = "Segoe UI"
F_H1 = (FONT, 17, "bold")
F_H2 = (FONT, 12, "bold")
F_BODY = (FONT, 10)
F_SMALL = (FONT, 9)
F_TINY = (FONT, 8)
F_ICON = ("Segoe UI Emoji", 19)
F_ICON_SM = ("Segoe UI Emoji", 12)
F_MONO = ("Consolas", 9)  # always present on Windows


def apply_theme(root: tk.Misc) -> ttk.Style:
    """Point every ttk widget at the palette above."""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")  # the most colour-friendly built-in theme
    except tk.TclError:
        pass

    root.configure(bg=C.BG_DEEP)

    # Combobox dropdowns are separate toplevels and ignore ttk styling, so they
    # have to be themed through the old Tk option database.
    root.option_add("*TCombobox*Listbox.background", C.SURFACE_2)
    root.option_add("*TCombobox*Listbox.foreground", C.TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", C.ACCENT)
    root.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")
    root.option_add("*TCombobox*Listbox.font", F_BODY)

    style.configure(".", background=C.BG, foreground=C.TEXT, font=F_BODY,
                    borderwidth=0, focuscolor=C.ACCENT)

    # ---- frames & labels
    style.configure("TFrame", background=C.BG)
    style.configure("Deep.TFrame", background=C.BG_DEEP)
    style.configure("Card.TFrame", background=C.SURFACE)
    style.configure("Surface.TFrame", background=C.SURFACE_2)

    style.configure("TLabel", background=C.BG, foreground=C.TEXT, font=F_BODY)
    style.configure("H1.TLabel", font=F_H1, foreground=C.TEXT, background=C.BG_DEEP)
    style.configure("H2.TLabel", font=F_H2, foreground=C.TEXT, background=C.BG)
    style.configure("Muted.TLabel", foreground=C.TEXT_MUTED, background=C.BG, font=F_SMALL)
    style.configure("MutedDeep.TLabel", foreground=C.TEXT_MUTED, background=C.BG_DEEP, font=F_SMALL)
    style.configure("CardTitle.TLabel", font=F_H2, foreground=C.TEXT, background=C.SURFACE)
    style.configure("CardBody.TLabel", foreground=C.TEXT_DIM, background=C.SURFACE, font=F_BODY)
    style.configure("CardMuted.TLabel", foreground=C.TEXT_MUTED, background=C.SURFACE, font=F_SMALL)
    style.configure("Accent.TLabel", foreground=C.ACCENT, background=C.BG, font=F_SMALL)

    # ---- buttons
    style.configure("TButton", background=C.SURFACE_2, foreground=C.TEXT,
                    bordercolor=C.BORDER, lightcolor=C.SURFACE_2, darkcolor=C.SURFACE_2,
                    focusthickness=0, borderwidth=1, padding=(14, 7), font=F_BODY)
    style.map("TButton",
              background=[("disabled", C.SURFACE), ("pressed", C.SURFACE_3), ("active", C.SURFACE_3)],
              foreground=[("disabled", C.TEXT_MUTED)],
              bordercolor=[("active", C.ACCENT_DEEP)],
              lightcolor=[("pressed", C.SURFACE_3), ("active", C.SURFACE_3)],
              darkcolor=[("pressed", C.SURFACE_3), ("active", C.SURFACE_3)])

    style.configure("Accent.TButton", background=C.ACCENT, foreground="#0A0E1B",
                    bordercolor=C.ACCENT, lightcolor=C.ACCENT, darkcolor=C.ACCENT,
                    padding=(22, 9), font=(FONT, 10, "bold"))
    style.map("Accent.TButton",
              background=[("disabled", C.SURFACE_2), ("pressed", C.ACCENT_DEEP), ("active", C.ACCENT_HOVER)],
              foreground=[("disabled", C.TEXT_MUTED)],
              bordercolor=[("disabled", C.BORDER), ("active", C.ACCENT_HOVER)],
              lightcolor=[("pressed", C.ACCENT_DEEP), ("active", C.ACCENT_HOVER)],
              darkcolor=[("pressed", C.ACCENT_DEEP), ("active", C.ACCENT_HOVER)])

    style.configure("Card.TButton", background=C.SURFACE, foreground=C.TEXT_DIM,
                    bordercolor=C.BORDER, lightcolor=C.SURFACE, darkcolor=C.SURFACE,
                    padding=(12, 6), font=F_SMALL)
    style.map("Card.TButton",
              background=[("pressed", C.SURFACE_3), ("active", C.SURFACE_2)],
              lightcolor=[("pressed", C.SURFACE_3), ("active", C.SURFACE_2)],
              darkcolor=[("pressed", C.SURFACE_3), ("active", C.SURFACE_2)],
              foreground=[("active", C.TEXT), ("disabled", C.TEXT_MUTED)])

    # ---- entries & combos
    for name in ("TEntry", "TCombobox"):
        style.configure(name,
                        fieldbackground=C.SURFACE_2, background=C.SURFACE_2,
                        foreground=C.TEXT, insertcolor=C.ACCENT,
                        bordercolor=C.BORDER, lightcolor=C.BORDER, darkcolor=C.BORDER,
                        arrowcolor=C.TEXT_DIM, borderwidth=1, padding=(8, 6))
        style.map(name,
                  fieldbackground=[("readonly", C.SURFACE_2), ("disabled", C.SURFACE)],
                  foreground=[("disabled", C.TEXT_MUTED)],
                  bordercolor=[("focus", C.ACCENT), ("hover", C.BORDER)],
                  lightcolor=[("focus", C.ACCENT)],
                  darkcolor=[("focus", C.ACCENT)],
                  arrowcolor=[("active", C.ACCENT)],
                  selectbackground=[("!disabled", C.ACCENT_DEEP)])

    # ---- toggles
    style.configure("TCheckbutton", background=C.SURFACE, foreground=C.TEXT_DIM,
                    font=F_BODY, focusthickness=0,
                    indicatorbackground=C.SURFACE_2, indicatorforeground=C.ACCENT,
                    indicatorcolor=C.SURFACE_2)
    style.map("TCheckbutton",
              background=[("active", C.SURFACE)],
              foreground=[("active", C.TEXT), ("disabled", C.TEXT_MUTED)],
              indicatorcolor=[("selected", C.ACCENT), ("pressed", C.SURFACE_3)],
              indicatorbackground=[("selected", C.ACCENT), ("active", C.SURFACE_3)])

    style.configure("Bg.TCheckbutton", background=C.BG)
    style.map("Bg.TCheckbutton", background=[("active", C.BG)])

    # ---- progress & scale
    style.configure("Accent.Horizontal.TProgressbar",
                    troughcolor=C.SURFACE, background=C.ACCENT,
                    bordercolor=C.SURFACE, lightcolor=C.ACCENT, darkcolor=C.ACCENT,
                    thickness=6, borderwidth=0)

    style.configure("Horizontal.TScale", background=C.SURFACE, troughcolor=C.SURFACE_2,
                    bordercolor=C.BORDER, lightcolor=C.ACCENT, darkcolor=C.ACCENT_DEEP)
    style.map("Horizontal.TScale", background=[("active", C.SURFACE)])

    # ---- scrollbars
    style.configure("Vertical.TScrollbar", background=C.SURFACE_2, troughcolor=C.BG,
                    bordercolor=C.BG, arrowcolor=C.TEXT_MUTED,
                    lightcolor=C.SURFACE_2, darkcolor=C.SURFACE_2, borderwidth=0)
    style.map("Vertical.TScrollbar",
              background=[("active", C.SURFACE_3), ("pressed", C.ACCENT_DEEP)])

    style.configure("TSeparator", background=C.BORDER_SOFT)

    return style


# --------------------------------------------------------------- widgets ----

class Card(tk.Frame):
    """A titled panel — the basic content container."""

    def __init__(self, parent, title: str = "", subtitle: str = "", **kw):
        super().__init__(parent, bg=C.SURFACE, highlightthickness=1,
                         highlightbackground=C.BORDER_SOFT, highlightcolor=C.BORDER_SOFT,
                         bd=0, **kw)
        self.body = self  # default; replaced below when a header exists

        if title:
            head = tk.Frame(self, bg=C.SURFACE)
            head.pack(fill="x", padx=18, pady=(15, 0))
            tk.Label(head, text=title, bg=C.SURFACE, fg=C.TEXT, font=F_H2,
                     anchor="w").pack(side="left")
            if subtitle:
                tk.Label(head, text=subtitle, bg=C.SURFACE, fg=C.TEXT_MUTED,
                         font=F_SMALL, anchor="w").pack(side="left", padx=(10, 0), pady=(3, 0))

            self.body = tk.Frame(self, bg=C.SURFACE)
            self.body.pack(fill="both", expand=True, padx=18, pady=(10, 16))


class ModeCard(tk.Frame):
    """A big clickable tile representing one conversion mode."""

    def __init__(self, parent, spec, command):
        super().__init__(parent, bg=C.SURFACE, highlightthickness=1,
                         highlightbackground=C.BORDER_SOFT, highlightcolor=C.BORDER_SOFT,
                         cursor="hand2")
        self.spec = spec
        self.command = command
        self._selected = False
        self._hover = False

        inner = tk.Frame(self, bg=C.SURFACE)
        inner.pack(fill="both", expand=True, padx=13, pady=11)

        self.icon = tk.Label(inner, text=spec.icon, bg=C.SURFACE, fg=C.TEXT, font=F_ICON)
        self.icon.pack(anchor="w")

        self.title = tk.Label(inner, text=spec.title, bg=C.SURFACE, fg=C.TEXT,
                              font=(FONT, 10, "bold"), anchor="w", justify="left")
        self.title.pack(anchor="w", pady=(6, 0))

        self.sub = tk.Label(inner, text=spec.subtitle, bg=C.SURFACE, fg=C.TEXT_MUTED,
                            font=F_TINY, anchor="w", justify="left", wraplength=150)
        self.sub.pack(anchor="w", pady=(2, 0))

        self._parts = [self, inner, self.icon, self.title, self.sub]
        for w in self._parts:
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

    def _on_click(self, _evt=None):
        self.command(self.spec.key)

    def _on_enter(self, _evt=None):
        self._hover = True
        self._repaint()

    def _on_leave(self, _evt=None):
        self._hover = False
        self._repaint()

    def set_selected(self, value: bool):
        self._selected = value
        self._repaint()

    def _repaint(self):
        if self._selected:
            bg, border = C.ACCENT_SOFT, C.ACCENT
            title_fg, sub_fg = C.TEXT, C.TEXT_DIM
        elif self._hover:
            bg, border = C.SURFACE_2, C.BORDER
            title_fg, sub_fg = C.TEXT, C.TEXT_MUTED
        else:
            bg, border = C.SURFACE, C.BORDER_SOFT
            title_fg, sub_fg = C.TEXT_DIM, C.TEXT_MUTED

        self.configure(highlightbackground=border, highlightcolor=border)
        for w in self._parts:
            w.configure(bg=bg)
        self.title.configure(fg=title_fg)
        self.sub.configure(fg=sub_fg)
        self.icon.configure(fg=C.ACCENT if self._selected else C.TEXT_DIM)


class NavButton(tk.Frame):
    """Sidebar entry with an accent bar when active."""

    def __init__(self, parent, icon: str, text: str, command):
        super().__init__(parent, bg=C.BG_DEEP, cursor="hand2")
        self.command = command
        self._active = False
        self._hover = False

        self.bar = tk.Frame(self, bg=C.BG_DEEP, width=3)
        self.bar.pack(side="left", fill="y")

        self.row = tk.Frame(self, bg=C.BG_DEEP)
        self.row.pack(side="left", fill="both", expand=True, padx=(9, 10), pady=8)

        self.icon = tk.Label(self.row, text=icon, bg=C.BG_DEEP, fg=C.TEXT_MUTED, font=F_ICON_SM)
        self.icon.pack(side="left")
        self.label = tk.Label(self.row, text=text, bg=C.BG_DEEP, fg=C.TEXT_DIM,
                              font=F_BODY, anchor="w")
        self.label.pack(side="left", padx=(9, 0))

        self._parts = [self, self.row, self.icon, self.label]
        for w in self._parts:
            w.bind("<Button-1>", lambda _e: self.command())
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

    def _on_enter(self, _evt=None):
        self._hover = True
        self._repaint()

    def _on_leave(self, _evt=None):
        self._hover = False
        self._repaint()

    def set_active(self, value: bool):
        self._active = value
        self._repaint()

    def _repaint(self):
        if self._active:
            bg, fg, icon_fg = C.SURFACE, C.TEXT, C.ACCENT
        elif self._hover:
            bg, fg, icon_fg = C.SURFACE_2, C.TEXT, C.TEXT_DIM
        else:
            bg, fg, icon_fg = C.BG_DEEP, C.TEXT_DIM, C.TEXT_MUTED

        for w in self._parts:
            w.configure(bg=bg)
        self.bar.configure(bg=C.ACCENT if self._active else bg)
        self.label.configure(fg=fg)
        self.icon.configure(fg=icon_fg)


class StatusPill(tk.Label):
    """Small rounded-ish status chip: idle / working / done / error."""

    def __init__(self, parent, **kw):
        super().__init__(parent, text="Ready", bg=C.SURFACE, fg=C.TEXT_MUTED,
                         font=F_SMALL, padx=12, pady=5, **kw)

    def set_state(self, kind: str, text: str):
        colours = {
            "idle": (C.SURFACE, C.TEXT_MUTED),
            "working": (C.ACCENT_SOFT, C.ACCENT_HOVER),
            "done": ("#12281F", C.SUCCESS),
            "error": ("#2A1620", C.DANGER),
        }
        bg, fg = colours.get(kind, colours["idle"])
        self.configure(bg=bg, fg=fg, text=text)


class ScrollFrame(tk.Frame):
    """Vertically scrollable container — pack content into ``.body``."""

    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C.BG, **kw)

        self.canvas = tk.Canvas(self, bg=C.BG, highlightthickness=0, bd=0)
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview,
                                    style="Vertical.TScrollbar")
        self.canvas.configure(yscrollcommand=self.scroll.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll.pack(side="right", fill="y")

        self.body = tk.Frame(self.canvas, bg=C.BG)
        self._window = self.canvas.create_window((0, 0), window=self.body, anchor="nw")

        self.body.bind("<Configure>", self._on_body_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        # Bind the wheel only while the pointer is over this pane, otherwise
        # every ScrollFrame in the app would react to every wheel event.
        self.canvas.bind("<Enter>", lambda _e: self._bind_wheel(True))
        self.canvas.bind("<Leave>", lambda _e: self._bind_wheel(False))

    def _on_body_configure(self, _evt=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, evt):
        self.canvas.itemconfigure(self._window, width=evt.width)

    def _bind_wheel(self, active: bool):
        if active:
            self.canvas.bind_all("<MouseWheel>", self._on_wheel)
        else:
            self.canvas.unbind_all("<MouseWheel>")

    def _on_wheel(self, evt):
        first, last = self.canvas.yview()
        if first <= 0.0 and last >= 1.0:
            return  # nothing to scroll
        self.canvas.yview_scroll(int(-evt.delta / 120), "units")
