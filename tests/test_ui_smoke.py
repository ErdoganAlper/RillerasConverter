"""Smoke test: build the real window and walk every screen and mode.

Catches the class of mistake unit tests miss — a bad grid option, a missing
attribute, an option row that fails to pack.

Two deliberate choices here:

* One shared window for the whole module. Creating and tearing down Tk roots
  repeatedly in a single process intermittently fails to re-initialise Tcl,
  which showed up as a random "no display available" skip. The real app only
  ever creates one root anyway.
* Visibility is asserted through ``winfo_manager()`` rather than
  ``winfo_ismapped()``. A withdrawn window reports nothing as mapped, so
  ``ismapped`` would pass or fail for reasons unrelated to the code under test.
"""

from __future__ import annotations

import pytest

tk = pytest.importorskip("tkinter")


def shown(widget) -> bool:
    """True when a geometry manager is currently displaying this widget."""
    return bool(widget.winfo_manager())


@pytest.fixture(scope="module")
def app():
    from rilleras import app as app_module

    # Never touch the user's real settings.json from a test run.
    original_save = app_module.save_settings
    app_module.save_settings = lambda data: None

    try:
        instance = app_module.App()
    except tk.TclError as exc:  # pragma: no cover - headless CI
        app_module.save_settings = original_save
        pytest.skip(f"no display available: {exc}")

    instance.withdraw()
    try:
        yield instance
    finally:
        instance.destroy()
        app_module.save_settings = original_save


def test_window_builds(app):
    app.update_idletasks()
    assert app.title().startswith("Rilleras Converter")


def test_every_view_opens(app):
    from rilleras.modes import GROUP_BATCH, GROUP_IMAGE, GROUP_MAIN, GROUP_PDF

    for view in (GROUP_MAIN, GROUP_PDF, GROUP_IMAGE, GROUP_BATCH, "settings", "log"):
        app._select_view(view)
        app.update_idletasks()
        assert app._current_view == view


def test_every_mode_selectable(app):
    from rilleras.modes import MODES, group_of

    for key, spec in MODES.items():
        app._select_view(group_of(key))
        app._on_mode_card_clicked(key)
        app.update_idletasks()

        assert app.mode_var.get() == key
        # the tile for the active mode must exist and be marked selected
        assert key in app._mode_cards
        assert app._mode_cards[key]._selected
        # the hint line always describes both ends of the conversion
        assert spec.input_label in app.mode_hint.cget("text")
        assert spec.output_label in app.mode_hint.cget("text")


def test_group_heading_shows_title_and_subtitle(app):
    """The panel heading must track the selected group, subtitle included."""
    from rilleras.modes import GROUP_PDF, GROUP_TITLES

    app._select_view(GROUP_PDF)
    app.update_idletasks()

    header = app.mode_panel.winfo_children()[0]
    texts = [w.cget("text") for w in header.winfo_children() if isinstance(w, tk.Label)]
    title, subtitle = GROUP_TITLES[GROUP_PDF]

    assert title in texts
    assert subtitle in texts


def test_switching_group_moves_to_a_mode_in_that_group(app):
    from rilleras.modes import GROUP_IMAGE, group_of

    app._select_view("main")
    app._on_mode_card_clicked("pdf_to_word")

    app._select_view(GROUP_IMAGE)
    assert group_of(app.mode_var.get()) == GROUP_IMAGE


def test_only_relevant_options_are_shown(app):
    from rilleras.modes import MODES, OPT_PAGES, OPT_RENDER, group_of

    app._select_view(group_of("pdf_to_word"))
    app._on_mode_card_clicked("pdf_to_word")
    app.update_idletasks()

    # PDF -> Word takes a page range but has no DPI/format controls
    assert set(MODES["pdf_to_word"].options) == {OPT_PAGES}
    assert shown(app._option_rows[OPT_PAGES])
    assert not shown(app._option_rows[OPT_RENDER])

    app._on_mode_card_clicked("pdf_to_images")
    app.update_idletasks()
    assert shown(app._option_rows[OPT_RENDER])


def test_modes_without_options_hide_the_options_card(app):
    app._select_view("main")
    app._on_mode_card_clicked("word_to_pdf")  # declares no options
    app.update_idletasks()
    assert not shown(app.options_card)

    app._on_mode_card_clicked("pdf_to_images")
    app.update_idletasks()
    assert shown(app.options_card)


def test_merge_mode_hides_input_row_and_shows_list(app):
    app._select_view("pdf")
    app._on_mode_card_clicked("merge_pdfs")
    app.update_idletasks()

    assert str(app.entry_in.cget("state")) == "disabled"
    assert shown(app.merge_card)

    app._on_mode_card_clicked("split_pdf")
    app.update_idletasks()
    assert str(app.entry_in.cget("state")) == "normal"
    assert not shown(app.merge_card)


def test_word_badge_visibility_follows_mode(app):
    app._select_view("main")

    app._on_mode_card_clicked("word_to_pdf")
    app.update_idletasks()
    assert shown(app.word_badge)

    app._on_mode_card_clicked("pdf_to_word")
    app.update_idletasks()
    assert not shown(app.word_badge)


def test_merge_list_reordering(app, tmp_path):
    from pathlib import Path

    app._select_view("pdf")
    app._on_mode_card_clicked("merge_pdfs")
    app.merge_list = [Path("a.pdf"), Path("b.pdf"), Path("c.pdf")]
    app._merge_refresh()

    app.merge_box.selection_set(2)
    app._merge_move(-1)
    assert [p.name for p in app.merge_list] == ["a.pdf", "c.pdf", "b.pdf"]

    app.merge_box.selection_clear(0, tk.END)
    app.merge_box.selection_set(0)
    app._merge_remove()
    assert [p.name for p in app.merge_list] == ["c.pdf", "b.pdf"]

    app._merge_clear()
    assert app.merge_list == []


def test_run_without_paths_reports_error(app, monkeypatch):
    shown_dialog = {}
    monkeypatch.setattr("rilleras.app.messagebox.showerror",
                        lambda title, msg: shown_dialog.update(title=title, msg=msg))

    app._select_view("main")
    app._on_mode_card_clicked("pdf_to_word")
    app.in_path.set("")
    app.out_path.set("")
    app._run()

    assert "input" in shown_dialog.get("msg", "").lower()
    assert app.worker_thread is None  # never started a job


def test_missing_input_file_is_reported(app, monkeypatch, tmp_path):
    shown_dialog = {}
    monkeypatch.setattr("rilleras.app.messagebox.showerror",
                        lambda title, msg: shown_dialog.update(msg=msg))

    app._select_view("main")
    app._on_mode_card_clicked("pdf_to_word")
    app.in_path.set(str(tmp_path / "nope.pdf"))
    app.out_path.set(str(tmp_path / "out.docx"))
    app._run()

    assert "does not exist" in shown_dialog.get("msg", "")


def test_output_extension_is_corrected(app, tmp_path):
    src = tmp_path / "in.pdf"
    src.write_bytes(b"%PDF-1.4\n")  # only existence is checked at this stage

    app._select_view("main")
    app._on_mode_card_clicked("pdf_to_word")
    app.in_path.set(str(src))
    app.out_path.set(str(tmp_path / "result.txt"))

    _spec, _in_p, out_p = app._resolve_paths()
    assert out_p.suffix == ".docx"


def test_folder_output_rejects_a_filename(app, tmp_path):
    from rilleras.core import ConversionError

    src = tmp_path / "in.pdf"
    src.write_bytes(b"%PDF-1.4\n")

    app._select_view("main")
    app._on_mode_card_clicked("pdf_to_images")
    app.in_path.set(str(src))
    app.out_path.set(str(tmp_path / "oops.png"))

    with pytest.raises(ConversionError):
        app._resolve_paths()


def test_wrong_input_type_is_rejected(app, tmp_path):
    from rilleras.core import ConversionError

    src = tmp_path / "in.txt"
    src.write_text("not a pdf")

    app._select_view("main")
    app._on_mode_card_clicked("pdf_to_word")
    app.in_path.set(str(src))
    app.out_path.set(str(tmp_path / "out.docx"))

    with pytest.raises(ConversionError):
        app._resolve_paths()


def test_preset_updates_render_settings(app):
    app._apply_preset("Fast Draft (100dpi JPG q65)")
    assert app.dpi_var.get() == "100"
    assert app.fmt_var.get() == "jpg"
    assert app.jpg_quality_var.get() == 65
    assert app.quality_value.cget("text") == "65"


def test_unused_option_fields_do_not_break_a_run(app, tmp_path):
    """Garbage in a field the current mode ignores must not abort the job."""
    src = tmp_path / "in.pdf"
    src.write_bytes(b"%PDF-1.4\n")

    app._select_view("main")
    app._on_mode_card_clicked("pdf_to_word")
    app.in_path.set(str(src))
    app.out_path.set(str(tmp_path / "out.docx"))
    app.dpi_var.set("not-a-number")  # pdf_to_word never reads DPI

    spec, in_p, out_p = app._resolve_paths()
    params = app._snapshot_params(spec, in_p, out_p)
    assert params["dpi"] == 300  # fell back instead of raising
