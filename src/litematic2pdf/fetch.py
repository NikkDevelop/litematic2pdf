#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Download Minecraft vanilla block textures (16x16 PNG) from the community
mirror repo InventivetalentDev/minecraft-assets into textures/block/.

Note: vanilla textures belong to Mojang; this mirror is a widely used
community copy - for personal use only.
"""

import argparse
import json
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = "https://api.github.com/repos/InventivetalentDev/minecraft-assets"
RAW = "https://raw.githubusercontent.com/InventivetalentDev/minecraft-assets"
FALLBACK_VERSIONS = ["latest", "1.21.4", "1.21.1", "1.20.4", "1.19.4",
                     "1.16.5", "1.12.2", "1.8.9"]


def api_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "fetch-mc-textures"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def list_block_textures(version):
    """Try the git trees API; fall back to contents API pagination."""
    for v in version:
        try:
            data = api_json(f"{REPO}/git/trees/{v}?recursive=1")
            prefix = "assets/minecraft/textures/block/"
            names = [e["path"][len(prefix):] for e in data.get("tree", [])
                     if e.get("type") == "blob"
                     and e["path"].startswith(prefix)
                     and e["path"].endswith(".png")]
            if names:
                return v, names
        except Exception as exc:
            print(f"  {v}: {exc}")
        try:
            names = []
            page = 1
            while True:
                data = api_json(
                    f"{REPO}/contents/assets/minecraft/textures/block"
                    f"?ref={v}&per_page=1000&page={page}")
                if not isinstance(data, list) or not data:
                    break
                names += [e["name"] for e in data if e["name"].endswith(".png")]
                if len(data) < 1000:
                    break
                page += 1
            if names:
                return v, names
        except Exception as exc:
            print(f"  {v} (contents): {exc}")
    return None, []


def download_one(args):
    name, version, outdir = args
    url = f"{RAW}/{version}/assets/minecraft/textures/block/{name}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "fetch-mc-textures"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
        if not data.startswith(b"\x89PNG"):
            return False
        (outdir / name).write_bytes(data)
        return True
    except Exception:
        return False


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="litematic2pdf-fetch",
        description="Скачивание ванильных текстур блоков для litematic2pdf.")
    ap.add_argument("--version", default=None,
                    help="версия игры (по умолчанию: пробует latest и новейшие)")
    ap.add_argument("--out", default="textures",
                    help="папка назначения (по умолчанию textures)")
    ap.add_argument("--jobs", type=int, default=16)
    ap.add_argument("--skip-existing", action="store_true",
                    help="не перекачивать уже скачанные файлы")
    args = ap.parse_args(argv)

    wanted = [args.version] if args.version else []
    wanted += [v for v in FALLBACK_VERSIONS if v not in wanted]
    print("Список текстур ...")
    version, names = list_block_textures(wanted)
    if not names:
        sys.exit("Не удалось получить список текстур ни для одной версии.")

    outdir = Path(args.out) / "block"
    outdir.mkdir(parents=True, exist_ok=True)
    if args.skip_existing:
        names = [n for n in names if not (outdir / n).exists()]
        print(f"К докачке: {len(names)} файлов (остальные уже есть)")
    else:
        print(f"Версия {version}: {len(names)} текстур блоков. Качаю в {outdir} ...")

    tasks = [(n, version, outdir) for n in names]
    ok = failed = 0
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        for i, success in enumerate(pool.map(download_one, tasks), 1):
            ok += bool(success)
            failed += not success
            if i % 250 == 0:
                print(f"  {i}/{len(tasks)} ...")
    skipped = len(list(outdir.glob('*.png')))
    print(f"Готово: скачано {ok}" +
          (f", сбоев {failed}" if failed else "") +
          f"; всего в {outdir}: {skipped} файлов")
    print("Теперь запустите litematic2pdf.py - текстуры подхватятся автоматически.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
