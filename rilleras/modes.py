"""Declarative description of every conversion the app offers.

The original build repeated the same mode list in four places (labels, input
browser, output browser, validation), which is how the labels drifted out of
sync with reality. Everything now derives from this one table.
"""

from __future__ import annotations

from dataclasses import dataclass, field

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
OPT_SORT = "sort"            # image ordering for image -> pdf
OPT_IMAGE_OUT = "image_out"  # output format / max size / quality
OPT_ROTATE = "rotate"
OPT_SPLIT = "split"
OPT_COMPRESS = "compress"
OPT_MERGE = "merge"

GROUP_MAIN = "main"
GROUP_PDF = "pdf"
GROUP_IMAGE = "image"
GROUP_BATCH = "batch"


@dataclass(frozen=True)
class ModeSpec:
    key: str
    icon: str
    title: str
    subtitle: str
    group: str
    input_kind: str
    output_kind: str
    options: tuple[str, ...] = field(default_factory=tuple)
    requires_word: bool = False

    @property
    def input_label(self) -> str:
        return {
            IN_DOCX: "Input Word document (.docx)",
            IN_PDF: "Input PDF (.pdf)",
            IN_FOLDER: "Input folder",
            IN_IMAGE_OR_FOLDER: "Input image or folder",
            IN_NONE: "Not used — build the merge list below",
        }[self.input_kind]

    @property
    def output_label(self) -> str:
        return {
            OUT_FOLDER: "Output folder",
            OUT_PDF: "Output PDF (.pdf)",
            OUT_DOCX: "Output Word document (.docx)",
            OUT_TXT: "Output text file (.txt)",
            OUT_IMAGE: "Output image (.png / .jpg)",
            OUT_IMAGE_OR_FOLDER: "Output folder, or a file when the input is one image",
        }[self.output_kind]


def _m(*args, **kwargs) -> ModeSpec:
    return ModeSpec(*args, **kwargs)


MODES: dict[str, ModeSpec] = {m.key: m for m in [
    # ---------------------------------------------------------- convert --
    _m("pdf_to_word", "📝", "PDF → Word",
       "Editable .docx with layout kept",
       GROUP_MAIN, IN_PDF, OUT_DOCX, (OPT_PAGES,)),
    _m("word_to_pdf", "📄", "Word → PDF",
       "Needs Microsoft Word installed",
       GROUP_MAIN, IN_DOCX, OUT_PDF, (), requires_word=True),
    _m("pdf_to_images", "🖼️", "PDF → Images",
       "One image file per page",
       GROUP_MAIN, IN_PDF, OUT_FOLDER, (OPT_RENDER, OPT_PAGES)),
    _m("images_to_pdf", "📚", "Images → PDF",
       "Lossless, naturally sorted",
       GROUP_MAIN, IN_IMAGE_OR_FOLDER, OUT_PDF, (OPT_RECURSIVE, OPT_SORT)),
    _m("word_to_images", "🧾", "Word → Images",
       "Via Word, then rendered per page",
       GROUP_MAIN, IN_DOCX, OUT_FOLDER, (OPT_RENDER, OPT_PAGES), requires_word=True),
    _m("pdf_to_text", "🔤", "PDF → Text",
       "Plain .txt from the text layer",
       GROUP_MAIN, IN_PDF, OUT_TXT, (OPT_PAGES,)),
    _m("pdf_to_long_image", "🧵", "PDF → Long Image",
       "All pages stitched vertically",
       GROUP_MAIN, IN_PDF, OUT_IMAGE, (OPT_RENDER, OPT_PAGES)),
    _m("pdf_to_images_only_img_pages", "🔎", "PDF → Images (image pages)",
       "Skips pages with no pictures",
       GROUP_MAIN, IN_PDF, OUT_FOLDER, (OPT_RENDER, OPT_PAGES)),
    _m("image_to_image", "🔄", "Image → Image",
       "Convert format, optionally resize",
       GROUP_MAIN, IN_IMAGE_OR_FOLDER, OUT_IMAGE_OR_FOLDER,
       (OPT_IMAGE_OUT, OPT_RECURSIVE)),

    # -------------------------------------------------------- pdf tools --
    _m("merge_pdfs", "🔗", "Merge PDFs",
       "Combine many files into one",
       GROUP_PDF, IN_NONE, OUT_PDF, (OPT_MERGE,)),
    _m("split_pdf", "✂️", "Split PDF",
       "Every page, or custom ranges",
       GROUP_PDF, IN_PDF, OUT_FOLDER, (OPT_SPLIT,)),
    _m("rotate_pdf", "🔃", "Rotate PDF",
       "Turn selected pages 90/180/270°",
       GROUP_PDF, IN_PDF, OUT_PDF, (OPT_ROTATE, OPT_PAGES)),
    _m("compress_pdf", "🗜️", "Compress PDF",
       "Clean up, or rebuild at lower DPI",
       GROUP_PDF, IN_PDF, OUT_PDF, (OPT_COMPRESS,)),

    # ------------------------------------------------------ image tools --
    _m("batch_image_convert", "🎛️", "Batch Convert Images",
       "Whole folder to one format",
       GROUP_IMAGE, IN_FOLDER, OUT_FOLDER, (OPT_IMAGE_OUT, OPT_RECURSIVE)),
    _m("batch_image_resize", "📐", "Batch Resize Images",
       "Shrink to a max dimension",
       GROUP_IMAGE, IN_FOLDER, OUT_FOLDER, (OPT_IMAGE_OUT, OPT_RECURSIVE)),
    _m("images_to_pdf_per_subfolder", "🗂️", "Subfolders → PDFs",
       "One PDF per subfolder",
       GROUP_IMAGE, IN_FOLDER, OUT_FOLDER, (OPT_RECURSIVE, OPT_SORT)),

    # ------------------------------------------------------------ batch --
    _m("batch_word_pdf", "📦", "Word folder → PDFs",
       "Every .docx in a folder",
       GROUP_BATCH, IN_FOLDER, OUT_FOLDER, (), requires_word=True),
    _m("batch_word_images", "🖼️", "Word folder → Images",
       "A subfolder of images per .docx",
       GROUP_BATCH, IN_FOLDER, OUT_FOLDER, (OPT_RENDER,), requires_word=True),
]}

GROUP_TITLES = {
    GROUP_MAIN: ("Convert", "Everyday document and image conversions"),
    GROUP_PDF: ("PDF Tools", "Merge, split, rotate and shrink PDF files"),
    GROUP_IMAGE: ("Image Tools", "Bulk operations across a folder of images"),
    GROUP_BATCH: ("Batch Word", "Process a whole folder of Word documents"),
}


def modes_in_group(group: str) -> list[ModeSpec]:
    return [m for m in MODES.values() if m.group == group]


def group_of(mode_key: str) -> str:
    spec = MODES.get(mode_key)
    return spec.group if spec else GROUP_MAIN
