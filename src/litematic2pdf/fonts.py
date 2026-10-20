"""TTF registration: main UI font and decorative signature font."""
import glob
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def register_font():
    candidates = (
        ("Arial", "C:/Windows/Fonts/arial.ttf"),
        ("SegoeUI", "C:/Windows/Fonts/segoeui.ttf"),
        ("Calibri", "C:/Windows/Fonts/calibri.ttf"),
        ("Verdana", "C:/Windows/Fonts/verdana.ttf"),
        ("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ("Arial", "/Library/Fonts/Arial.ttf"),
        ("Arial", "/System/Library/Fonts/Supplemental/Arial.ttf"),
    )
    extra = [p for pat in (
        "/usr/share/fonts/**/DejaVuSans.ttf",
        "/usr/share/fonts/**/*.ttf",
        str(Path.home() / ".fonts" / "**" / "*.ttf"),
    ) for p in glob.glob(pat, recursive=True)]
    for path in [c[1] for c in candidates] + sorted(extra)[:5]:
        name = Path(path).stem or "Font"
        if not Path(path).exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            return name
        except Exception:
            continue
    return "Helvetica"


def register_script_font():
    """Register a cursive font for the signature watermark as 'Signature'.

    Returns the registered name, or None when nothing suitable is installed
    (caller falls back to the main font)."""
    candidates = (
        "C:/Windows/Fonts/segoesc.ttf",   # Segoe Script
        "C:/Windows/Fonts/segoescb.ttf",
        "C:/Windows/Fonts/BRUSHSCI.TTF",  # Brush Script MT
        "C:/Windows/Fonts/LHANDW.TTF",    # Lucida Handwriting
        "C:/Windows/Fonts/Inkfree.ttf",   # Ink Free
        "/usr/share/fonts/**/*[Ss]cript*.ttf",
        str(Path.home() / ".fonts" / "**" / "*[Ss]cript*.ttf"),
    )
    paths = list(candidates[:5])
    for pat in candidates[5:]:
        paths += glob.glob(pat, recursive=True)
    for path in paths:
        if not Path(path).exists():
            continue
        try:
            pdfmetrics.registerFont(TTFont("Signature", path))
            return "Signature"
        except Exception:
            continue
    return None
