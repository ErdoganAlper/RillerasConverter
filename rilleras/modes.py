"""Declarative description of every conversion the app offers.

The original build repeated the same mode list in four places (labels, input
browser, output browser, validation), which is how the labels drifted out of
sync with reality. Everything now derives from this one table.

Display text is *not* stored here — titles, subtitles and the input/output
descriptions resolve through `i18n` on access, so switching language changes
them without rebuilding this table.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import i18n

# What kind of thing the user picks as input / output.
IN_DOCX = "docx"
IN_PDF = "pdf"
IN_FOLDER = "folder"
IN_IMAGE_OR_FOLDER = "image_or_folder"
IN_NONE = "none"

OUT_FOLDER = "folder"
OUT_PDF = "pdf"
OUT_DOCX = "docx"
OUT_TXT = "txt"
OUT_IMAGE = "image"
OUT_IMAGE_OR_FOLDER = "image_or_folder"

# Option groups a mode wants shown. Anything not listed stays hidden, so the
# panel only ever shows controls that actually affect the current job.
OPT_RENDER = "render"        # DPI + png/jpg + JPG quality
OPT_PAGES = "pages"          # page range
OPT_RECURSIVE = "recursive"  # scan subfolders
OPT_SORT = "sort"            # image ordering for image -> pdf/docx
OPT_IMAGE_OUT = "image_out"  # output format / max size / quality
OPT_ROTATE = "rotate"
OPT_SPLIT = "split"
OPT_COMPRESS = "compress"
OPT_MERGE = "merge"

GROUP_MAIN = "main"
GROUP_PDF = "pdf"
GROUP_IMAGE = "image"
GROUP_BATCH = "batch"

GROUPS = (GROUP_MAIN, GROUP_PDF, GROUP_IMAGE, GROUP_BATCH)


@dataclass(frozen=True)
class ModeSpec:
    key: str
    icon: str
    group: str
    input_kind: str
    output_kind: str
    options: tuple[str, ...] = field(default_factory=tuple)
    requires_word: bool = False

    @property
    def title(self) -> str:
        return i18n.t(f"mode.{self.key}.title")

    @property
    def subtitle(self) -> str:
        return i18n.t(f"mode.{self.key}.sub")

    @property
    def input_label(self) -> str:
        return i18n.t(f"io.in.{self.input_kind}")

    @property
    def output_label(self) -> str:
        return i18n.t(f"io.out.{self.output_kind}")


def _m(*args, **kwargs) -> ModeSpec:
    return ModeSpec(*args, **kwargs)


MODES: dict[str, ModeSpec] = {m.key: m for m in [
    # ---------------------------------------------------------- convert --
    _m("pdf_to_word", "📝", GROUP_MAIN, IN_PDF, OUT_DOCX, (OPT_PAGES,)),
    _m("word_to_pdf", "📄", GROUP_MAIN, IN_DOCX, OUT_PDF, (), requires_word=True),
    _m("pdf_to_images", "🖼️", GROUP_MAIN, IN_PDF, OUT_FOLDER, (OPT_RENDER, OPT_PAGES)),
    _m("images_to_pdf", "📚", GROUP_MAIN, IN_IMAGE_OR_FOLDER, OUT_PDF,
       (OPT_RECURSIVE, OPT_SORT)),
    _m("images_to_word", "🗎", GROUP_MAIN, IN_IMAGE_OR_FOLDER, OUT_DOCX,
       (OPT_RECURSIVE, OPT_SORT)),
    _m("word_to_images", "🧾", GROUP_MAIN, IN_DOCX, OUT_FOLDER,
       (OPT_RENDER, OPT_PAGES), requires_word=True),
    _m("pdf_to_text", "🔤", GROUP_MAIN, IN_PDF, OUT_TXT, (OPT_PAGES,)),
    _m("pdf_to_long_image", "🧵", GROUP_MAIN, IN_PDF, OUT_IMAGE, (OPT_RENDER, OPT_PAGES)),
    _m("pdf_to_images_only_img_pages", "🔎", GROUP_MAIN, IN_PDF, OUT_FOLDER,
       (OPT_RENDER, OPT_PAGES)),
    _m("image_to_image", "🔄", GROUP_MAIN, IN_IMAGE_OR_FOLDER, OUT_IMAGE_OR_FOLDER,
       (OPT_IMAGE_OUT, OPT_RECURSIVE)),

    # -------------------------------------------------------- pdf tools --
    _m("merge_pdfs", "🔗", GROUP_PDF, IN_NONE, OUT_PDF, (OPT_MERGE,)),
    _m("split_pdf", "✂️", GROUP_PDF, IN_PDF, OUT_FOLDER, (OPT_SPLIT,)),
    _m("rotate_pdf", "🔃", GROUP_PDF, IN_PDF, OUT_PDF, (OPT_ROTATE, OPT_PAGES)),
    _m("compress_pdf", "🗜️", GROUP_PDF, IN_PDF, OUT_PDF, (OPT_COMPRESS,)),

    # ------------------------------------------------------ image tools --
    _m("batch_image_convert", "🎛️", GROUP_IMAGE, IN_FOLDER, OUT_FOLDER,
       (OPT_IMAGE_OUT, OPT_RECURSIVE)),
    _m("batch_image_resize", "📐", GROUP_IMAGE, IN_FOLDER, OUT_FOLDER,
       (OPT_IMAGE_OUT, OPT_RECURSIVE)),
    _m("images_to_pdf_per_subfolder", "🗂️", GROUP_IMAGE, IN_FOLDER, OUT_FOLDER,
       (OPT_RECURSIVE, OPT_SORT)),

    # ------------------------------------------------------------ batch --
    _m("batch_word_pdf", "📦", GROUP_BATCH, IN_FOLDER, OUT_FOLDER, (), requires_word=True),
    _m("batch_word_images", "🖼️", GROUP_BATCH, IN_FOLDER, OUT_FOLDER,
       (OPT_RENDER,), requires_word=True),
]}


def group_heading(group: str) -> tuple[str, str]:
    """Translated (title, subtitle) for a group of conversions."""
    return i18n.t(f"group.{group}.title"), i18n.t(f"group.{group}.sub")


def modes_in_group(group: str) -> list[ModeSpec]:
    return [m for m in MODES.values() if m.group == group]


def group_of(mode_key: str) -> str:
    spec = MODES.get(mode_key)
    return spec.group if spec else GROUP_MAIN
