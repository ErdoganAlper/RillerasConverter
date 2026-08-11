# Rilleras Converter

A Windows desktop app for converting between **PDF, Word and image** formats — plus the
everyday PDF chores (merge, split, rotate, compress) and bulk image work.

Built with Python + Tkinter. No cloud, no uploads: everything runs on your machine.

---

## Install

Double-click **`setup.bat`**. That is the whole procedure.

It will:

1. Find Python — and install it automatically via `winget` if the PC doesn't have it.
2. Create an isolated virtual environment in `.venv`.
3. Install every required package.
4. Create Desktop and Start Menu shortcuts, plus a `Rilleras Converter.bat` launcher.

If you skip setup and just run `python RillerasConverter.py`, the app notices any missing
packages on startup and installs them itself in a small progress window. Either way you
should never have to install packages by hand.

> Requires an internet connection the first time, and Windows 10/11.

## Run

Use the Desktop shortcut, the Start Menu entry, or:

```bash
python RillerasConverter.py
```

---

## What it does

**Convert**

| Conversion | Notes |
|---|---|
| PDF → Word (`.docx`) | Rebuilds paragraphs, tables and images — not just raw text |
| Word → PDF | Requires Microsoft Word installed |
| PDF → Images | One image per page, any DPI |
| Images → PDF | Lossless, naturally sorted (`page2` before `page10`) |
| Word → Images | Via Word, then rendered per page |
| PDF → Text | Plain `.txt` from the text layer |
| PDF → Long Image | All pages stitched into one tall image |
| PDF → Images (image pages) | Skips pages containing no pictures |
| Image → Image | 13 output formats, optional resize |

**PDF Tools** — merge, split (per page or by ranges), rotate, compress (lossless clean-up
or re-render at a lower DPI).

**Image Tools** — batch convert a folder, batch resize/compress, one PDF per subfolder.

**Batch Word** — process a whole folder of `.docx` files into PDFs or image sets.

Everything runs on a background thread with live progress, a cancel button and an
activity log, so the window never freezes mid-job.

### Two things worth knowing

- **Word conversions need Microsoft Word.** They automate a real Word install through
  COM. The app checks up front and says so plainly instead of failing cryptically.
- **PDF → Word on a scanned PDF** produces page images, not editable text. A scan has no
  text layer to recover; that is a property of the file, not a bug. The app warns you
  when it detects this.

---

## Build a standalone `.exe`

```bash
build.bat
```

Produces `dist\RillerasConverter.exe` — a single file with Python and every dependency
bundled, so it runs on a PC with no Python at all.

If [Inno Setup](https://jrsoftware.org/isdl.php) is installed, `build.bat` also produces
`installer\Output\RillerasConverterSetup.exe`: a proper Windows installer with Start Menu
and Desktop entries and an uninstaller.

---

## Development

```bash
.venv\Scripts\python.exe -m pytest tests -q
```

The conversion engine has no Tk dependency, so it is tested headlessly. A separate smoke
test builds the real window and walks every screen and mode.

```
RillerasConverter.py     launcher + automatic dependency install
rilleras/
  core.py                conversion engine — pure functions, no UI
  modes.py               declarative table of every conversion
  settings.py            settings.json persistence
  theme.py               dark theme + custom widgets
  app.py                 the window
tests/                   engine tests + UI smoke tests
setup.bat                one-click install
build.bat                exe + installer build
installer/               Inno Setup script
```

## Author

ErdoganAlper
