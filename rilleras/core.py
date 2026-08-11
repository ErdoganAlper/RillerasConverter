"""Pure conversion operations for Rilleras Converter.

Nothing in this module imports Tk. Every operation takes plain paths plus
optional ``progress_cb`` / ``log_cb`` / ``cancel_event`` hooks, which keeps the
whole module unit-testable headlessly.

Heavy or platform-specific backends (``docx2pdf``, ``pdf2docx``) are imported
lazily inside the functions that need them so that startup stays fast and a
missing Word installation only fails the operations that actually need Word.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
from pathlib import Path

import fitz  # PyMuPDF
import img2pdf
from PIL import Image

# ---------------------------------------------------------------- constants --

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
OUT_IMAGE_FORMATS = [
    "jpg", "png", "webp", "tif", "bmp", "pdf",
    "ico", "gif", "tga", "ppm", "pgm", "pbm", "dds",
]
PDF_EXTS = {".pdf"}
DOCX_EXTS = {".docx"}

PRESETS = {
    "High Quality Print (300dpi PNG)": dict(dpi=300, fmt="png", jpg_quality=90),
    "Small Share (150dpi JPG q75)": dict(dpi=150, fmt="jpg", jpg_quality=75),
    "Fast Draft (100dpi JPG q65)": dict(dpi=100, fmt="jpg", jpg_quality=65),
    "Archive (300dpi JPG q85)": dict(dpi=300, fmt="jpg", jpg_quality=85),
}


class ConversionError(RuntimeError):
    """A failure the user can act on — shown verbatim in the UI."""


class Cancelled(ConversionError):
    """Raised when the user cancels a running job."""


# ------------------------------------------------------------------ helpers --

def natural_key(s: str):
    """Sort key so 'page2' comes before 'page10'."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def open_in_explorer(path: Path):
    target = path if path.is_dir() else path.parent
    try:
        os.startfile(str(target))  # noqa: S606 - Windows shell open
    except Exception:
        try:
            subprocess.Popen(["explorer", str(target)])
        except Exception:
            pass


def _check_cancel(cancel_event):
    if cancel_event is not None and cancel_event.is_set():
        raise Cancelled("Cancelled.")


def parse_page_range(text: str, max_page: int) -> list[int]:
    """Turn '1-3,7,10-' into a sorted list of 0-based page indexes."""
    t = (text or "").strip().lower()
    if t in ("", "all", "*"):
        return list(range(max_page))

    out: set[int] = set()
    for part in [p.strip() for p in t.split(",") if p.strip()]:
        try:
            if "-" in part:
                a, b = part.split("-", 1)
                a, b = a.strip(), b.strip()
                start = int(a) if a else 1
                end = int(b) if b else max_page
                start, end = max(1, start), min(max_page, end)
                if start <= end:
                    out.update(range(start - 1, end))
            else:
                p = int(part)
                if 1 <= p <= max_page:
                    out.add(p - 1)
        except ValueError as exc:
            raise ConversionError(
                f"Could not read page range '{part}'. Use formats like: all, 1-3,7,10-"
            ) from exc
    return sorted(out)


def collect_images(input_path: Path, recursive: bool) -> list[Path]:
    """All image files under ``input_path`` (a file or a folder), naturally sorted."""
    if input_path.is_dir():
        files = input_path.rglob("*") if recursive else input_path.glob("*")
        imgs = [p for p in files if p.suffix.lower() in IMAGE_EXTS]
    else:
        imgs = [input_path] if input_path.suffix.lower() in IMAGE_EXTS else []
    imgs.sort(key=lambda p: natural_key(p.name))
    return imgs


def word_backend_available() -> tuple[bool, str]:
    """Report whether Word -> PDF conversion can run on this machine.

    ``docx2pdf`` drives Microsoft Word through COM, so it needs both the package
    and a real Word installation. Checking up front turns a cryptic COM
    traceback into a sentence the user can act on.
    """
    if os.name != "nt":
        return False, "Word conversion needs Microsoft Word on Windows."
    try:
        import docx2pdf  # noqa: F401
    except Exception:
        return False, "The 'docx2pdf' package is not installed."
    try:
        import win32com.client  # type: ignore

        win32com.client.Dispatch("Word.Application").Quit()
        return True, "Microsoft Word detected."
    except Exception:
        return False, "Microsoft Word does not appear to be installed."


# --------------------------------------------------------------- image save --

def pil_save_image(im: Image.Image, out_path: Path, out_fmt: str, quality: int = 90):
    out_fmt = out_fmt.lower().lstrip(".")
    quality = int(quality)

    def flatten_alpha_to_rgb(img: Image.Image, bg=(255, 255, 255)) -> Image.Image:
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            rgba = img.convert("RGBA")
            background = Image.new("RGB", rgba.size, bg)
            background.paste(rgba, mask=rgba.split()[-1])
            return background
        return img.convert("RGB")

    try:
        if out_fmt in ("jpg", "jpeg"):
            flatten_alpha_to_rgb(im).save(out_path, "JPEG", quality=quality, optimize=True)
        elif out_fmt == "png":
            im.save(out_path, "PNG", optimize=True)
        elif out_fmt == "webp":
            im.save(out_path, "WEBP", quality=quality, method=6)
        elif out_fmt in ("tif", "tiff"):
            im.save(out_path, "TIFF", compression="tiff_deflate")
        elif out_fmt == "bmp":
            im.save(out_path, "BMP")
        elif out_fmt == "pdf":
            im.convert("RGB").save(out_path, "PDF", resolution=300.0)
        elif out_fmt == "ico":
            rgba = im.convert("RGBA")
            w, h = rgba.size
            side = min(w, h)
            left, top = (w - side) // 2, (h - side) // 2
            square = rgba.crop((left, top, left + side, top + side))
            square.save(
                out_path,
                format="ICO",
                sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
            )
        elif out_fmt == "gif":
            im.convert("RGBA").convert("P", palette=Image.Palette.ADAPTIVE).save(out_path, "GIF")
        elif out_fmt == "tga":
            im.save(out_path, "TGA")
        elif out_fmt in ("ppm", "pgm", "pbm"):
            im.save(out_path, out_fmt.upper())
        elif out_fmt == "dds":
            # DDS write support is missing from some Pillow builds.
            im.save(out_path, "DDS")
        else:
            raise ConversionError(f"Unsupported output format: {out_fmt}")
    except ConversionError:
        raise
    except Exception as e:
        raise ConversionError(
            f"Failed saving as .{out_fmt}. Your Pillow build may not support it.\nDetails: {e}"
        ) from e


# --------------------------------------------------------------- image → * --

def image_to_image(input_path: Path, out_path: Path, out_fmt: str,
                   recursive: bool, max_size: int | None, quality: int,
                   progress_cb=None, cancel_event=None, log_cb=None):
    out_fmt = out_fmt.lower()
    if out_fmt not in OUT_IMAGE_FORMATS:
        raise ConversionError(f"Choose output format from: {', '.join(OUT_IMAGE_FORMATS)}")

    if input_path.is_dir():
        ensure_dir(out_path)
        imgs = collect_images(input_path, recursive)
        if not imgs:
            raise ConversionError("No images found.")

        total = len(imgs)
        for i, p in enumerate(imgs, start=1):
            _check_cancel(cancel_event)
            with Image.open(p) as im:
                im.load()
                if max_size and max_size > 0:
                    im.thumbnail((max_size, max_size))
                out_file = out_path / f"{p.stem}.{out_fmt}"
                pil_save_image(im, out_file, out_fmt, quality=quality)
            if log_cb:
                log_cb(f"Saved: {out_file}")
            if progress_cb:
                progress_cb(i, total)
    else:
        if input_path.suffix.lower() not in IMAGE_EXTS:
            raise ConversionError("Input must be an image file.")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        _check_cancel(cancel_event)

        with Image.open(input_path) as im:
            im.load()
            if max_size and max_size > 0:
                im.thumbnail((max_size, max_size))
            pil_save_image(im, out_path, out_fmt, quality=quality)

        if log_cb:
            log_cb(f"Saved: {out_path}")
        if progress_cb:
            progress_cb(1, 1)


def batch_image_convert(in_dir: Path, out_dir: Path, out_fmt: str, recursive: bool,
                        progress_cb=None, cancel_event=None, log_cb=None):
    image_to_image(in_dir, out_dir, out_fmt, recursive=recursive, max_size=None,
                   quality=90, progress_cb=progress_cb, cancel_event=cancel_event,
                   log_cb=log_cb)


def batch_image_resize(in_dir: Path, out_dir: Path, out_fmt: str, max_size: int,
                       quality: int, recursive: bool,
                       progress_cb=None, cancel_event=None, log_cb=None):
    image_to_image(in_dir, out_dir, out_fmt, recursive=recursive, max_size=max_size,
                   quality=quality, progress_cb=progress_cb, cancel_event=cancel_event,
                   log_cb=log_cb)


def images_to_pdf(input_path: Path, out_pdf: Path, recursive: bool, sort_mode: str,
                  progress_cb=None, cancel_event=None, log_cb=None):
    images = collect_images(input_path, recursive)
    if not images:
        raise ConversionError("No images found.")

    if sort_mode == "mtime":
        images.sort(key=lambda p: p.stat().st_mtime)
    elif sort_mode == "name":
        images.sort(key=lambda p: p.name.lower())

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    if log_cb:
        log_cb(f"Found {len(images)} images. Creating PDF...")
    _check_cancel(cancel_event)

    with open(out_pdf, "wb") as f:
        f.write(img2pdf.convert([str(p) for p in images]))

    if log_cb:
        log_cb(f"Created: {out_pdf}")
    if progress_cb:
        progress_cb(1, 1)


def images_to_pdf_per_subfolder(in_dir: Path, out_dir: Path, recursive: bool, sort_mode: str,
                                progress_cb=None, cancel_event=None, log_cb=None):
    ensure_dir(out_dir)
    subfolders = [p for p in in_dir.iterdir() if p.is_dir()]
    if not subfolders:
        raise ConversionError("No subfolders found. Put images into subfolders.")

    total = len(subfolders)
    for i, folder in enumerate(subfolders, start=1):
        _check_cancel(cancel_event)
        images_to_pdf(folder, out_dir / f"{folder.name}.pdf", recursive=recursive,
                      sort_mode=sort_mode, progress_cb=None,
                      cancel_event=cancel_event, log_cb=log_cb)
        if progress_cb:
            progress_cb(i, total)


# ----------------------------------------------------------------- PDF → * --

def pdf_to_images(pdf_path: Path, out_dir: Path, dpi: int, fmt: str, jpg_quality: int,
                  page_range="all", only_pages_with_images=False,
                  progress_cb=None, cancel_event=None, log_cb=None):
    ensure_dir(out_dir)
    with fitz.open(pdf_path) as doc:
        page_indexes = parse_page_range(page_range, len(doc))

        if only_pages_with_images:
            filtered = []
            for pno in page_indexes:
                _check_cancel(cancel_event)
                if doc[pno].get_images(full=True):
                    filtered.append(pno)
            page_indexes = filtered

        total = len(page_indexes)
        if total == 0:
            raise ConversionError("No pages selected (or no pages with images).")

        mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        for i, pno in enumerate(page_indexes, start=1):
            _check_cancel(cancel_event)
            pix = doc[pno].get_pixmap(matrix=mat, alpha=False)
            out_path = out_dir / f"page_{pno + 1}.{fmt}"

            if fmt.lower() in ("jpg", "jpeg"):
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                img.save(out_path, "JPEG", quality=jpg_quality, optimize=True)
            else:
                pix.save(str(out_path))

            if log_cb:
                log_cb(f"Saved: {out_path}")
            if progress_cb:
                progress_cb(i, total)


def pdf_to_long_image(pdf_path: Path, out_image: Path, dpi: int, fmt: str, jpg_quality: int,
                      page_range="all", progress_cb=None, cancel_event=None, log_cb=None):
    with fitz.open(pdf_path) as doc:
        page_indexes = parse_page_range(page_range, len(doc))
        if not page_indexes:
            raise ConversionError("No pages selected.")

        mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
        imgs = []
        total = len(page_indexes)
        for i, pno in enumerate(page_indexes, start=1):
            _check_cancel(cancel_event)
            pix = doc[pno].get_pixmap(matrix=mat, alpha=False)
            imgs.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
            if progress_cb:
                progress_cb(i, total)

    max_w = max(im.width for im in imgs)
    total_h = sum(im.height for im in imgs)
    stitched = Image.new("RGB", (max_w, total_h), (255, 255, 255))
    y = 0
    for im in imgs:
        stitched.paste(im, (0, y))
        y += im.height

    out_image.parent.mkdir(parents=True, exist_ok=True)
    if fmt.lower() in ("jpg", "jpeg"):
        stitched.save(out_image, "JPEG", quality=jpg_quality, optimize=True)
    else:
        stitched.save(out_image, "PNG")

    if log_cb:
        log_cb(f"Created: {out_image}")


def pdf_to_text(pdf_path: Path, out_txt: Path, page_range="all",
                progress_cb=None, cancel_event=None, log_cb=None):
    with fitz.open(pdf_path) as doc:
        idxs = parse_page_range(page_range, len(doc))
        total = len(idxs)
        out_txt.parent.mkdir(parents=True, exist_ok=True)
        with open(out_txt, "w", encoding="utf-8") as f:
            for i, pno in enumerate(idxs, start=1):
                _check_cancel(cancel_event)
                f.write(doc[pno].get_text("text"))
                f.write("\n\n")
                if progress_cb:
                    progress_cb(i, total)
    if log_cb:
        log_cb(f"Created: {out_txt}")


class _Pdf2DocxLogBridge(logging.Handler):
    """Forward pdf2docx's own log records into the app log + progress bar.

    pdf2docx reports per-page progress through the logging module rather than a
    callback, so this is the only way to drive a real progress bar.
    """

    def __init__(self, total: int, progress_cb=None, log_cb=None):
        super().__init__(level=logging.INFO)
        self.total = max(1, total)
        self.progress_cb = progress_cb
        self.log_cb = log_cb
        self.pages_seen = 0

    def emit(self, record):
        try:
            msg = record.getMessage().strip()
        except Exception:
            return
        if not msg:
            return
        if re.search(r"\bpage\s+\d+", msg, re.IGNORECASE):
            self.pages_seen += 1
            if self.progress_cb:
                self.progress_cb(min(self.pages_seen, self.total), self.total)
        if self.log_cb:
            self.log_cb(msg)


def pdf_to_word(pdf_path: Path, out_docx: Path, page_range="all",
                progress_cb=None, cancel_event=None, log_cb=None):
    """Convert a PDF to an editable .docx, reconstructing the page layout.

    Uses pdf2docx, which rebuilds paragraphs, tables and images rather than
    dumping raw text. Scanned/image-only PDFs have no text layer, so they come
    out as pictures — that is a property of the source, not a failure here.
    """
    try:
        from pdf2docx import Converter
    except Exception as e:
        raise ConversionError(
            "PDF → Word needs the 'pdf2docx' package.\n"
            "Install it with:  pip install pdf2docx\n"
            f"Details: {e}"
        ) from e

    if out_docx.suffix.lower() != ".docx":
        out_docx = out_docx.with_suffix(".docx")
    out_docx.parent.mkdir(parents=True, exist_ok=True)

    _check_cancel(cancel_event)

    with fitz.open(pdf_path) as doc:
        total_pages = len(doc)
        has_text = any(doc[i].get_text("text").strip() for i in range(min(3, total_pages)))
    pages = parse_page_range(page_range, total_pages)
    if not pages:
        raise ConversionError("No pages selected.")

    if not has_text and log_cb:
        log_cb("Note: this PDF has no text layer (likely a scan). "
               "Output will contain page images, not editable text.")

    if log_cb:
        log_cb(f"Converting {len(pages)} page(s) to Word — this can take a while...")

    bridge = _Pdf2DocxLogBridge(len(pages), progress_cb=progress_cb, log_cb=log_cb)
    pdf2docx_logger = logging.getLogger("pdf2docx")
    prev_level, prev_propagate = pdf2docx_logger.level, pdf2docx_logger.propagate
    pdf2docx_logger.setLevel(logging.INFO)
    pdf2docx_logger.addHandler(bridge)

    cv = None
    try:
        cv = Converter(str(pdf_path))
        # multi_processing spawns workers that ignore our cancel flag, so keep
        # the conversion in-process.
        cv.convert(str(out_docx), pages=pages, multi_processing=False)
    except Cancelled:
        raise
    except Exception as e:
        raise ConversionError(f"PDF → Word failed: {e}") from e
    finally:
        if cv is not None:
            try:
                cv.close()
            except Exception:
                pass
        pdf2docx_logger.removeHandler(bridge)
        pdf2docx_logger.setLevel(prev_level)
        pdf2docx_logger.propagate = prev_propagate

    if progress_cb:
        progress_cb(len(pages), len(pages))
    if log_cb:
        log_cb(f"Created: {out_docx}")


# ------------------------------------------------------------- PDF surgery --

def merge_pdfs(pdf_files: list[Path], out_pdf: Path,
               progress_cb=None, cancel_event=None, log_cb=None):
    if not pdf_files:
        raise ConversionError("No PDFs selected.")
    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    merged = fitz.open()
    try:
        total = len(pdf_files)
        for i, p in enumerate(pdf_files, start=1):
            _check_cancel(cancel_event)
            with fitz.open(p) as src:
                merged.insert_pdf(src)
            if log_cb:
                log_cb(f"Added: {p}")
            if progress_cb:
                progress_cb(i, total)
        merged.save(out_pdf)
    finally:
        merged.close()

    if log_cb:
        log_cb(f"Created: {out_pdf}")


def split_pdf(pdf_path: Path, out_dir: Path, mode: str, ranges: str,
              progress_cb=None, cancel_event=None, log_cb=None):
    ensure_dir(out_dir)
    with fitz.open(pdf_path) as doc:
        n = len(doc)

        if mode == "each":
            for i in range(n):
                _check_cancel(cancel_event)
                new = fitz.open()
                new.insert_pdf(doc, from_page=i, to_page=i)
                out = out_dir / f"{pdf_path.stem}_page_{i + 1}.pdf"
                new.save(out)
                new.close()
                if log_cb:
                    log_cb(f"Saved: {out}")
                if progress_cb:
                    progress_cb(i + 1, n)
        else:
            blocks = [b.strip() for b in ranges.split(",") if b.strip()]
            if not blocks:
                raise ConversionError("Provide ranges like 1-3,4-7")
            total = len(blocks)
            for idx, b in enumerate(blocks, start=1):
                _check_cancel(cancel_event)
                if "-" not in b:
                    raise ConversionError("Ranges must be like 1-3,4-7")
                a, c = b.split("-", 1)
                try:
                    a, c = int(a.strip()), int(c.strip())
                except ValueError as exc:
                    raise ConversionError(f"Could not read range '{b}'.") from exc
                a, c = max(1, a), min(n, c)
                if a > c:
                    continue
                new = fitz.open()
                new.insert_pdf(doc, from_page=a - 1, to_page=c - 1)
                out = out_dir / f"{pdf_path.stem}_{a}-{c}.pdf"
                new.save(out)
                new.close()
                if log_cb:
                    log_cb(f"Saved: {out}")
                if progress_cb:
                    progress_cb(idx, total)


def rotate_pdf(pdf_path: Path, out_pdf: Path, degrees: int, page_range="all",
               progress_cb=None, cancel_event=None, log_cb=None):
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    with fitz.open(pdf_path) as doc:
        idxs = parse_page_range(page_range, len(doc))
        total = len(idxs)
        for i, pno in enumerate(idxs, start=1):
            _check_cancel(cancel_event)
            page = doc[pno]
            page.set_rotation((page.rotation + degrees) % 360)
            if progress_cb:
                progress_cb(i, total)
        doc.save(out_pdf)
    if log_cb:
        log_cb(f"Created: {out_pdf}")


def compress_pdf_clean(pdf_path: Path, out_pdf: Path, log_cb=None):
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    with fitz.open(pdf_path) as doc:
        doc.save(out_pdf, garbage=4, deflate=True, clean=True)
    if log_cb:
        log_cb(f"Created (clean/deflate): {out_pdf}")


def compress_pdf_rebuild(pdf_path: Path, out_pdf: Path, dpi: int,
                         progress_cb=None, cancel_event=None, log_cb=None):
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    mat = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    out = fitz.open()
    try:
        with fitz.open(pdf_path) as doc:
            n = len(doc)
            for i in range(n):
                _check_cancel(cancel_event)
                pix = doc[i].get_pixmap(matrix=mat, alpha=False)
                rect = fitz.Rect(0, 0, pix.width, pix.height)
                page = out.new_page(width=rect.width, height=rect.height)
                page.insert_image(rect, stream=pix.tobytes("jpeg"))
                if progress_cb:
                    progress_cb(i + 1, n)
        out.save(out_pdf, garbage=4, deflate=True)
    finally:
        out.close()
    if log_cb:
        log_cb(f"Created (rebuild at {dpi} dpi): {out_pdf}")


# ---------------------------------------------------------------- Word → * --

def word_to_pdf(docx_path: Path, out_pdf: Path, log_cb=None):
    ok, why = word_backend_available()
    if not ok:
        raise ConversionError(
            f"Word → PDF is unavailable. {why}\n\n"
            "This conversion automates Microsoft Word, so Word must be installed "
            "and licensed on this PC."
        )

    from docx2pdf import convert as docx2pdf_convert

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    if log_cb:
        log_cb("Word → PDF (driving Microsoft Word)...")
    docx2pdf_convert(str(docx_path), str(out_pdf))
    if log_cb:
        log_cb(f"Created: {out_pdf}")


def word_to_images(docx_path: Path, out_dir: Path, dpi: int, fmt: str, jpg_quality: int,
                   page_range="all", progress_cb=None, cancel_event=None, log_cb=None):
    ensure_dir(out_dir)
    temp_pdf = out_dir / (docx_path.stem + "___temp.pdf")
    _check_cancel(cancel_event)
    try:
        word_to_pdf(docx_path, temp_pdf, log_cb=log_cb)
        pdf_to_images(temp_pdf, out_dir, dpi, fmt, jpg_quality, page_range=page_range,
                      progress_cb=progress_cb, cancel_event=cancel_event, log_cb=log_cb)
    finally:
        try:
            temp_pdf.unlink()
        except Exception:
            pass


def batch_word_convert(in_dir: Path, out_dir: Path, mode: str,
                       dpi: int, fmt: str, jpg_quality: int,
                       progress_cb=None, cancel_event=None, log_cb=None):
    ensure_dir(out_dir)
    docs = sorted(in_dir.glob("*.docx"), key=lambda p: p.name.lower())
    if not docs:
        raise ConversionError("No .docx files found in folder.")

    total = len(docs)
    for i, docx in enumerate(docs, start=1):
        _check_cancel(cancel_event)
        if mode == "pdf":
            word_to_pdf(docx, out_dir / (docx.stem + ".pdf"), log_cb=log_cb)
        else:
            word_to_images(docx, out_dir / docx.stem, dpi, fmt, jpg_quality,
                           page_range="all", progress_cb=None,
                           cancel_event=cancel_event, log_cb=log_cb)
        if progress_cb:
            progress_cb(i, total)
