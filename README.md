# Rilleras Converter

A Windows desktop app for converting between **PDF, Word and image** formats — plus the
everyday PDF chores (merge, split, rotate, compress) and bulk image work.

Built with Python + Tkinter. No cloud, no uploads: everything runs on your machine.

---

## Install

### To use the app — run the installer

Double-click **`RillerasConverterSetup.exe`**. That's it.

No Python, no packages, no scripts. It installs per-user so Windows never asks for admin
rights, adds a Start Menu entry and an optional Desktop shortcut, and registers a normal
entry in *Add or remove programs*.

Build it yourself with [`build.bat`](#build-the-installer), or grab it from the project's
releases.

> Windows SmartScreen will warn you the first time, because the installer is not
> code-signed. Click **More info → Run anyway**. Removing that warning requires buying a
> signing certificate.

There is also a **portable** build — `dist\RillerasConverter.exe` — a single self-contained
file you can copy onto a USB stick and run with no installation at all. It starts more
slowly (it unpacks itself on each launch), so prefer the installer for a machine you use
regularly.

### To work on the code — run setup.bat

Double-click **`setup.bat`**. It will:

1. Find Python — and install it automatically via `winget` if the PC doesn't have it.
2. Create an isolated virtual environment in `.venv`.
3. Install every required package.
4. Create Desktop and Start Menu shortcuts, plus a `Rilleras Converter.bat` launcher.

If you skip setup and just run `python RillerasConverter.py`, the app notices any missing
packages on startup and installs them itself in a small progress window. Either way you
should never have to install packages by hand.

> Requires an internet connection the first time, and Windows 10/11.

## Run

Use the Start Menu entry, the Desktop shortcut, or from source:

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
| Images → Word (`.docx`) | One picture per page, scaled to fit the margins |
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

### Language

The interface ships in **English and Turkish** (*İngilizce ve Türkçe*). Pick one under
**Settings → Language**; the window relabels itself immediately and remembers the choice.
Error messages and the activity log are translated too, not just the buttons.

To add a language, add a code to `LANGUAGES` and a table to `TRANSLATIONS` in
`rilleras/i18n.py`. The test suite fails if a language is missing any key.

### Two things worth knowing

- **Word conversions need Microsoft Word.** They automate a real Word install through
  COM. The app checks up front and says so plainly instead of failing cryptically.
- **PDF → Word on a scanned PDF** produces page images, not editable text. A scan has no
  text layer to recover; that is a property of the file, not a bug. The app warns you
  when it detects this.

---

## Build the installer

```bash
build.bat
```

One command, a few minutes, two outputs:

| Output | What it is |
|---|---|
| `installer\Output\RillerasConverterSetup.exe` | The installer — this is what you give people |
| `dist\RillerasConverter.exe` | Portable single file, no installation |

Both bundle Python and every dependency, so they run on a PC with nothing installed.

Building the installer needs [Inno Setup](https://jrsoftware.org/isdl.php)
(`winget install JRSoftware.InnoSetup`). Without it `build.bat` still produces the portable
exe and tells you what's missing.

### Why two PyInstaller specs

`RillerasConverter-onedir.spec` builds a folder — exe plus libraries side by side — and Inno
Setup packs that folder into the installer. Nothing is unpacked at startup, so an installed
copy opens in about a second.

`RillerasConverter.spec` builds the portable single file. Convenient to copy around, but the
bootloader has to expand ~100 MB into `%TEMP%` on every launch, which is why it is slower.

Both specs share their bundling rules through `build_common.py` so they cannot drift apart.

Installed builds keep `settings.json` in `%APPDATA%\RillerasConverter`, since an all-users
install lands in Program Files where a normal user cannot write. Running from source keeps
it in the repo folder.

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
  i18n.py                English/Turkish string tables
  modes.py               declarative table of every conversion
  settings.py            settings.json persistence
  theme.py               dark theme + custom widgets
  app.py                 the window
tests/                   engine tests + i18n tests + UI smoke tests
setup.bat                one-click install
build.bat                exe + installer build
installer/               Inno Setup script
tools/make_icon.py       regenerates convert.ico
```

The app icon is generated, not hand-drawn — run `python tools/make_icon.py` after editing
it. It writes all seven sizes into `convert.ico`, using simplified artwork below 32px so
the mark stays legible on the taskbar.

## Author

ErdoganAlper
