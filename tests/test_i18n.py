"""Translation-catalogue tests.

The point of these is to make an incomplete translation a test failure rather
than a `some.missing.key` string appearing in the UI at runtime.
"""

from __future__ import annotations

import re

import pytest

from rilleras import i18n
from rilleras.modes import GROUPS, MODES


@pytest.fixture(autouse=True)
def restore_language():
    original = i18n.get_language()
    yield
    i18n.set_language(original)


def test_every_language_defines_every_english_key():
    english = set(i18n.EN)
    for code, table in i18n.TRANSLATIONS.items():
        missing = english - set(table)
        extra = set(table) - english
        assert not missing, f"{code} is missing: {sorted(missing)}"
        assert not extra, f"{code} has keys English does not: {sorted(extra)}"


def test_no_translation_is_left_as_english_placeholder():
    """Catch keys that were copied across but never actually translated."""
    # A handful legitimately match: brand names, format names, units.
    allowed_identical = {
        "about.version", "opt.dpi", "opt.format", "filetype.pdf", "filetype.word",
        "mode.pdf_to_word.title", "mode.word_to_pdf.title",
        "nav.pdf", "group.pdf.title",
    }
    identical = [
        key for key, text in i18n.TR.items()
        if text == i18n.EN[key] and key not in allowed_identical
    ]
    assert not identical, f"untranslated Turkish strings: {identical}"


def test_every_mode_has_title_and_subtitle_in_every_language():
    for code in i18n.LANGUAGES:
        i18n.set_language(code)
        for key, spec in MODES.items():
            assert spec.title and not spec.title.startswith("mode."), (code, key)
            assert spec.subtitle and not spec.subtitle.startswith("mode."), (code, key)
            assert spec.input_label and not spec.input_label.startswith("io."), (code, key)
            assert spec.output_label and not spec.output_label.startswith("io."), (code, key)


def test_every_group_has_a_heading_in_every_language():
    from rilleras.modes import group_heading

    for code in i18n.LANGUAGES:
        i18n.set_language(code)
        for group in GROUPS:
            title, subtitle = group_heading(group)
            assert not title.startswith("group."), (code, group)
            assert not subtitle.startswith("group."), (code, group)


def test_placeholders_match_between_languages():
    """A {placeholder} dropped in translation would raise or print wrongly."""
    pattern = re.compile(r"{(\w+)}")
    for code, table in i18n.TRANSLATIONS.items():
        for key, english in i18n.EN.items():
            assert pattern.findall(english).sort() == pattern.findall(table[key]).sort(), (
                f"{code}:{key} placeholder mismatch")


def test_switching_language_changes_output():
    i18n.set_language("en")
    english = i18n.t("btn.run")
    i18n.set_language("tr")
    turkish = i18n.t("btn.run")
    assert english != turkish
    assert turkish == "Dönüştürmeyi başlat"


def test_unknown_language_falls_back_to_english():
    i18n.set_language("klingon")
    assert i18n.get_language() == "en"
    assert i18n.t("status.ready") == "Ready"


def test_unknown_key_returns_the_key():
    assert i18n.t("nope.not.here") == "nope.not.here"


def test_formatting_is_applied():
    i18n.set_language("en")
    assert i18n.t("log.starting", title="PDF → Word") == "Starting: PDF → Word"


def test_bad_placeholder_does_not_raise():
    i18n.set_language("en")
    # missing kwarg: returns the raw template instead of blowing up the UI
    assert "{path}" in i18n.t("msg.saved")


def test_engine_errors_are_translated():
    from rilleras import core

    i18n.set_language("tr")
    try:
        with pytest.raises(core.ConversionError) as exc:
            core.parse_page_range("abc", 5)
        assert "okunamadı" in str(exc.value)
    finally:
        i18n.set_language("en")
