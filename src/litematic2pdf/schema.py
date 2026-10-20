"""Decoding of Litematica .litematic NBT files."""
import array

import nbtlib

from .blocks import AIR_NAMES, resolve_color
from .errors import LitematicError

def load_litematic(path):
    for gzipped in (True, False):
        try:
            root = nbtlib.File.load(path, gzipped=gzipped)
        except Exception:
            continue
        if "Regions" not in root:
            raise LitematicError(
                f"{path.name}: это NBT-файл, но без разделов Regions — "
                "похоже на .schem/.schematic, а не .litematic. "
                "Конвертируйте схему через Litematica (mod) в .litematic")
        return root
    raise LitematicError(
        f"{path.name}: не читается как NBT (сжатый или нет). "
        "Убедитесь, что это файл .litematic из мода Litematica")


def tag_vector3(tag):
    """Size/Position can be an IntArray or a Compound {x,y,z} (new Litematica)."""
    if isinstance(tag, nbtlib.tag.Compound):
        return [int(tag["x"]), int(tag["y"]), int(tag["z"])]
    values = [int(v) for v in tag]
    if len(values) != 3:
        raise ValueError(f"ожидалось 3 числа, найдено {len(values)}")
    return values


def parse_region(root, region_name):
    """Decode one region; returns None for harmless empty/degenerate cases,
    raises LitematicError for corrupt structures."""
    region = root["Regions"][region_name]
    for tag in ("Size", "BlockStatePalette", "BlockStates"):
        if tag not in region:
            raise LitematicError(
                f"регион '{region_name}': нет тега {tag} — файл повреждён")
    try:
        size = tag_vector3(region["Size"])
        pos = tag_vector3(region.get("Position", [0, 0, 0]))
    except (KeyError, ValueError, TypeError) as e:
        raise LitematicError(f"регион '{region_name}': битые Size/Position ({e})")
    palette = list(region["BlockStatePalette"])
    long_data = [int(v) & 0xFFFFFFFFFFFFFFFF for v in region["BlockStates"]]

    if not palette or all(str(e) in AIR_NAMES for e in palette):
        return None
    # negative components (new Litematica): the min corner is pos + size
    min_corner = [pos[i] + (size[i] if size[i] < 0 else 0) for i in range(3)]
    size = [abs(v) for v in size]
    if 0 in size:
        return None  # degenerate flat region
    total = size[0] * size[1] * size[2]

    bits = max(2, (len(palette) - 1).bit_length())
    mask = (1 << bits) - 1
    needed = (total * bits + 63) // 64
    if len(long_data) < needed:
        raise LitematicError(
            f"регион '{region_name}': BlockStates короче, чем нужно "
            f"({len(long_data)} < {needed}) — файл обрезан или повреждён")

    last = len(palette) - 1
    indices = array.array("q", bytes(0))
    append = indices.append
    for i in range(total):
        start = i * bits
        li = start >> 6
        off = start & 63
        v = (long_data[li] >> off) if li < len(long_data) else 0
        if off + bits > 64:
            v |= long_data[li + 1] << (64 - off)
        v &= mask
        if v > last:  # index beyond palette: garbage data
            raise LitematicError(
                f"регион '{region_name}': индекс блока {v} вне палитры "
                f"(0..{last}) — файл повреждён")
        append(v)
    return {"size": size, "pos": min_corner, "palette": palette, "indices": indices}


def palette_colors(palette):
    """Per palette entry: (r, g, b) or None for air, plus display name."""
    colors, names = [], []
    for entry in palette:
        if isinstance(entry, str):
            name = entry
        else:
            name = str(entry.get("Name", ""))
        base = name.split(":")[-1]
        colors.append(resolve_color(base))
        names.append(base)
    return colors, names


def layer_plan(axis, sx, sy, sz):
    """Return (width, height, layer_count, index_func) for a slice axis."""
    if axis == "y":
        def idx(x, y, l):
            return x + y * sx + l * sx * sz
        return sx, sz, sy, idx
    if axis == "z":
        def idx(x, y, l):
            return x + l * sx + y * sx * sz
        return sx, sy, sz, idx
    # axis == "x"
    def idx(x, y, l):
        return l + x * sx + y * sx * sz
    return sz, sy, sx, idx
