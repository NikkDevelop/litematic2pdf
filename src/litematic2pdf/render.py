"""Raster rendering of a single layer: blocks, shading, arrows, grid."""
from PIL import Image, ImageDraw

from .blocks import shape_parts
from .textures import cover_crop

def draw_grid_coords(img, grid_w, grid_h, cell_size, font_path=None):
    """Draw coordinate numbers on the grid (X at bottom, Y at left).

    On dense grids numbers are printed every `stride` cells so they stay
    readable on builds hundreds of blocks wide."""
    from PIL import ImageDraw, ImageFont
    draw = ImageDraw.Draw(img)
    try:
        if font_path:
            fnt = ImageFont.truetype(font_path, max(8, cell_size // 3))
        else:
            fnt = ImageFont.load_default()
    except Exception:
        fnt = ImageFont.load_default()

    if cell_size >= 16:
        stride = 1
    elif cell_size >= 8:
        stride = 5
    elif cell_size >= 4:
        stride = 10
    else:
        stride = 25

    text_color = (80, 80, 80, 200)
    # X coordinates at bottom
    for x in range(0, grid_w, stride):
        cx = x * cell_size + cell_size // 2
        cy = grid_h * cell_size - 2
        txt = str(x + 1)
        # Use textbbox (works in Pillow 8+)
        bbox = draw.textbbox((0, 0), txt, font=fnt)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((cx - tw // 2, cy - th), txt, fill=text_color, font=fnt)
    # Y coordinates at left
    for y in range(0, grid_h, stride):
        cx = 2
        cy = y * cell_size + cell_size // 2
        txt = str(y + 1)
        bbox = draw.textbbox((0, 0), txt, font=fnt)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text((cx, cy - th // 2), txt, fill=text_color, font=fnt)
    return img


ARROW_RGB = (214, 30, 30)


_ARROW_DIR = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}


def _draw_stair_arrow(draw, facing, cx, cy, s):
    dx, dy = _ARROW_DIR[facing]
    mx, my = cx + s / 2.0, cy + s / 2.0
    a = s * 0.32
    tip = (mx + dx * a, my + dy * a)
    tail = (mx - dx * a, my - dy * a)
    w = max(1, s // 12)
    draw.line([tail, tip], fill=ARROW_RGB, width=w)
    hl = s * 0.24
    px, py = -dy, dx
    for sd in (1, -1):
        draw.line([tip, (tip[0] - dx * hl + px * hl * 0.6 * sd,
                         tip[1] - dy * hl + py * hl * 0.6 * sd)],
                  fill=ARROW_RGB, width=w)


def render_layer(layer_indices, pal_data, width, height, scale, grid, max_px,
                 bg_image=None):
    """pal_data: per palette entry None (air) or (texture, rgb, shape)."""
    k = min(1.0, max_px / max(width, height)) if max(width, height) > 0 else 1.0
    s = max(1, int(scale * k))
    w_px, h_px = width * s, height * s

    if bg_image is not None:
        base = cover_crop(bg_image, w_px, h_px).convert("RGBA")
        overlay = Image.new("RGBA", (w_px, h_px), (255, 255, 255, 70))
        img = Image.alpha_composite(base, overlay).convert("RGBA")
    else:
        # Transparent background — the beige PDF page color shows through air
        img = Image.new("RGBA", (w_px, h_px), (0, 0, 0, 0))

    draw = ImageDraw.Draw(img)
    tile_cache = {}
    count = 0
    pos = 0
    shade_layer = None
    stairs_cells = []
    for pi in layer_indices:
        entry = pal_data[pi]
        if entry is not None:
            count += 1
            cx = (pos % width) * s
            cy = (pos // width) * s
            tex, rgb, shape = entry
            parts = shape_parts(shape, s)
            if shape.startswith("stairs:"):
                stairs_cells.append((shape.split(":")[1], cx, cy))
            if tex is not None:
                tile = tile_cache.get(id(tex))
                if tile is None:
                    tile = tex.resize((s, s), Image.NEAREST)
                    tile_cache[id(tex)] = tile
                for rx, ry, rw, rh, dark in parts:
                    if rw == s and rh == s:
                        img.paste(tile, (cx, cy), tile)
                    else:
                        # partial shape: slab half / stair quadrant
                        part = tile.crop((rx, ry, rx + rw, ry + rh))
                        img.paste(part, (cx + rx, cy + ry), part)
                    if dark:
                        # shade the lower stair half like a cast shadow
                        if shade_layer is None:
                            shade_layer = Image.new("RGBA", (w_px, h_px),
                                                    (0, 0, 0, 0))
                            shade_draw = ImageDraw.Draw(shade_layer)
                        shade_draw.rectangle(
                            (cx + rx, cy + ry, cx + rx + rw - 1, cy + ry + rh - 1),
                            fill=(0, 0, 0, 150))
            else:
                for rx, ry, rw, rh, dark in parts:
                    col = rgb if not dark else tuple(int(v * 0.45) for v in rgb)
                    draw.rectangle((cx + rx, cy + ry,
                                    cx + rx + rw - 1, cy + ry + rh - 1),
                                   fill=col)
        pos += 1

    if shade_layer is not None:
        img = Image.alpha_composite(img, shade_layer)

    if grid and s >= 3:
        # draw on a separate layer and composite, otherwise the lines
        # would turn solid black when the alpha channel is dropped
        overlay = Image.new("RGBA", (w_px, h_px), (0, 0, 0, 0))
        gdraw = ImageDraw.Draw(overlay)
        for gx in range(s, w_px, s):
            gdraw.line([(gx, 0), (gx, h_px)], fill=(0, 0, 0, 45))
        for gy in range(s, h_px, s):
            gdraw.line([(0, gy), (w_px, gy)], fill=(0, 0, 0, 45))
        gdraw.rectangle([0, 0, w_px - 1, h_px - 1], outline=(0, 0, 0, 120))
        img = Image.alpha_composite(img, overlay)

    # red facing arrows last, on top of everything
    if stairs_cells and s >= 8:
        adraw = ImageDraw.Draw(img)
        for facing, cx, cy in stairs_cells:
            _draw_stair_arrow(adraw, facing, cx, cy, s)
    return img, count  # keep RGBA so the beige page background shows through air
