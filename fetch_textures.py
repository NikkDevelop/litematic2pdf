#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Launcher: python fetch_textures.py (код в src/litematic2pdf/fetch.py)."""
import sys
from pathlib import Path

_src = Path(__file__).resolve().parent / "src"
if _src.is_dir():
    sys.path = [p for p in sys.path
                if p and Path(p).resolve() != _src.parent]
    sys.path.insert(0, str(_src))

try:
    from litematic2pdf.fetch import main  # noqa: E402
except ImportError:
    sys.exit("Не найдена папка src рядом с этим файлом. Скопируй проект целиком "
             "или используй собранный .exe")

if __name__ == "__main__":
    sys.exit(main())
