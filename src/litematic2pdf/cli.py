"""Command line interface."""
import argparse
import datetime
import io
import sys
from collections import Counter
from pathlib import Path

from PIL import Image

from . import BRAND, __version__
from .blocks import AIR_NAMES, block_shape, resolve_color
from .errors import LitematicError, MAX_VOLUME
from .fonts import register_font
from .pdf import build_pdf
from .render import draw_grid_coords, render_layer
from .schema import (
    layer_plan,
    load_litematic,
    palette_colors,
    parse_region,
    tag_vector3,
)
from .textures import PHOTO_FILES, TextureSet

def build_parser():
    ap = argparse.ArgumentParser(
        prog="litematic2pdf",
        description="Litematica -> PDF: послойная схема сборки (как у Bloxelizer).")
    ap.add_argument("input", nargs="?", help="путь к .litematic файлу")
    ap.add_argument("-o", "--output", help="выходной PDF (по умолчанию: <имя>.pdf)")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    ap.add_argument("--axis", choices=["y", "x", "z"], default="y",
                    help="ось срезов (по умолчанию y — горизонтальные слои)")
    ap.add_argument("--scale", type=int, default=None,
                    help="пикселей на блок (по умолчанию: авто)")
    ap.add_argument("--max-size", type=int, default=8192,
                    help="максимальный размер слоя в px (по умолчанию 8192)")
    ap.add_argument("--page", choices=["auto", "a4", "a3", "a2"], default="auto",
                    help="размер страницы PDF (auto: A4/A3/A2 по габаритам "
                         "постройки, ориентация — по её пропорции)")
    ap.add_argument("--no-grid", action="store_true", help="не рисовать сетку")
    ap.add_argument("--regions", default=None,
                    help="список регионов через запятую (по умолчанию все)")
    ap.add_argument("--background", default=None,
                    help="фото для фона страниц (по умолчанию: background.png/jpg рядом)")
    ap.add_argument("--textures-dir", default="textures",
                    help="папка с текстурами блоков (textures/block/*.png)")
    ap.add_argument("--list-regions", action="store_true",
                    help="показать список регионов схемы и выйти")
    ap.add_argument("--watermark", default=None,
                    help="водяной знак на страницах (по умолчанию: имя проекта)")
    ap.add_argument("--no-watermark", action="store_true", help="отключить водяной знак")
    ap.add_argument("--title", default=None,
                    help="название гайда на обложке (по умолчанию: имя схемы/файла)")
    ap.add_argument("--description", default=None,
                    help="описание на обложке (например, краткая аннотация постройки)")
    ap.add_argument("--force", action="store_true",
                    help=f"обойти лимит объёма региона ({MAX_VOLUME:,} блоков)")
    ap.add_argument("--debug", action="store_true",
                    help="показывать полный трейсбек при непредвиденных ошибках")
    return ap


def main(argv=None):
    ap = build_parser()
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

    if not args.input:
        ap.error("не указан входной .litematic файл")

    try:
        return _run(args)
    except LitematicError as e:
        # expected, user-facing problems: one clean line, no traceback
        sys.exit(f"Ошибка: {e}")
    except Exception as e:
        if args.debug:
            raise
        sys.exit(f"Непредвиденная ошибка: {type(e).__name__}: {e}\n"
                 "Запустите с --debug, чтобы увидеть трейсбек, и пришлите её автору.")


def auto_cell_scale(w, h):
    """Pixels per block, adaptive to layer size — small builds get very
    crisp zoomable cells, huge builds get enough detail to stay readable
    while keeping the PDF memory-safe."""
    m = max(w, h)
    for limit, s in ((48, 24), (96, 16), (160, 12), (280, 8), (480, 6)):
        if m <= limit:
            return s
    return 4


def _run(args):
    src = Path(args.input)
    if not src.exists():
        raise LitematicError(f"файл не найден: {src}")

    print(f"Читаю {src} ...")
    root = load_litematic(src)
    meta_tag = root.get("Metadata", {})
    all_region_names = list(root.get("Regions", {}).keys())
    region_names = all_region_names
    if args.regions:
        wanted = [r.strip() for r in args.regions.split(",") if r.strip()]
        region_names = [r for r in wanted if r in all_region_names]
        missing = [r for r in wanted if r not in all_region_names]
        if missing:
            print(f"  ! регионы не найдены в схеме: {', '.join(missing)}")
    if not region_names:
        raise LitematicError("в файле нет регионов (или выбранные не найдены).")

    if args.list_regions:
        for rname in region_names:
            reg = root["Regions"][rname]
            size = tag_vector3(reg["Size"])
            pos = tag_vector3(reg.get("Position", [0, 0, 0]))
            print(f"  {rname}: {size[0]}x{size[1]}x{size[2]} @ {pos}")
        return 0

    font = register_font()
    if font == "Helvetica":
        print("Внимание: TTF-шрифт не найден — кириллица в PDF может не отобразиться.")

    def find_asset(name, search_dirs):
        for d in search_dirs:
            p = d / name
            if p.exists():
                return p
        return None

    search_dirs = [Path.cwd(), src.parent]
    if getattr(sys, "frozen", False):        # PyInstaller exe: bundled textures
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            search_dirs.append(Path(meipass))
    textures_root = find_asset(args.textures_dir, search_dirs)
    textures = (TextureSet(textures_root, photo_dirs=search_dirs)
                if textures_root else TextureSet(Path.cwd(), photo_dirs=search_dirs))
    if textures.count:
        print(f"Текстуры: {textures.count} файлов")
    else:
        print("Текстуры не найдены — блоки будут плоскими цветами. "
              "Скачайте их: python fetch_textures.py")
    for base in textures.photos:
        print(f"Фото-замена: «{base}» вместо ванильного спрайта "
              f"({PHOTO_FILES[base]}, вписан в клетки)")

    bg = None
    bg_path = Path(args.background) if args.background else None
    if bg_path is not None and bg_path.exists():
        pass
    else:
        bg_path = None
        for cand in ("background.png", "background.jpg", "background.jpeg"):
            found = find_asset(cand, search_dirs)
            if found:
                bg_path = found
                break
    if bg_path is not None:
        bg = Image.open(bg_path).convert("RGB")
        print(f"Фон: {bg_path}")
    else:
        print("Фон: бежевый, нейтральный. Чтобы поставить фото — "
              "положите background.png рядом или укажите --background")
    meta = {
        "file": src.name,
        "name": str(meta_tag.get("Name", "")),
        "author": str(meta_tag.get("Author", "")),
        "description": str(meta_tag.get("Description", "")),
    }
    if args.title:
        meta["name"] = args.title
    if args.description is not None:
        meta["description"] = args.description
    created = meta_tag.get("TimeCreated")
    if isinstance(created, int):
        try:
            meta["created"] = datetime.datetime.fromtimestamp(
                created / 1000.0).strftime("%d.%m.%Y %H:%M")
        except (OSError, OverflowError, ValueError):
            meta["created"] = ""
    else:
        meta["created"] = ""

    regions = []
    total_blocks = 0
    for rname in region_names:
        parsed = parse_region(root, rname)
        if parsed is None:
            print(f"  ! регион {rname} пустой — пропущен")
            continue
        sx, sy, sz = parsed["size"]
        volume = sx * sy * sz
        if volume > MAX_VOLUME and not args.force:
            raise LitematicError(
                f"регион '{rname}': объём {volume:,} блоков превышает лимит "
                f"{MAX_VOLUME:,}. Уменьшите выделение в Litematica или "
                "используйте --force (потребуется много времени и памяти)")
        pal_rgb, pal_names = palette_colors(parsed["palette"])
        pal_data = []
        for entry in parsed["palette"]:
            name = str(entry) if isinstance(entry, str) else str(entry.get("Name", ""))
            base = name.split(":")[-1]
            if base in AIR_NAMES:
                pal_data.append(None)
                continue
            tex = textures.get(base) if textures.count else None
            rgb = None if tex is not None else resolve_color(base)
            props = None
            if not isinstance(entry, str):
                pt = entry.get("Properties")
                if isinstance(pt, dict):
                    props = {str(k): str(v) for k, v in pt.items()}
            pal_data.append((tex, rgb, block_shape(base, props)))
        W, H, L, idx = layer_plan(args.axis, sx, sy, sz)
        axis_pos = {"x": 0, "y": 1, "z": 2}[args.axis]
        pos0 = parsed["pos"][axis_pos]

        if args.scale:
            scale = args.scale
        else:
            scale = auto_cell_scale(W, H)

        print(f"Регион '{rname}': {sx}x{sy}x{sz}, слоев по оси {args.axis}: {L}, "
              f"{scale} px/блок")
        layers = []
        materials = Counter()
        layer_blocks = 0
        rng = range(L)
        # side views: row 0 must be the top of the build (ground at the bottom)
        ys = range(H) if args.axis == "y" else range(H - 1, -1, -1)
        spam_step = 1 if L <= 60 else max(1, L // 20)
        for l in rng:
            layer_pi = [parsed["indices"][idx(x, y, l)]
                        for y in ys for x in range(W)]
            counts = Counter(pal_names[pi] for pi in layer_pi)
            for air in AIR_NAMES:
                counts.pop(air, None)
            img, count = render_layer(layer_pi, pal_data, W, H, scale,
                                      not args.no_grid, args.max_size, bg)
            label = f"Layer {args.axis.upper()}={pos0 + l} " \
                    f"({l + 1}/{L} from bottom)"
            if not args.no_grid:
                cell_px = img.size[0] // W if W else 1
                img = draw_grid_coords(img, W, H, cell_px)
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            png = buf.getvalue()
            size = img.size
            del img, buf, layer_pi
            materials.update(counts)
            layer_blocks += count
            total_blocks += count
            top = counts.most_common()
            if l % spam_step == 0 or l == L - 1:
                print(f"  {label}: {count} блоков")
            layers.append((label, png, size, count, top))
        regions.append({
            "name": rname, "size": [sx, sy, sz], "pos": parsed["pos"],
            "axis": args.axis, "layers": layers, "materials": materials,
            "blocks": layer_blocks,
            "page_range": "—",
            "grid_w": W, "grid_h": H,
        })

    if not regions:
        raise LitematicError("нечего рисовать: все регионы пустые или пропущены")
    meta["total_blocks"] = total_blocks
    for r in regions:
        n = len(r["layers"])
        r["page_range"] = f"{n} layers, {n} pages (1 layer per page)"

    out = Path(args.output) if args.output else src.with_suffix(".pdf")
    if args.no_watermark:
        watermark = None
    elif args.watermark is not None:
        watermark = args.watermark or None
    else:
        watermark = BRAND
    try:
        build_pdf(out, src.stem, meta, regions, font,
                  background=bg, textures=textures, watermark=watermark,
                  page_mode=args.page)
    except OSError as e:
        raise LitematicError(
            f"не удалось записать «{out}»: {e.strerror}. "
            "Возможно, PDF открыт в просмотрщике — закройте его и повторите")
    size_kb = out.stat().st_size / 1024
    print(f"\nГотово: {out} ({size_kb:.0f} КБ, всего блоков {total_blocks:,})")
    return 0
