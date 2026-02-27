import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading, queue, re, os, json, sys, subprocess
from datetime import datetime

import fitz  # PyMuPDF
import img2pdf
from docx2pdf import convert as docx2pdf_convert
from PIL import Image

# Optional drag & drop
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except Exception:
    HAS_DND = False

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
OUT_IMAGE_FORMATS = [
    "jpg", "png", "webp", "tif", "bmp", "pdf",
    "ico", "gif", "tga", "ppm", "pgm", "pbm", "dds"
]
PDF_EXTS = {".pdf"}
DOCX_EXTS = {".docx"}

# ---------------- Presets ----------------
PRESETS = {
    "High Quality Print (300dpi PNG)": dict(dpi=300, fmt="png", jpg_quality=90),
    "Small Share (150dpi JPG q75)": dict(dpi=150, fmt="jpg", jpg_quality=75),
    "Fast Draft (100dpi JPG q65)": dict(dpi=100, fmt="jpg", jpg_quality=65),
    "Archive (300dpi JPG q85)": dict(dpi=300, fmt="jpg", jpg_quality=85),
}

# ---------------- Settings ----------------
def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent

SETTINGS_FILE = app_dir() / "settings.json"

DEFAULT_SETTINGS = {
    "remember_paths": True,             # <-- your “turn off last_in_path” switch
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

    # merge defaults
    merged = dict(DEFAULT_SETTINGS)
    merged.update(data if isinstance(data, dict) else {})
    # basic sanity
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

# ---------------- Helpers ----------------
def natural_key(s: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

def open_in_explorer(path: Path):
    try:
        os.startfile(str(path if path.is_dir() else path.parent))
    except Exception:
        try:
            subprocess.Popen(["explorer", str(path.parent)])
        except Exception:
            pass

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def log_time():
    return datetime.now().strftime("%H:%M:%S")

def parse_page_range(text: str, max_page: int):
    t = (text or "").strip().lower()
    if t in ("", "all", "*"):
        return list(range(max_page))
    out = set()
    parts = [p.strip() for p in t.split(",") if p.strip()]
    for part in parts:
        if "-" in part:
            a, b = part.split("-", 1)
            a, b = a.strip(), b.strip()
            start = int(a) if a else 1
            end = int(b) if b else max_page
            start, end = max(1, start), min(max_page, end)
            if start <= end:
                for p in range(start, end + 1):
                    out.add(p - 1)
        else:
            p = int(part)
            if 1 <= p <= max_page:
                out.add(p - 1)
    return sorted(out)

# ---------------- Image save (supports ico etc) ----------------
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
            rgb = flatten_alpha_to_rgb(im)
            rgb.save(out_path, "JPEG", quality=quality, optimize=True)

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
            left = (w - side) // 2
            top = (h - side) // 2
            square = rgba.crop((left, top, left + side, top + side))
            sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            square.save(out_path, format="ICO", sizes=sizes)

        elif out_fmt == "gif":
            im2 = im.convert("RGBA").convert("P", palette=Image.Palette.ADAPTIVE)
            im2.save(out_path, "GIF")

        elif out_fmt == "tga":
            im.save(out_path, "TGA")

        elif out_fmt in ("ppm", "pgm", "pbm"):
            im.save(out_path, out_fmt.upper())

        elif out_fmt == "dds":
            # NOTE: DDS may not be supported in some Pillow builds
            im.save(out_path, "DDS")

        else:
            raise RuntimeError(f"Unsupported output format: {out_fmt}")

    except Exception as e:
        raise RuntimeError(f"Failed saving as .{out_fmt}. Your Pillow build may not support it.\nDetails: {e}")

# ---------------- Core ops ----------------
def image_to_image(input_path: Path, out_path: Path, out_fmt: str,
                   recursive: bool, max_size: int | None, quality: int,
                   progress_cb=None, cancel_event=None, log_cb=None):
    out_fmt = out_fmt.lower()
    if out_fmt not in OUT_IMAGE_FORMATS:
        raise RuntimeError(f"Choose output format from: {', '.join(OUT_IMAGE_FORMATS)}")

    if input_path.is_dir():
        ensure_dir(out_path)
        files = input_path.rglob("*") if recursive else input_path.glob("*")
        imgs = [p for p in files if p.suffix.lower() in IMAGE_EXTS]
        if not imgs:
            raise RuntimeError("No images found.")
        imgs.sort(key=lambda p: natural_key(p.name))

        total = len(imgs)
        for i, p in enumerate(imgs, start=1):
            if cancel_event and cancel_event.is_set():
                raise RuntimeError("Cancelled.")
            im = Image.open(p)
            im.load()

            if max_size and max_size > 0:
                im.thumbnail((max_size, max_size))

            out_file = out_path / f"{p.stem}.{out_fmt}"
            pil_save_image(im, out_file, out_fmt, quality=quality)

            if log_cb: log_cb(f"Saved: {out_file}")
            if progress_cb: progress_cb(i, total)

    else:
        if input_path.suffix.lower() not in IMAGE_EXTS:
            raise RuntimeError("Input must be an image file.")
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if cancel_event and cancel_event.is_set():
            raise RuntimeError("Cancelled.")

        im = Image.open(input_path)
        im.load()
        if max_size and max_size > 0:
            im.thumbnail((max_size, max_size))

        pil_save_image(im, out_path, out_fmt, quality=quality)

        if log_cb: log_cb(f"Saved: {out_path}")
        if progress_cb: progress_cb(1, 1)

def pdf_to_images(pdf_path: Path, out_dir: Path, dpi: int, fmt: str, jpg_quality: int,
                  page_range="all", only_pages_with_images=False,
                  progress_cb=None, cancel_event=None, log_cb=None):
    ensure_dir(out_dir)
    doc = fitz.open(pdf_path)
    max_page = len(doc)

    page_indexes = parse_page_range(page_range, max_page)

    if only_pages_with_images:
        filtered = []
        for pno in page_indexes:
            if cancel_event and cancel_event.is_set():
                raise RuntimeError("Cancelled.")
            imgs = doc[pno].get_images(full=True)
            if imgs:
                filtered.append(pno)
        page_indexes = filtered

    total = len(page_indexes)
    if total == 0:
        raise RuntimeError("No pages selected (or no pages with images).")

    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    for i, pno in enumerate(page_indexes, start=1):
        if cancel_event and cancel_event.is_set():
            raise RuntimeError("Cancelled.")
        page = doc[pno]
        pix = page.get_pixmap(matrix=mat, alpha=False)
        out_path = out_dir / f"page_{pno+1}.{fmt}"

        if fmt.lower() in ("jpg", "jpeg"):
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            img.save(out_path, "JPEG", quality=jpg_quality, optimize=True)
        else:
            pix.save(str(out_path))

        if log_cb: log_cb(f"Saved: {out_path}")
        if progress_cb: progress_cb(i, total)

def word_to_pdf(docx_path: Path, out_pdf: Path, log_cb=None):
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    if log_cb: log_cb("Word → PDF (requires MS Word)...")
    docx2pdf_convert(str(docx_path), str(out_pdf))
    if log_cb: log_cb(f"Created: {out_pdf}")

def word_to_images(docx_path: Path, out_dir: Path, dpi: int, fmt: str, jpg_quality: int,
                   page_range="all", progress_cb=None, cancel_event=None, log_cb=None):
    ensure_dir(out_dir)
    temp_pdf = out_dir / (docx_path.stem + "___temp.pdf")
    if cancel_event and cancel_event.is_set():
        raise RuntimeError("Cancelled.")
    word_to_pdf(docx_path, temp_pdf, log_cb=log_cb)
    pdf_to_images(temp_pdf, out_dir, dpi, fmt, jpg_quality, page_range=page_range,
                  progress_cb=progress_cb, cancel_event=cancel_event, log_cb=log_cb)
    try:
        temp_pdf.unlink()
    except Exception:
        pass

def images_to_pdf(input_path: Path, out_pdf: Path, recursive: bool, sort_mode: str,
                  progress_cb=None, cancel_event=None, log_cb=None):
    if input_path.is_dir():
        files = input_path.rglob("*") if recursive else input_path.glob("*")
        images = [p for p in files if p.suffix.lower() in IMAGE_EXTS]
    else:
        images = [input_path] if input_path.suffix.lower() in IMAGE_EXTS else []

    if not images:
        raise RuntimeError("No images found.")

    if sort_mode == "mtime":
        images.sort(key=lambda p: p.stat().st_mtime)
    elif sort_mode == "name":
        images.sort(key=lambda p: p.name.lower())
    else:
        images.sort(key=lambda p: natural_key(p.name))

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    if log_cb: log_cb(f"Found {len(images)} images. Creating PDF...")

    if cancel_event and cancel_event.is_set():
        raise RuntimeError("Cancelled.")

    with open(out_pdf, "wb") as f:
        f.write(img2pdf.convert([str(p) for p in images]))

    if log_cb: log_cb(f"Created: {out_pdf}")
    if progress_cb: progress_cb(1, 1)

def pdf_to_long_image(pdf_path: Path, out_image: Path, dpi: int, fmt: str, jpg_quality: int,
                      page_range="all", progress_cb=None, cancel_event=None, log_cb=None):
    doc = fitz.open(pdf_path)
    page_indexes = parse_page_range(page_range, len(doc))
    if not page_indexes:
        raise RuntimeError("No pages selected.")

    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    imgs = []
    total = len(page_indexes)
    for i, pno in enumerate(page_indexes, start=1):
        if cancel_event and cancel_event.is_set():
            raise RuntimeError("Cancelled.")
        pix = doc[pno].get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        imgs.append(img)
        if progress_cb: progress_cb(i, total)

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

    if log_cb: log_cb(f"Created: {out_image}")

def merge_pdfs(pdf_files: list[Path], out_pdf: Path, progress_cb=None, cancel_event=None, log_cb=None):
    if not pdf_files:
        raise RuntimeError("No PDFs selected.")
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    merged = fitz.open()
    total = len(pdf_files)
    for i, p in enumerate(pdf_files, start=1):
        if cancel_event and cancel_event.is_set():
            raise RuntimeError("Cancelled.")
        src = fitz.open(p)
        merged.insert_pdf(src)
        if log_cb: log_cb(f"Added: {p}")
        if progress_cb: progress_cb(i, total)
    merged.save(out_pdf)
    merged.close()
    if log_cb: log_cb(f"Created: {out_pdf}")

def split_pdf(pdf_path: Path, out_dir: Path, mode: str, ranges: str,
              progress_cb=None, cancel_event=None, log_cb=None):
    ensure_dir(out_dir)
    doc = fitz.open(pdf_path)
    n = len(doc)

    if mode == "each":
        total = n
        for i in range(n):
            if cancel_event and cancel_event.is_set():
                raise RuntimeError("Cancelled.")
            new = fitz.open()
            new.insert_pdf(doc, from_page=i, to_page=i)
            out = out_dir / f"{pdf_path.stem}_page_{i+1}.pdf"
            new.save(out)
            new.close()
            if log_cb: log_cb(f"Saved: {out}")
            if progress_cb: progress_cb(i+1, total)
    else:
        blocks = [b.strip() for b in ranges.split(",") if b.strip()]
        if not blocks:
            raise RuntimeError("Provide ranges like 1-3,4-7")
        total = len(blocks)
        for idx, b in enumerate(blocks, start=1):
            if cancel_event and cancel_event.is_set():
                raise RuntimeError("Cancelled.")
            if "-" not in b:
                raise RuntimeError("Ranges must be like 1-3,4-7")
            a, c = b.split("-", 1)
            a, c = int(a.strip()), int(c.strip())
            a, c = max(1, a), min(n, c)
            if a > c:
                continue
            new = fitz.open()
            new.insert_pdf(doc, from_page=a-1, to_page=c-1)
            out = out_dir / f"{pdf_path.stem}_{a}-{c}.pdf"
            new.save(out)
            new.close()
            if log_cb: log_cb(f"Saved: {out}")
            if progress_cb: progress_cb(idx, total)

def compress_pdf_clean(pdf_path: Path, out_pdf: Path, log_cb=None):
    doc = fitz.open(pdf_path)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_pdf, garbage=4, deflate=True, clean=True)
    doc.close()
    if log_cb: log_cb(f"Created (clean/deflate): {out_pdf}")

def compress_pdf_rebuild(pdf_path: Path, out_pdf: Path, dpi: int,
                         progress_cb=None, cancel_event=None, log_cb=None):
    doc = fitz.open(pdf_path)
    n = len(doc)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    out = fitz.open()

    for i in range(n):
        if cancel_event and cancel_event.is_set():
            raise RuntimeError("Cancelled.")
        pix = doc[i].get_pixmap(matrix=mat, alpha=False)
        rect = fitz.Rect(0, 0, pix.width, pix.height)
        page = out.new_page(width=rect.width, height=rect.height)
        img_bytes = pix.tobytes("jpeg")
        page.insert_image(rect, stream=img_bytes)
        if progress_cb: progress_cb(i+1, n)

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_pdf, garbage=4, deflate=True)
    out.close()
    if log_cb: log_cb(f"Created (rebuild at {dpi} dpi): {out_pdf}")

def rotate_pdf(pdf_path: Path, out_pdf: Path, degrees: int, page_range="all",
               progress_cb=None, cancel_event=None, log_cb=None):
    doc = fitz.open(pdf_path)
    idxs = parse_page_range(page_range, len(doc))
    total = len(idxs)
    for i, pno in enumerate(idxs, start=1):
        if cancel_event and cancel_event.is_set():
            raise RuntimeError("Cancelled.")
        page = doc[pno]
        page.set_rotation((page.rotation + degrees) % 360)
        if progress_cb: progress_cb(i, total)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_pdf)
    doc.close()
    if log_cb: log_cb(f"Created: {out_pdf}")

def batch_image_convert(in_dir: Path, out_dir: Path, out_fmt: str, recursive: bool,
                        progress_cb=None, cancel_event=None, log_cb=None):
    out_fmt = out_fmt.lower()
    if out_fmt not in OUT_IMAGE_FORMATS:
        raise RuntimeError(f"Unsupported output format: {out_fmt}")

    ensure_dir(out_dir)
    files = in_dir.rglob("*") if recursive else in_dir.glob("*")
    imgs = [p for p in files if p.suffix.lower() in IMAGE_EXTS]
    if not imgs:
        raise RuntimeError("No images found.")

    imgs.sort(key=lambda p: natural_key(p.name))
    total = len(imgs)

    for i, p in enumerate(imgs, start=1):
        if cancel_event and cancel_event.is_set():
            raise RuntimeError("Cancelled.")
        im = Image.open(p)
        im.load()
        out_path = out_dir / f"{p.stem}.{out_fmt}"
        pil_save_image(im, out_path, out_fmt, quality=90)
        if log_cb: log_cb(f"Saved: {out_path}")
        if progress_cb: progress_cb(i, total)

def batch_image_resize(in_dir: Path, out_dir: Path, out_fmt: str, max_size: int, quality: int, recursive: bool,
                       progress_cb=None, cancel_event=None, log_cb=None):
    out_fmt = out_fmt.lower()
    if out_fmt not in OUT_IMAGE_FORMATS:
        raise RuntimeError(f"Unsupported output format: {out_fmt}")

    ensure_dir(out_dir)
    files = in_dir.rglob("*") if recursive else in_dir.glob("*")
    imgs = [p for p in files if p.suffix.lower() in IMAGE_EXTS]
    if not imgs:
        raise RuntimeError("No images found.")

    imgs.sort(key=lambda p: natural_key(p.name))
    total = len(imgs)

    for i, p in enumerate(imgs, start=1):
        if cancel_event and cancel_event.is_set():
            raise RuntimeError("Cancelled.")
        im = Image.open(p)
        im.load()
        im.thumbnail((max_size, max_size))
        out_path = out_dir / f"{p.stem}.{out_fmt}"
        pil_save_image(im, out_path, out_fmt, quality=quality)
        if log_cb: log_cb(f"Saved: {out_path}")
        if progress_cb: progress_cb(i, total)

def images_to_pdf_per_subfolder(in_dir: Path, out_dir: Path, recursive: bool, sort_mode: str,
                                progress_cb=None, cancel_event=None, log_cb=None):
    ensure_dir(out_dir)
    subfolders = [p for p in in_dir.iterdir() if p.is_dir()]
    if not subfolders:
        raise RuntimeError("No subfolders found. Put images into subfolders.")
    total = len(subfolders)
    for i, folder in enumerate(subfolders, start=1):
        if cancel_event and cancel_event.is_set():
            raise RuntimeError("Cancelled.")
        out_pdf = out_dir / f"{folder.name}.pdf"
        images_to_pdf(folder, out_pdf, recursive=recursive, sort_mode=sort_mode,
                      progress_cb=None, cancel_event=cancel_event, log_cb=log_cb)
        if progress_cb: progress_cb(i, total)

def pdf_to_text(pdf_path: Path, out_txt: Path, page_range="all",
                progress_cb=None, cancel_event=None, log_cb=None):
    doc = fitz.open(pdf_path)
    idxs = parse_page_range(page_range, len(doc))
    total = len(idxs)
    out_txt.parent.mkdir(parents=True, exist_ok=True)
    with open(out_txt, "w", encoding="utf-8") as f:
        for i, pno in enumerate(idxs, start=1):
            if cancel_event and cancel_event.is_set():
                raise RuntimeError("Cancelled.")
            text = doc[pno].get_text("text")
            f.write(text)
            f.write("\n\n")
            if progress_cb: progress_cb(i, total)
    if log_cb: log_cb(f"Created: {out_txt}")

def batch_word_convert(in_dir: Path, out_dir: Path, mode: str,
                       dpi: int, fmt: str, jpg_quality: int,
                       progress_cb=None, cancel_event=None, log_cb=None):
    ensure_dir(out_dir)
    docs = sorted([p for p in in_dir.glob("*.docx")], key=lambda p: p.name.lower())
    if not docs:
        raise RuntimeError("No .docx files found in folder.")
    total = len(docs)
    for i, docx in enumerate(docs, start=1):
        if cancel_event and cancel_event.is_set():
            raise RuntimeError("Cancelled.")
        if mode == "pdf":
            out_pdf = out_dir / (docx.stem + ".pdf")
            word_to_pdf(docx, out_pdf, log_cb=log_cb)
        else:
            folder = out_dir / docx.stem
            word_to_images(docx, folder, dpi, fmt, jpg_quality, page_range="all",
                           progress_cb=None, cancel_event=cancel_event, log_cb=log_cb)
        if progress_cb: progress_cb(i, total)

# ---------------- GUI ----------------
BaseTk = TkinterDnD.Tk if HAS_DND else tk.Tk

class App(BaseTk):
    def __init__(self):
        super().__init__()
        icon_path = Path(__file__).with_name("convert.ico")
        if icon_path.exists():
            self.iconbitmap(default=str(icon_path))
        self.title("Rilleras Converter PRO")
        self.geometry("980x720")
        self.minsize(820, 600)
        self.resizable(True, True)

        self.ui_queue = queue.Queue()
        self.cancel_event = threading.Event()
        self.worker_thread = None

        self._settings = load_settings()

        # shared vars
        self.preset_var = tk.StringVar(value=self._settings["last_preset"])
        self.mode_var = tk.StringVar(value=self._settings["last_mode"])
        self.in_path = tk.StringVar()
        self.out_path = tk.StringVar()

        self.dpi_var = tk.StringVar(value=str(self._settings["dpi"]))
        self.fmt_var = tk.StringVar(value=str(self._settings["fmt"]))
        self.jpg_quality_var = tk.IntVar(value=int(self._settings["jpg_quality"]))
        self.page_range_var = tk.StringVar(value=str(self._settings["page_range"]))
        self.recursive_var = tk.BooleanVar(value=bool(self._settings["recursive"]))
        self.sort_mode_var = tk.StringVar(value=str(self._settings["sort_mode"]))

        # image tools
        self.batch_img_fmt_var = tk.StringVar(value=str(self._settings.get("batch_img_fmt", "jpg")))
        self.resize_max_var = tk.StringVar(value=str(self._settings.get("resize_max", "1600")))
        self.resize_quality_var = tk.StringVar(value=str(self._settings.get("resize_quality", "80")))

        # pdf tools
        self.rotate_deg_var = tk.IntVar(value=int(self._settings.get("rotate_deg", 90)))
        self.split_mode_var = tk.StringVar(value=str(self._settings.get("split_mode", "each")))
        self.split_ranges_var = tk.StringVar(value=str(self._settings.get("split_ranges", "1-3,4-7")))
        self.compress_mode_var = tk.StringVar(value=str(self._settings.get("compress_mode", "clean")))
        self.compress_dpi_var = tk.StringVar(value=str(self._settings.get("compress_dpi", "150")))

        # PRO settings vars
        self.remember_paths_var = tk.BooleanVar(value=bool(self._settings.get("remember_paths", True)))
        self.open_output_after_run_var = tk.BooleanVar(value=bool(self._settings.get("open_output_after_run", False)))
        self.confirm_overwrite_var = tk.BooleanVar(value=bool(self._settings.get("confirm_overwrite", True)))

        self.recent_inputs = list(self._settings.get("recent_inputs", [])) or []
        self.recent_max = int(self._settings.get("recent_max", 10) or 10)

        # merge list
        self.merge_list: list[Path] = []

        # path widgets across tabs (so labels update everywhere)
        self._path_widgets = []  # list of dicts: {"lbl_in":..., "lbl_out":...}

        self._build_ui()
        self._apply_loaded_settings()
        self._refresh_labels()
        self._refresh_recent_inputs_ui()
        self._poll_queue()

        if HAS_DND:
            self._enable_dnd()

    # -------- UI --------
    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=0)

        header = ttk.Label(self, text="Rilleras Converter PRO", font=("Segoe UI", 15, "bold"))
        header.grid(row=0, column=0, sticky="w", padx=12, pady=10)

        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 10))

        self.tab_main = ttk.Frame(nb)
        self.tab_pdf = ttk.Frame(nb)
        self.tab_img = ttk.Frame(nb)
        self.tab_batch = ttk.Frame(nb)
        self.tab_settings = ttk.Frame(nb)
        self.tab_log = ttk.Frame(nb)

        nb.add(self.tab_main, text="Main Converters")
        nb.add(self.tab_pdf, text="PDF Tools")
        nb.add(self.tab_img, text="Image Tools")
        nb.add(self.tab_batch, text="Batch")
        nb.add(self.tab_settings, text="Presets & Paths")
        nb.add(self.tab_log, text="Log")

        self._build_main_tab()
        self._build_pdf_tab()
        self._build_img_tab()
        self._build_batch_tab()
        self._build_settings_tab()
        self._build_log_tab(self.tab_log)

        run_frame = ttk.Frame(self)
        run_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 8))

        self.btn_run = ttk.Button(run_frame, text="Run", command=self._run)
        self.btn_run.grid(row=0, column=0, sticky="w")

        self.btn_cancel = ttk.Button(run_frame, text="Cancel", command=self._cancel, state="disabled")
        self.btn_cancel.grid(row=0, column=1, sticky="w", padx=(10, 0))

        self.btn_open = ttk.Button(run_frame, text="Open Output", command=self._open_output, state="disabled")
        self.btn_open.grid(row=0, column=2, sticky="w", padx=(10, 0))

        self.lbl_status = ttk.Label(run_frame, text="")
        self.lbl_status.grid(row=0, column=3, sticky="w", padx=(12, 0))

        self.progress = ttk.Progressbar(self, mode="determinate")
        self.progress.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 12))

    def _build_main_tab(self):
        f = self.tab_main
        lf = ttk.LabelFrame(f, text="Conversion Type (main)")
        lf.pack(fill="x", padx=12, pady=12)

        opts = [
            ("Word (.docx) → Images", "word_to_images"),
            ("Images → PDF", "images_to_pdf"),
            ("PDF → Images", "pdf_to_images"),
            ("Word (.docx) → PDF", "word_to_pdf"),
            ("PDF → Single Long Image (stitch)", "pdf_to_long_image"),
            ("PDF → Text (.txt)", "pdf_to_text"),
            ("PDF → Images (only pages with images)", "pdf_to_images_only_img_pages"),
            ("Image → Image (convert format)", "image_to_image"),
        ]
        for i, (label, val) in enumerate(opts):
            ttk.Radiobutton(lf, text=label, variable=self.mode_var, value=val,
                            command=self._refresh_labels).grid(row=i//2, column=i%2, sticky="w", padx=12, pady=6)

        self._build_paths_box(f, include_recent=True)
        self._build_common_settings_box(f)

    def _build_pdf_tab(self):
        f = self.tab_pdf
        lf = ttk.LabelFrame(f, text="PDF Tools")
        lf.pack(fill="x", padx=12, pady=12)

        opts = [
            ("Merge PDFs → one", "merge_pdfs"),
            ("Split PDF (each page / ranges)", "split_pdf"),
            ("Rotate PDF", "rotate_pdf"),
            ("Compress PDF (clean/deflate OR rebuild)", "compress_pdf"),
        ]
        for i, (label, val) in enumerate(opts):
            ttk.Radiobutton(lf, text=label, variable=self.mode_var, value=val,
                            command=self._refresh_labels).grid(row=i, column=0, sticky="w", padx=12, pady=6)

        self._build_paths_box(f, include_recent=False)

        tools = ttk.LabelFrame(f, text="Tool Options")
        tools.pack(fill="x", padx=12, pady=12)

        ttk.Label(tools, text="Rotate degrees:").grid(row=0, column=0, sticky="w", padx=12, pady=8)
        ttk.Combobox(tools, textvariable=self.rotate_deg_var, values=[90, 180, 270], state="readonly", width=6)\
            .grid(row=0, column=1, sticky="w")

        ttk.Label(tools, text="Split mode:").grid(row=1, column=0, sticky="w", padx=12, pady=8)
        ttk.Combobox(tools, textvariable=self.split_mode_var, values=["each", "ranges"], state="readonly", width=10)\
            .grid(row=1, column=1, sticky="w")
        ttk.Label(tools, text="Ranges (when mode=ranges):").grid(row=1, column=2, sticky="w", padx=(20, 8))
        ttk.Entry(tools, textvariable=self.split_ranges_var, width=30).grid(row=1, column=3, sticky="w")

        ttk.Label(tools, text="Compress mode:").grid(row=2, column=0, sticky="w", padx=12, pady=8)
        ttk.Combobox(tools, textvariable=self.compress_mode_var, values=["clean", "rebuild"], state="readonly", width=10)\
            .grid(row=2, column=1, sticky="w")
        ttk.Label(tools, text="Rebuild DPI:").grid(row=2, column=2, sticky="w", padx=(20, 8))
        ttk.Entry(tools, textvariable=self.compress_dpi_var, width=8).grid(row=2, column=3, sticky="w")

        ttk.Label(tools, text="Page range (rotate):").grid(row=3, column=0, sticky="w", padx=12, pady=(0, 10))
        ttk.Entry(tools, textvariable=self.page_range_var, width=25).grid(row=3, column=1, sticky="w", pady=(0, 10))

        mlf = ttk.LabelFrame(f, text="Merge List (for Merge PDFs)")
        mlf.pack(fill="x", padx=12, pady=12)

        btns = ttk.Frame(mlf)
        btns.pack(fill="x", padx=8, pady=8)
        ttk.Button(btns, text="Add PDFs...", command=self._merge_add).pack(side="left")
        ttk.Button(btns, text="Clear", command=self._merge_clear).pack(side="left", padx=(10,0))

        self.merge_box = tk.Listbox(mlf, height=6)
        self.merge_box.pack(fill="x", padx=8, pady=(0, 8))

    def _build_img_tab(self):
        f = self.tab_img
        lf = ttk.LabelFrame(f, text="Image Tools")
        lf.pack(fill="x", padx=12, pady=12)

        opts = [
            ("Batch Image Convert (folder)", "batch_image_convert"),
            ("Batch Resize/Compress Images (folder)", "batch_image_resize"),
            ("Images → PDF (one PDF per subfolder)", "images_to_pdf_per_subfolder"),
        ]
        for i, (label, val) in enumerate(opts):
            ttk.Radiobutton(lf, text=label, variable=self.mode_var, value=val,
                            command=self._refresh_labels).grid(row=i, column=0, sticky="w", padx=12, pady=6)

        self._build_paths_box(f, include_recent=False)

        tools = ttk.LabelFrame(f, text="Image Options")
        tools.pack(fill="x", padx=12, pady=12)

        ttk.Label(tools, text="Output format:").grid(row=0, column=0, sticky="w", padx=12, pady=8)
        ttk.Combobox(tools, textvariable=self.batch_img_fmt_var, values=OUT_IMAGE_FORMATS, state="readonly", width=8)\
            .grid(row=0, column=1, sticky="w")

        ttk.Label(tools, text="Resize max dimension:").grid(row=1, column=0, sticky="w", padx=12, pady=8)
        ttk.Entry(tools, textvariable=self.resize_max_var, width=10).grid(row=1, column=1, sticky="w")

        ttk.Label(tools, text="Quality (JPG/WEBP):").grid(row=1, column=2, sticky="w", padx=(20, 8))
        ttk.Entry(tools, textvariable=self.resize_quality_var, width=10).grid(row=1, column=3, sticky="w")

        ttk.Checkbutton(tools, text="Recursive folder search", variable=self.recursive_var)\
            .grid(row=2, column=0, sticky="w", padx=12, pady=(0, 10))

    def _build_batch_tab(self):
        f = self.tab_batch
        lf = ttk.LabelFrame(f, text="Batch (Word)")
        lf.pack(fill="x", padx=12, pady=12)

        ttk.Radiobutton(lf, text="Batch Word folder → PDFs", variable=self.mode_var, value="batch_word_pdf",
                        command=self._refresh_labels).grid(row=0, column=0, sticky="w", padx=12, pady=6)
        ttk.Radiobutton(lf, text="Batch Word folder → Images (subfolder per docx)", variable=self.mode_var, value="batch_word_images",
                        command=self._refresh_labels).grid(row=1, column=0, sticky="w", padx=12, pady=6)

        self._build_paths_box(f, include_recent=False)
        self._build_common_settings_box(f)

    def _build_settings_tab(self):
        f = self.tab_settings

        lf = ttk.LabelFrame(f, text="Presets")
        lf.pack(fill="x", padx=12, pady=12)

        ttk.Label(lf, text="Preset:").grid(row=0, column=0, sticky="w", padx=12, pady=10)
        cb = ttk.Combobox(lf, textvariable=self.preset_var, values=list(PRESETS.keys()), state="readonly", width=32)
        cb.grid(row=0, column=1, sticky="w", pady=10)
        cb.bind("<<ComboboxSelected>>", lambda e: self._apply_preset(self.preset_var.get()))

        pro = ttk.LabelFrame(f, text="PRO Settings")
        pro.pack(fill="x", padx=12, pady=12)

        ttk.Checkbutton(
            pro, text="Remember last input/output paths (turn OFF to disable last_in_path)",
            variable=self.remember_paths_var,
            command=self._persist_settings
        ).grid(row=0, column=0, sticky="w", padx=12, pady=6)

        ttk.Checkbutton(
            pro, text="Open output automatically after Done",
            variable=self.open_output_after_run_var,
            command=self._persist_settings
        ).grid(row=1, column=0, sticky="w", padx=12, pady=6)

        ttk.Checkbutton(
            pro, text="Confirm before overwriting existing output",
            variable=self.confirm_overwrite_var,
            command=self._persist_settings
        ).grid(row=2, column=0, sticky="w", padx=12, pady=6)

        ttk.Button(
            pro, text="Open settings.json folder",
            command=lambda: open_in_explorer(app_dir())
        ).grid(row=3, column=0, sticky="w", padx=12, pady=(8, 10))

        dnd = "Enabled" if HAS_DND else "Not installed (optional: pip install tkinterdnd2)"
        ttk.Label(pro, text=f"Drag & Drop: {dnd}").grid(row=4, column=0, sticky="w", padx=12, pady=(0, 10))

    def _build_paths_box(self, parent, include_recent: bool):
        lf = ttk.LabelFrame(parent, text="Paths")
        lf.pack(fill="x", padx=12, pady=12)

        row0 = 0

        if include_recent:
            ttk.Label(lf, text="Recent inputs:").grid(row=row0, column=0, sticky="w", padx=12, pady=(10, 0))
            self.recent_cb = ttk.Combobox(lf, values=[], state="readonly", width=90)
            self.recent_cb.grid(row=row0, column=1, padx=8, pady=(10, 0), sticky="w")
            self.recent_cb.bind("<<ComboboxSelected>>", lambda e: self._choose_recent_input())
            ttk.Button(lf, text="Clear Recents", command=self._clear_recent_inputs)\
                .grid(row=row0, column=2, padx=8, pady=(10, 0))
            row0 += 1

        lbl_in = ttk.Label(lf, text="Input:")
        lbl_in.grid(row=row0, column=0, sticky="w", padx=12, pady=8)
        ttk.Entry(lf, textvariable=self.in_path, width=100).grid(row=row0, column=1, padx=8, pady=8, sticky="w")
        ttk.Button(lf, text="Browse…", command=self._browse_input).grid(row=row0, column=2, padx=8, pady=8)

        lbl_out = ttk.Label(lf, text="Output:")
        lbl_out.grid(row=row0 + 1, column=0, sticky="w", padx=12, pady=8)
        ttk.Entry(lf, textvariable=self.out_path, width=100).grid(row=row0 + 1, column=1, padx=8, pady=8, sticky="w")
        ttk.Button(lf, text="Browse…", command=self._browse_output).grid(row=row0 + 1, column=2, padx=8, pady=8)

        self._path_widgets.append({"lbl_in": lbl_in, "lbl_out": lbl_out})

    def _build_log_tab(self, parent):
        log_frame = ttk.LabelFrame(parent, text="Log")
        log_frame.pack(fill="both", expand=True, padx=12, pady=12)

        self.log = tk.Text(log_frame, height=10, wrap="word")
        self.log.pack(fill="both", expand=True, padx=8, pady=8)
        self.log.configure(state="disabled")

    def _build_common_settings_box(self, parent):
        lf = ttk.LabelFrame(parent, text="Common Settings")
        lf.pack(fill="x", padx=12, pady=12)

        ttk.Label(lf, text="DPI:").grid(row=0, column=0, sticky="w", padx=12, pady=8)
        ttk.Entry(lf, textvariable=self.dpi_var, width=8).grid(row=0, column=1, sticky="w")

        ttk.Label(lf, text="Format (png/jpg):").grid(row=0, column=2, sticky="w", padx=(20, 8))
        ttk.Combobox(lf, textvariable=self.fmt_var, values=["png", "jpg"], state="readonly", width=6)\
            .grid(row=0, column=3, sticky="w")

        ttk.Label(lf, text="JPG Quality:").grid(row=0, column=4, sticky="w", padx=(20, 8))
        ttk.Scale(lf, from_=50, to=95, orient="horizontal", variable=self.jpg_quality_var)\
            .grid(row=0, column=5, sticky="we", padx=(0, 12))
        lf.columnconfigure(5, weight=1)

        ttk.Label(lf, text="Page range (all / 1-3,7,10-):").grid(row=1, column=0, sticky="w", padx=12, pady=(0,10))
        ttk.Entry(lf, textvariable=self.page_range_var, width=25).grid(row=1, column=1, sticky="w", pady=(0,10))

        ttk.Checkbutton(lf, text="Recursive (folder scanning)", variable=self.recursive_var)\
            .grid(row=1, column=2, sticky="w", padx=(20,0), pady=(0,10))

        ttk.Label(lf, text="Sort (images → pdf):").grid(row=1, column=3, sticky="w", padx=(20,8), pady=(0,10))
        ttk.Combobox(lf, textvariable=self.sort_mode_var, values=["natural", "name", "mtime"], state="readonly", width=10)\
            .grid(row=1, column=4, sticky="w", pady=(0,10))

    # -------- DnD --------
    def _enable_dnd(self):
        def on_drop(event):
            paths = self._parse_dnd_files(event.data)
            if not paths:
                return
            p = Path(paths[0])
            self.in_path.set(str(p))
            self._add_recent_input(p)

            if p.is_dir():
                self.mode_var.set("images_to_pdf")
            else:
                ext = p.suffix.lower()
                if ext in DOCX_EXTS:
                    self.mode_var.set("word_to_images")
                elif ext in PDF_EXTS:
                    self.mode_var.set("pdf_to_images")
                elif ext in IMAGE_EXTS:
                    self.mode_var.set("image_to_image")

            self._refresh_labels()
            self._log(f"[{log_time()}] Dropped: {p}")

        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", on_drop)

    def _parse_dnd_files(self, data: str):
        parts = []
        buf = ""
        in_brace = False
        for ch in data:
            if ch == "{":
                in_brace = True
                buf = ""
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

    # -------- Recent inputs --------
    def _refresh_recent_inputs_ui(self):
        if hasattr(self, "recent_cb"):
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
            self._refresh_labels()

    def _clear_recent_inputs(self):
        self.recent_inputs = []
        self._refresh_recent_inputs_ui()
        self._persist_settings()

    # -------- Presets / persistence --------
    def _apply_preset(self, name: str):
        p = PRESETS.get(name)
        if not p:
            return
        self.dpi_var.set(str(p["dpi"]))
        self.fmt_var.set(p["fmt"])
        self.jpg_quality_var.set(int(p["jpg_quality"]))
        self._log(f"[{log_time()}] Preset applied: {name}")
        self._persist_settings()

    def _persist_settings(self):
        remember_paths = bool(self.remember_paths_var.get())

        data = dict(
            remember_paths=remember_paths,
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
        )

        if remember_paths:
            data["last_in_path"] = self.in_path.get()
            data["last_out_path"] = self.out_path.get()
        else:
            data["last_in_path"] = ""
            data["last_out_path"] = ""

        save_settings(data)

    def _apply_loaded_settings(self):
        s = self._settings or {}
        remember_paths = bool(s.get("remember_paths", True))

        # load paths depending on remember_paths
        if remember_paths:
            self.in_path.set(s.get("last_in_path", ""))
            self.out_path.set(s.get("last_out_path", ""))
        else:
            self.in_path.set("")
            self.out_path.set("")

    # -------- Merge list UI --------
    def _merge_add(self):
        files = filedialog.askopenfilenames(title="Select PDFs to merge", filetypes=[("PDF", "*.pdf")])
        for f in files:
            p = Path(f)
            if p.exists() and p.suffix.lower() == ".pdf":
                self.merge_list.append(p)
        self._merge_refresh()

    def _merge_clear(self):
        self.merge_list = []
        self._merge_refresh()

    def _merge_refresh(self):
        self.merge_box.delete(0, tk.END)
        for p in self.merge_list:
            self.merge_box.insert(tk.END, str(p))

    # -------- Labels / Browse --------
    def _refresh_labels(self):
        mode = self.mode_var.get()
        self.btn_open.config(state="disabled")

        # input label
        if mode in ("word_to_images", "word_to_pdf"):
            in_txt = "Input Word (.docx):"
        elif mode in ("images_to_pdf", "batch_image_convert", "batch_image_resize",
                      "images_to_pdf_per_subfolder", "image_to_image"):
            in_txt = "Input image file or folder:"
        elif mode in ("batch_word_pdf", "batch_word_images"):
            in_txt = "Input folder with .docx:"
        elif mode in ("merge_pdfs",):
            in_txt = "(Use Merge List tab tools)"
        else:
            in_txt = "Input PDF (.pdf):"

        # output label
        if mode in ("word_to_images", "pdf_to_images", "pdf_to_images_only_img_pages", "split_pdf",
                    "batch_image_convert", "batch_image_resize", "images_to_pdf_per_subfolder", "batch_word_images"):
            out_txt = "Output folder:"
        elif mode == "image_to_image":
            out_txt = "Output folder (if input is folder) OR output file (if input is file):"
        elif mode in ("images_to_pdf", "word_to_pdf", "merge_pdfs", "rotate_pdf", "compress_pdf", "batch_word_pdf"):
            out_txt = "Output PDF (.pdf):"
        elif mode in ("pdf_to_text",):
            out_txt = "Output TXT (.txt):"
        elif mode in ("pdf_to_long_image",):
            out_txt = "Output image file (.png/.jpg):"
        else:
            out_txt = "Output:"

        for w in self._path_widgets:
            w["lbl_in"].config(text=in_txt)
            w["lbl_out"].config(text=out_txt)

    def _browse_input(self):
        mode = self.mode_var.get()

        if mode in ("merge_pdfs",):
            messagebox.showinfo("Merge PDFs", "Use 'Add PDFs...' in the PDF Tools tab (Merge List).")
            return

        if mode in ("word_to_images", "word_to_pdf"):
            p = filedialog.askopenfilename(title="Select Word file", filetypes=[("Word", "*.docx")])

        elif mode in ("pdf_to_images", "pdf_to_images_only_img_pages", "pdf_to_long_image", "pdf_to_text",
                      "split_pdf", "rotate_pdf", "compress_pdf"):
            p = filedialog.askopenfilename(title="Select PDF file", filetypes=[("PDF", "*.pdf")])

        elif mode in ("batch_word_pdf", "batch_word_images", "batch_image_convert", "batch_image_resize", "images_to_pdf_per_subfolder"):
            p = filedialog.askdirectory(title="Select folder")

        elif mode == "image_to_image":
            choice = messagebox.askyesno("Image → Image", "Select a folder?\nYes = folder, No = single image file")
            if choice:
                p = filedialog.askdirectory(title="Select folder containing images")
            else:
                p = filedialog.askopenfilename(
                    title="Select image file",
                    filetypes=[("Images", "*.jpg;*.jpeg;*.png;*.webp;*.tif;*.tiff;*.bmp")]
                )
        else:
            choice = messagebox.askyesno("Images → PDF", "Select a folder?\nYes = folder, No = single image file")
            if choice:
                p = filedialog.askdirectory(title="Select folder containing images")
            else:
                p = filedialog.askopenfilename(
                    title="Select image file",
                    filetypes=[("Images", "*.jpg;*.jpeg;*.png;*.webp;*.tif;*.tiff;*.bmp")]
                )

        if p:
            self.in_path.set(p)
            try:
                self._add_recent_input(Path(p))
            except Exception:
                pass
            self._persist_settings()

    def _browse_output(self):
        mode = self.mode_var.get()

        if mode in ("word_to_images", "pdf_to_images", "pdf_to_images_only_img_pages",
                    "split_pdf", "batch_image_convert", "batch_image_resize",
                    "images_to_pdf_per_subfolder", "batch_word_images"):
            p = filedialog.askdirectory(title="Select output folder")

        elif mode in ("images_to_pdf", "word_to_pdf", "merge_pdfs", "rotate_pdf", "compress_pdf", "batch_word_pdf"):
            p = filedialog.asksaveasfilename(title="Save PDF as", defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])

        elif mode == "pdf_to_text":
            p = filedialog.asksaveasfilename(title="Save TXT as", defaultextension=".txt", filetypes=[("Text", "*.txt")])

        elif mode == "pdf_to_long_image":
            p = filedialog.asksaveasfilename(title="Save image as", defaultextension=".png",
                                             filetypes=[("PNG", "*.png"), ("JPG", "*.jpg")])

        elif mode == "image_to_image":
            in_txt = self.in_path.get().strip().strip('"')
            in_p = Path(in_txt) if in_txt else None
            if in_p and in_p.exists() and in_p.is_dir():
                p = filedialog.askdirectory(title="Select output folder")
            else:
                ext = "." + self.batch_img_fmt_var.get().lower()
                p = filedialog.asksaveasfilename(
                    title="Save image as",
                    defaultextension=ext,
                    filetypes=[("Image", "*" + ext)]
                )
        else:
            p = filedialog.askdirectory(title="Select output folder")

        if p:
            self.out_path.set(p)
            self._persist_settings()

    # -------- Run / Threading --------
    def _set_working(self, working: bool):
        self.btn_run.config(state="disabled" if working else "normal")
        self.btn_cancel.config(state="normal" if working else "disabled")
        if working:
            self.btn_open.config(state="disabled")

    def _cancel(self):
        self.cancel_event.set()
        self._log(f"[{log_time()}] Cancel requested...")

    def _open_output(self):
        out = self.out_path.get().strip().strip('"')
        if out:
            open_in_explorer(Path(out))

    def _log(self, msg: str):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _validate_common(self):
        mode = self.mode_var.get()

        in_txt = self.in_path.get().strip().strip('"')
        out_txt = self.out_path.get().strip().strip('"')

        if mode == "merge_pdfs":
            if not self.merge_list:
                raise RuntimeError("Merge list is empty. Add PDFs in the PDF Tools tab.")
        else:
            if not in_txt:
                raise RuntimeError("Choose an input path.")
            if not Path(in_txt).exists():
                raise RuntimeError("Input path does not exist.")

        if not out_txt and mode != "merge_pdfs":
            raise RuntimeError("Choose an output path.")

        dpi_needed = {"pdf_to_images", "pdf_to_images_only_img_pages", "pdf_to_long_image", "word_to_images", "batch_word_images"}
        if mode in dpi_needed:
            dpi = int(self.dpi_var.get())
            if not (72 <= dpi <= 600):
                raise RuntimeError("DPI must be between 72 and 600.")

            fmt = self.fmt_var.get().lower()
            if fmt not in ("png", "jpg"):
                raise RuntimeError("Format must be png or jpg.")

            jpgq = int(self.jpg_quality_var.get())
            if not (50 <= jpgq <= 95):
                raise RuntimeError("JPG quality must be 50..95.")

        if mode in ("batch_image_convert", "batch_image_resize", "image_to_image"):
            out_fmt = self.batch_img_fmt_var.get().lower()
            if out_fmt not in OUT_IMAGE_FORMATS:
                raise RuntimeError(f"Choose output format from: {', '.join(OUT_IMAGE_FORMATS)}")

        return mode

    def _confirm_overwrite_output(self, mode: str, out_p: Path) -> bool:
        if not self.confirm_overwrite_var.get():
            return True

        folder_modes = {
            "word_to_images", "pdf_to_images", "pdf_to_images_only_img_pages", "split_pdf",
            "batch_image_convert", "batch_image_resize", "images_to_pdf_per_subfolder", "batch_word_images"
        }

        # folder output
        if mode in folder_modes:
            if out_p.exists() and out_p.is_dir():
                try:
                    has_any = any(out_p.iterdir())
                except Exception:
                    has_any = True
                if has_any:
                    return messagebox.askyesno(
                        "Overwrite?",
                        f"Output folder already contains files:\n{out_p}\n\nOverwrite (files may be replaced)?"
                    )
            return True

        # file output
        if out_p.exists() and out_p.is_file():
            return messagebox.askyesno("Overwrite?", f"Output file exists:\n{out_p}\n\nOverwrite it?")
        return True

    def _run(self):
        try:
            self.cancel_event.clear()
            self.progress["value"] = 0
            self.progress["maximum"] = 100
            self.lbl_status.config(text="Working...")
            self._set_working(True)
            self._persist_settings()

            mode = self._validate_common()

            # overwrite check (UI thread)
            if mode != "merge_pdfs":
                out_txt = self.out_path.get().strip().strip('"')
                if out_txt:
                    if not self._confirm_overwrite_output(mode, Path(out_txt)):
                        self._set_working(False)
                        self.lbl_status.config(text="Cancelled")
                        return

            def worker():
                try:
                    def progress_cb(done, total):
                        self.ui_queue.put(("progress", done, total))

                    def log_cb(m):
                        self.ui_queue.put(("log", f"[{log_time()}] {m}"))

                    in_p = Path(self.in_path.get().strip().strip('"')) if mode != "merge_pdfs" else None
                    out_p = Path(self.out_path.get().strip().strip('"')) if self.out_path.get().strip() else None

                    dpi = int(self.dpi_var.get()) if self.dpi_var.get().strip() else 300
                    fmt = self.fmt_var.get().lower()
                    jpgq = int(self.jpg_quality_var.get())
                    pr = self.page_range_var.get().strip() or "all"
                    recursive = bool(self.recursive_var.get())
                    sort_mode = self.sort_mode_var.get()

                    if mode == "word_to_images":
                        if in_p.suffix.lower() != ".docx":
                            raise RuntimeError("Input must be .docx")
                        if not out_p or out_p.suffix.lower() == ".pdf":
                            raise RuntimeError("Output must be a folder for Word → Images.")
                        word_to_images(in_p, out_p, dpi, fmt, jpgq, page_range=pr,
                                       progress_cb=progress_cb, cancel_event=self.cancel_event, log_cb=log_cb)

                    elif mode == "images_to_pdf":
                        if not out_p or out_p.suffix.lower() != ".pdf":
                            raise RuntimeError("Output must be a .pdf file.")
                        images_to_pdf(in_p, out_p, recursive=recursive, sort_mode=sort_mode,
                                      progress_cb=progress_cb, cancel_event=self.cancel_event, log_cb=log_cb)

                    elif mode == "pdf_to_images":
                        if in_p.suffix.lower() != ".pdf":
                            raise RuntimeError("Input must be .pdf")
                        if not out_p or out_p.suffix.lower() == ".pdf":
                            raise RuntimeError("Output must be a folder for PDF → Images.")
                        pdf_to_images(in_p, out_p, dpi, fmt, jpgq, page_range=pr,
                                      only_pages_with_images=False,
                                      progress_cb=progress_cb, cancel_event=self.cancel_event, log_cb=log_cb)

                    elif mode == "pdf_to_images_only_img_pages":
                        if in_p.suffix.lower() != ".pdf":
                            raise RuntimeError("Input must be .pdf")
                        if not out_p or out_p.suffix.lower() == ".pdf":
                            raise RuntimeError("Output must be a folder.")
                        pdf_to_images(in_p, out_p, dpi, fmt, jpgq, page_range=pr,
                                      only_pages_with_images=True,
                                      progress_cb=progress_cb, cancel_event=self.cancel_event, log_cb=log_cb)

                    elif mode == "word_to_pdf":
                        if in_p.suffix.lower() != ".docx":
                            raise RuntimeError("Input must be .docx")
                        if not out_p or out_p.suffix.lower() != ".pdf":
                            raise RuntimeError("Output must be a .pdf file.")
                        word_to_pdf(in_p, out_p, log_cb=log_cb)
                        progress_cb(1, 1)

                    elif mode == "pdf_to_long_image":
                        if in_p.suffix.lower() != ".pdf":
                            raise RuntimeError("Input must be .pdf")
                        if not out_p:
                            raise RuntimeError("Choose output image.")
                        out_fmt = out_p.suffix.lower().lstrip(".")
                        if out_fmt not in ("png", "jpg", "jpeg"):
                            raise RuntimeError("Output image must be .png or .jpg")
                        pdf_to_long_image(in_p, out_p, dpi, "jpg" if out_fmt in ("jpg","jpeg") else "png", jpgq,
                                          page_range=pr, progress_cb=progress_cb, cancel_event=self.cancel_event, log_cb=log_cb)

                    elif mode == "pdf_to_text":
                        if in_p.suffix.lower() != ".pdf":
                            raise RuntimeError("Input must be .pdf")
                        if not out_p or out_p.suffix.lower() != ".txt":
                            raise RuntimeError("Output must be .txt")
                        pdf_to_text(in_p, out_p, page_range=pr, progress_cb=progress_cb,
                                    cancel_event=self.cancel_event, log_cb=log_cb)

                    elif mode == "merge_pdfs":
                        if not out_p or out_p.suffix.lower() != ".pdf":
                            raise RuntimeError("Output must be a .pdf file.")
                        merge_pdfs(self.merge_list, out_p, progress_cb=progress_cb,
                                   cancel_event=self.cancel_event, log_cb=log_cb)

                    elif mode == "split_pdf":
                        if in_p.suffix.lower() != ".pdf":
                            raise RuntimeError("Input must be .pdf")
                        if not out_p or out_p.suffix.lower() == ".pdf":
                            raise RuntimeError("Output must be a folder.")
                        split_pdf(in_p, out_p, mode=self.split_mode_var.get(), ranges=self.split_ranges_var.get(),
                                  progress_cb=progress_cb, cancel_event=self.cancel_event, log_cb=log_cb)

                    elif mode == "rotate_pdf":
                        if in_p.suffix.lower() != ".pdf":
                            raise RuntimeError("Input must be .pdf")
                        if not out_p or out_p.suffix.lower() != ".pdf":
                            raise RuntimeError("Output must be .pdf")
                        rotate_pdf(in_p, out_p, int(self.rotate_deg_var.get()), page_range=pr,
                                   progress_cb=progress_cb, cancel_event=self.cancel_event, log_cb=log_cb)

                    elif mode == "compress_pdf":
                        if in_p.suffix.lower() != ".pdf":
                            raise RuntimeError("Input must be .pdf")
                        if not out_p or out_p.suffix.lower() != ".pdf":
                            raise RuntimeError("Output must be .pdf")
                        cm = self.compress_mode_var.get()
                        if cm == "clean":
                            compress_pdf_clean(in_p, out_p, log_cb=log_cb)
                            progress_cb(1, 1)
                        else:
                            rebuild_dpi = int(self.compress_dpi_var.get())
                            compress_pdf_rebuild(in_p, out_p, rebuild_dpi, progress_cb=progress_cb,
                                                 cancel_event=self.cancel_event, log_cb=log_cb)

                    elif mode == "batch_image_convert":
                        if not in_p.is_dir():
                            raise RuntimeError("Input must be a folder.")
                        if not out_p or out_p.suffix.lower() == ".pdf":
                            raise RuntimeError("Output must be a folder.")
                        batch_image_convert(in_p, out_p, self.batch_img_fmt_var.get(),
                                            recursive=recursive, progress_cb=progress_cb,
                                            cancel_event=self.cancel_event, log_cb=log_cb)

                    elif mode == "batch_image_resize":
                        if not in_p.is_dir():
                            raise RuntimeError("Input must be a folder.")
                        if not out_p or out_p.suffix.lower() == ".pdf":
                            raise RuntimeError("Output must be a folder.")
                        max_dim = int(self.resize_max_var.get())
                        q = int(self.resize_quality_var.get())
                        batch_image_resize(in_p, out_p, self.batch_img_fmt_var.get(), max_dim, q,
                                           recursive=recursive, progress_cb=progress_cb,
                                           cancel_event=self.cancel_event, log_cb=log_cb)

                    elif mode == "images_to_pdf_per_subfolder":
                        if not in_p.is_dir():
                            raise RuntimeError("Input must be a folder.")
                        if not out_p or out_p.suffix.lower() == ".pdf":
                            raise RuntimeError("Output must be a folder.")
                        images_to_pdf_per_subfolder(in_p, out_p, recursive=recursive, sort_mode=sort_mode,
                                                    progress_cb=progress_cb, cancel_event=self.cancel_event, log_cb=log_cb)

                    elif mode == "image_to_image":
                        out_fmt = self.batch_img_fmt_var.get().lower()
                        q = int(self.resize_quality_var.get())
                        max_dim = int(self.resize_max_var.get()) if self.resize_max_var.get().strip() else 0
                        max_dim = max_dim if max_dim > 0 else None

                        if in_p.is_dir():
                            if not out_p or out_p.suffix.lower() == ".pdf":
                                raise RuntimeError("Output must be a folder when input is a folder.")
                        else:
                            if not out_p:
                                raise RuntimeError("Choose output file.")
                            if out_p.suffix.lower().lstrip(".") != out_fmt:
                                out_p = out_p.with_suffix("." + out_fmt)

                        image_to_image(in_p, out_p, out_fmt,
                                       recursive=recursive, max_size=max_dim, quality=q,
                                       progress_cb=progress_cb, cancel_event=self.cancel_event, log_cb=log_cb)

                    elif mode == "batch_word_pdf":
                        if not in_p.is_dir():
                            raise RuntimeError("Input must be a folder.")
                        if not out_p or out_p.suffix.lower() == ".pdf":
                            raise RuntimeError("Output must be a folder.")
                        batch_word_convert(in_p, out_p, "pdf", dpi, fmt, jpgq,
                                           progress_cb=progress_cb, cancel_event=self.cancel_event, log_cb=log_cb)

                    elif mode == "batch_word_images":
                        if not in_p.is_dir():
                            raise RuntimeError("Input must be a folder.")
                        if not out_p or out_p.suffix.lower() == ".pdf":
                            raise RuntimeError("Output must be a folder.")
                        batch_word_convert(in_p, out_p, "images", dpi, fmt, jpgq,
                                           progress_cb=progress_cb, cancel_event=self.cancel_event, log_cb=log_cb)

                    else:
                        raise RuntimeError(f"Unknown mode: {mode}")

                    self.ui_queue.put(("done", str(out_p) if out_p else ""))

                except Exception as e:
                    self.ui_queue.put(("error", str(e)))

            self.worker_thread = threading.Thread(target=worker, daemon=True)
            self.worker_thread.start()

        except Exception as e:
            self._set_working(False)
            self.lbl_status.config(text="Error ❌")
            messagebox.showerror("Error", str(e))

    def _poll_queue(self):
        try:
            while True:
                msg = self.ui_queue.get_nowait()
                if msg[0] == "log":
                    self._log(msg[1])
                elif msg[0] == "progress":
                    done, total = msg[1], msg[2]
                    total = max(1, total)
                    pct = int((done / total) * 100)
                    self.progress["value"] = pct
                    self.lbl_status.config(text=f"Working... ({done}/{total})")
                elif msg[0] == "done":
                    self._set_working(False)
                    self.progress["value"] = 100
                    self.lbl_status.config(text="Done ✅")
                    self.btn_open.config(state="normal")
                    if self.open_output_after_run_var.get():
                        try:
                            self._open_output()
                        except Exception:
                            pass
                    messagebox.showinfo("Success", "Completed successfully!")
                elif msg[0] == "error":
                    self._set_working(False)
                    self.lbl_status.config(text="Error ❌")
                    messagebox.showerror("Error", msg[1])
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)

if __name__ == "__main__":
    App().mainloop()