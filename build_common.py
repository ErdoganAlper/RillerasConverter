"""Shared PyInstaller inputs for both build specs.

Build-time only — the app never imports this. It exists so the one-file and
one-folder specs cannot drift apart in what they bundle.
"""

from PyInstaller.utils.hooks import collect_all

HIDDEN_IMPORTS = [
    'rilleras',
    'rilleras.app',
    'rilleras.core',
    'rilleras.i18n',
    'rilleras.modes',
    'rilleras.settings',
    'rilleras.theme',
]

# Packages whose data files / native libs static analysis alone misses.
COLLECT_PACKAGES = ('pdf2docx', 'docx', 'docx2pdf', 'tkinterdnd2', 'img2pdf')


def analysis_inputs():
    """Return (datas, binaries, hiddenimports) for Analysis()."""
    datas = [('convert.ico', '.')]
    binaries = []
    hiddenimports = list(HIDDEN_IMPORTS)

    for pkg in COLLECT_PACKAGES:
        try:
            pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
            datas += pkg_datas
            binaries += pkg_binaries
            hiddenimports += pkg_hidden
        except Exception:
            pass  # optional package not installed in this environment

    return datas, binaries, hiddenimports
