#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Открыть GUI-панель:  python guide.py  (или двойным кликом)

Точка входа для PyInstaller; вся логика — в пакете src/litematic2pdf/gui.py."""
import sys
from pathlib import Path

_src = Path(__file__).resolve().parent / "src"
if _src.is_dir():
    sys.path.insert(0, str(_src))

try:
    from litematic2pdf.gui import main
except ImportError:
    sys.exit("Рядом с этим файлом нет папки src — копируй проект целиком "
             "или используй собранный .exe")

if __name__ == "__main__":
    sys.exit(main())
