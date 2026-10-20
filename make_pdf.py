#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Создать PDF из .litematic:  python make_pdf.py схема.litematic [-o out.pdf]

Вся логика — в пакете src/litematic2pdf/, этот файл только запускает CLI."""
import sys
from pathlib import Path

_src = Path(__file__).resolve().parent / "src"
if _src.is_dir():
    sys.path.insert(0, str(_src))

try:
    from litematic2pdf.cli import main
except ImportError:
    sys.exit("Рядом с этим файлом нет папки src — копируй проект целиком "
             "или используй собранный .exe")

if __name__ == "__main__":
    sys.exit(main())
