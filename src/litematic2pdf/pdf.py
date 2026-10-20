"""PDF assembly: cover, layer pages with sidebar, materials, watermark."""
import io
from collections import Counter

from PIL import Image
from reportlab.lib import colors as rl_colors
from reportlab.lib.pagesizes import A2, A3, A4, landscape, portrait
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    Image as RLImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .blocks import BEIGE, pretty_name, resolve_color
from .fonts import register_script_font
from .render import render_layer
from .textures import cover_crop

# neutral page background (classic beige)
PAGE_BG_RGB = BEIGE


def pil_to_rlimage(pil_img):
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf


def pick_page(max_w_blocks, max_h_blocks, mode="auto"):
    """Page size adapts to the build: bigger builds get bigger paper,
    tall builds get portrait pages. Returns a reportlab page size tuple."""
    big = max(max_w_blocks, max_h_blocks)
    if mode == "auto":
        base = A4 if big <= 64 else (A3 if big <= 140 else A2)
    else:
        base = {"a4": A4, "a3": A3, "a2": A2}[mode]
    return landscape(base) if max_w_blocks >= max_h_blocks else portrait(base)


def _chip(rgb, w_mm, h_mm):
    t = Table([[""]], colWidths=[w_mm * mm], rowHeights=[h_mm * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), rl_colors.HexColor("#%02x%02x%02x" % rgb)),
        ("BOX", (0, 0), (-1, -1), 0.4, rl_colors.HexColor("#999999")),
    ]))
    return t


def _thumb_cell(tex, w_mm=11, h_mm=11):
    if tex is None:
        return None
    tile = tex.resize((32, 32), Image.NEAREST)
    buf = io.BytesIO()
    tile.save(buf, format="PNG")
    return RLImage(io.BytesIO(buf.getvalue()), width=w_mm * mm, height=h_mm * mm)


LEGEND_SAMPLES = [
    ("spruce_stairs", "stairs:north:straight"),
    ("spruce_stairs", "stairs:east:straight"),
    ("oak_slab", "slab_bottom"),
    ("glass", "full"),
    ("cobblestone", "full"),
]


def make_legend_preview(textures, cell=40):
    """Render a real 5-cell sample strip for the cover legend:
    stairs facing north / east, slab, glass, full block."""
    pal_data = []
    for base, shape in LEGEND_SAMPLES:
        tex = textures.get(base) if textures and textures.count else None
        rgb = None if tex is not None else resolve_color(base)
        pal_data.append((tex, rgb, shape))
    img, _ = render_layer(list(range(len(pal_data))), pal_data, len(pal_data), 1,
                          cell, False, 4096)
    return img


def build_cover(title, meta, regions, styles, font, textures, content_w):
    """Flowables for a decorated first page."""
    fl = [Spacer(1, 14 * mm)]
    fl.append(Paragraph(title, styles["title"]))
    fl.append(Paragraph("Layer-by-layer Build Guide", styles["h2"]))
    line = Table([[""]], colWidths=[60 * mm], rowHeights=[0.9 * mm])
    line.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1),
                               rl_colors.HexColor("#8a6f4a"))]))
    fl.append(line)
    fl.append(Spacer(1, 6 * mm))
    description = str(meta.get("description", "")).strip()
    if description:
        fl.append(Paragraph(description.replace("\n", "<br/>"), styles["desc"]))
        fl.append(Spacer(1, 6 * mm))
    else:
        fl.append(Spacer(1, 2 * mm))

    # ---- info card ----
    total_layers = sum(len(r["layers"]) for r in regions)
    sizes = "  ·  ".join(
        f"{r['name']}: {r['size'][0]}x{r['size'][1]}x{r['size'][2]}"
        for r in regions)
    info = [
        ["Regions", str(len(regions))],
        ["Build size", sizes],
        ["Layers", f"{total_layers} (sliced along {regions[0]['axis'].upper()})"],
        ["Total blocks", f"{meta.get('total_blocks', 0):,}".replace(",", " ")],
    ]
    card = Table(info, colWidths=[28 * mm, content_w - 60 * mm])
    card.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), font),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), rl_colors.HexColor("#8a6f4a")),
        ("TEXTCOLOR", (1, 0), (1, -1), rl_colors.HexColor("#4a3a3a")),
        ("BACKGROUND", (0, 0), (-1, -1),
         rl_colors.Color(1, 1, 1, alpha=0.35)),
        ("BOX", (0, 0), (-1, -1), 0.5, rl_colors.HexColor("#c9b896")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, rl_colors.HexColor("#d8cbae")),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    fl.append(card)
    fl.append(Spacer(1, 8 * mm))

    # ---- materials preview strip ----
    merged = Counter()
    for r in regions:
        merged.update(r["materials"])
    top = merged.most_common(8)
    if top:
        fl.append(Paragraph("Main materials", styles["h3"]))
        img_row, cap_row = [], []
        for name, cnt in top:
            tex = textures.get(name) if textures and textures.count else None
            cell = _thumb_cell(tex) or _chip(resolve_color(name) or (200, 200, 200), 11, 11)
            img_row.append(cell)
            cap_row.append(Paragraph(
                f"{cnt:,}<br/>{pretty_name(name)}".replace(",", " "),
                styles["caption"]))
        cw = [content_w / len(top)] * len(top)
        hero = Table([img_row, cap_row], colWidths=cw)
        hero.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]))
        fl.append(hero)
        fl.append(Spacer(1, 8 * mm))

    # ---- legend: what the symbols mean ----
    try:
        legend_img = make_legend_preview(textures)
        iw = len(LEGEND_SAMPLES) * 9 * mm
        fl.append(Paragraph("How to read the layers", styles["h3"]))
        fl.append(RLImage(pil_to_rlimage(legend_img), width=iw, height=iw / 5.0,
                          hAlign="LEFT"))
        fl.append(Paragraph(
            "1-2: stairs — red arrow points where the stair faces, dark half is the "
            "low step &nbsp;&nbsp;|&nbsp;&nbsp; 3: slab — half cell &nbsp;&nbsp;|&nbsp;&nbsp;"
            "4: glass/water — translucent &nbsp;&nbsp;|&nbsp;&nbsp;5: full block. "
            "Top view: north up, east right.", styles["small"]))
    except Exception:
        pass  # legend is decoration; never block the build
    fl.append(PageBreak())
    return fl


def build_pdf(out_path, title, meta, regions, font,
              background=None, textures=None, watermark=None, page_mode="auto"):
    """regions: list of dicts with name, size, pos, axis, layers, materials.
    layers items: (label, png_bytes, (w_px, h_px), count, top_blocks)."""
    # page size adapts to the biggest layer
    max_w = max((r.get("grid_w") or r["size"][0]) for r in regions)
    max_h = max((r.get("grid_h") or r["size"][2]) for r in regions)
    page_size = pick_page(max_w, max_h, page_mode)
    doc = SimpleDocTemplate(
        str(out_path), pagesize=page_size,
        leftMargin=6 * mm, rightMargin=6 * mm,
        topMargin=6 * mm, bottomMargin=6 * mm,
        title=f"{title} — Layer-by-layer Build Guide",
        author="",
    )
    page_w, page_h = page_size
    content_w = page_w - 12 * mm
    content_h = page_h - 12 * mm

    # neutral beige background page (or user photo if given)
    if background is not None:
        page_bg = cover_crop(background.convert("RGB"), int(page_w), int(page_h))
    else:
        page_bg = Image.new("RGB", (int(page_w), int(page_h)), PAGE_BG_RGB)

    # guide title: cover headline and running header
    raw_name = str(meta.get("name", "")).strip()
    display_title = raw_name if raw_name and raw_name.lower() != "unnamed" else title

    # signature script font (falls back to the main font when unavailable)
    sig_font = register_script_font()

    def draw_bg(canvas, doc):
        canvas.saveState()
        canvas.drawImage(ImageReader(page_bg), 0, 0, page_w, page_h)
        if canvas.getPageNumber() > 1:
            # tasteful running header on every guide page
            canvas.setFont(font, 8.5)
            canvas.setFillColor(rl_colors.HexColor("#8a7a66"))
            canvas.drawString(8 * mm, page_h - 4.5 * mm, display_title)
            canvas.drawRightString(page_w - 8 * mm, page_h - 4.5 * mm,
                                   "Layer-by-layer Build Guide")
        if watermark:
            wm = str(watermark)
            # ghosted name tiled across the whole page (brick pattern),
            # behind all content
            wm_font = sig_font or font
            wm_size = 48
            canvas.setFont(wm_font, wm_size)
            canvas.setFillColor(rl_colors.Color(0.29, 0.23, 0.23, alpha=0.09))
            canvas.translate(page_w / 2.0, page_h / 2.0)
            canvas.rotate(30)
            diag = (page_w ** 2 + page_h ** 2) ** 0.5
            step_x = canvas.stringWidth(wm, wm_font, wm_size) + 16 * mm
            step_y = 26 * mm
            cols = int(diag / step_x) + 2
            rows = int(diag / step_y) + 1
            x0 = -step_x * (cols - 1) / 2.0
            y0 = -step_y * (rows - 1) / 2.0
            for row in range(rows):
                off = step_x / 2.0 if row % 2 else 0.0
                for col in range(cols):
                    canvas.drawCentredString(x0 + off + col * step_x,
                                             y0 + row * step_y, wm)
            canvas.restoreState()
            # cursive signature in the corner
            canvas.saveState()
            canvas.setFont(sig_font or font, 15)
            canvas.setFillColor(rl_colors.Color(0.42, 0.30, 0.20, alpha=0.85))
            canvas.drawString(8 * mm, 5.5 * mm, wm)
        else:
            canvas.saveState()
        canvas.setFont(font, 7)
        canvas.setFillColor(rl_colors.HexColor("#555555"))
        canvas.drawRightString(page_w - 8 * mm, 5 * mm,
                               f"— {canvas.getPageNumber()} —")
        canvas.restoreState()

    styles = {
        "title": ParagraphStyle("title", fontName=font, fontSize=32, leading=38,
                                spaceAfter=6 * mm, textColor=rl_colors.HexColor("#4a3a3a")),
        "h2": ParagraphStyle("h2", fontName=font, fontSize=18, leading=24,
                             spaceBefore=4 * mm, spaceAfter=2 * mm,
                             textColor=rl_colors.HexColor("#4a3a3a")),
        "h3": ParagraphStyle("h3", fontName=font, fontSize=13, leading=17,
                             spaceBefore=1 * mm, spaceAfter=1 * mm,
                             textColor=rl_colors.HexColor("#5a4a4a")),
        "body": ParagraphStyle("body", fontName=font, fontSize=10, leading=14),
        "desc": ParagraphStyle("desc", fontName=font, fontSize=11, leading=15,
                               alignment=1,
                               textColor=rl_colors.HexColor("#5a4a4a")),
        "page_header": ParagraphStyle("page_header", fontName=font, fontSize=8.5,
                                      leading=11,
                                      textColor=rl_colors.HexColor("#8a7a66")),
        "sidebar_item": ParagraphStyle("sidebar_item", fontName=font, fontSize=7.5,
                                       leading=9.5,
                                       textColor=rl_colors.HexColor("#4a3a3a")),
        "caption": ParagraphStyle("caption", fontName=font, fontSize=6.5, leading=8.5,
                                  alignment=1,
                                  textColor=rl_colors.HexColor("#6a5a5a")),
        "small": ParagraphStyle("small", fontName=font, fontSize=8, leading=10,
                                textColor=rl_colors.HexColor("#6a5a5a")),
        "layer_label": ParagraphStyle("layer_label", fontName=font, fontSize=28, leading=34,
                                      alignment=1,  # center
                                      textColor=rl_colors.HexColor("#4a3a3a")),
    }
    story = []

    # ---- cover ----
    story.extend(build_cover(display_title, meta, regions, styles, font,
                             textures, content_w))

    # ---- regions ----
    for region in regions:
        layers = region["layers"]
        size = region["size"]
        axis = region["axis"]
        W = region["grid_w"] if "grid_w" in region else (size[0] if axis != "x" else size[2])
        H = region["grid_h"] if "grid_h" in region else (size[1] if axis != "y" else size[2])

        # layers are pre-rendered PNGs (bytes) with coordinates baked in
        for i, (label, png, size, count, top_blocks) in enumerate(layers):
            # all block types of this layer, sorted by count desc
            story.extend(build_layer_page(
                layer_num=i + 1,
                total_layers=len(layers),
                img_png=png,
                img_size=size,
                sidebar_items=list(top_blocks),
                grid_w=W,
                grid_h=H,
                styles=styles,
                font=font,
                textures=textures,
                region_name=region["name"],
                page_w=page_w,
                page_h=page_h,
                content_w=content_w,
                content_h=content_h,
            ))
            if i < len(layers) - 1:
                story.append(PageBreak())

    # ---- materials grid ----
    story.append(PageBreak())
    story.extend(build_materials_grid(regions, styles, font, textures, content_w, content_h))

    doc.build(story, onFirstPage=draw_bg, onLaterPages=draw_bg)


def build_layer_page(layer_num, total_layers, img_png, img_size, sidebar_items,
                     grid_w, grid_h,
                     styles, font, textures, region_name, page_w, page_h,
                     content_w, content_h):
    """Build a single layer page with sidebar and grid using single table with SPAN."""
    sidebar_w = content_w * 0.22
    gap = 4 * mm
    grid_area_w = content_w - sidebar_w - gap

    # Scale image to fit grid area
    iw, ih = img_size
    k = min(grid_area_w / iw, content_h * 0.85 / ih)
    disp_w, disp_h = iw * k, ih * k

    layer_label = Paragraph(f"Layer {layer_num} / {total_layers}", styles["layer_label"])

    # keep the sidebar on one page even for huge builds with 100+ block types
    max_rows = 29
    overflow = max(0, len(sidebar_items) - max_rows)
    shown = sidebar_items[:max_rows]

    # Build sidebar rows (header + one compact row per block type)
    icon_sz = 4.2 * mm
    text_w = sidebar_w - 2 * (icon_sz + 1.2 * mm) - 6 * mm
    sidebar_rows = [[Paragraph(f"Blocks in this layer ({len(sidebar_items)})",
                               styles["h3"])]]
    for name, cnt in shown:
        pname = pretty_name(name)
        top_tex = textures.get(name) if textures and textures.count else None
        side_tex = textures.get_side(name) if textures and textures.count else None

        cells = []
        for tex in (side_tex, top_tex):
            if tex:
                thumb = tex.resize((24, 24), Image.NEAREST)
                buf = io.BytesIO()
                thumb.save(buf, format="PNG")
                cells.append(RLImage(io.BytesIO(buf.getvalue()),
                                     width=icon_sz, height=icon_sz))
            else:
                rgb = resolve_color(name)
                sw = Spacer(1, icon_sz)
                if rgb:
                    cell = Table([[""]], colWidths=[icon_sz], rowHeights=[icon_sz])
                    cell.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1),
                         rl_colors.HexColor("#%02x%02x%02x" % rgb)),
                        ("BOX", (0, 0), (-1, -1), 0.4, rl_colors.HexColor("#999999")),
                    ]))
                    cells.append(cell)
                else:
                    cells.append(sw)

        item = Table([[cells[0], cells[1],
                       Paragraph(f"{cnt}x {pname}", styles["sidebar_item"])]],
                     colWidths=[icon_sz + 1.2 * mm, icon_sz + 1.2 * mm, text_w + 6 * mm])
        item.setStyle(TableStyle([
            ("ALIGN", (0, 0), (1, 0), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 0.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 1),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ]))
        sidebar_rows.append([item])
    if overflow:
        sidebar_rows.append([Paragraph(
            f"...and {overflow} more type{'s' if overflow > 1 else ''} "
            "(see Materials page)", styles["small"])])

    # Grid cell (column 1, spans all sidebar rows); bytes already contain
    # the baked-in coordinate ruler from the render step
    grid_cell = RLImage(io.BytesIO(img_png), width=disp_w, height=disp_h)

    all_rows = []
    num_sidebar = len(sidebar_rows)

    # Row 0: sidebar header + grid image
    all_rows.append([sidebar_rows[0][0], grid_cell])

    # Rows 1..N-1: sidebar items + empty (grid spans over them)
    for i in range(1, num_sidebar):
        all_rows.append([sidebar_rows[i][0], Spacer(1, 1)])

    # Create table with 2 columns
    page_table = Table(all_rows, colWidths=[sidebar_w, grid_area_w + gap])
    style_cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        # Span grid image across all sidebar rows
        ("SPAN", (1, 0), (1, num_sidebar - 1)),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("VALIGN", (1, 0), (1, 0), "MIDDLE"),
    ]
    page_table.setStyle(TableStyle(style_cmds))

    # the label is a separate flowable below the table — inside a SPANned
    # table row it was silently swallowed
    return [page_table, Spacer(1, 3 * mm), layer_label]


def build_materials_grid(regions, styles, font, textures, content_w, content_h):
    """Build materials page as 2-column grid with side+top textures. Returns list of flowables."""
    flowables = []
    flowables.append(Paragraph("Materials", styles["h2"]))
    flowables.append(Spacer(1, 4 * mm))

    for region in regions:
        flowables.append(Paragraph(f"Region: {region['name']}", styles["h3"]))
        flowables.append(Spacer(1, 2 * mm))

        items = region["materials"].most_common()
        cols = 2  # 2 columns for wide text cells
        cell_w = content_w / cols
        thumb_mm = 12  # mm per thumbnail

        rows = []
        row = []
        for idx, (name, cnt) in enumerate(items):
            pname = pretty_name(name)
            top_tex = textures.get(name) if textures and textures.count else None
            side_tex = textures.get_side(name) if textures and textures.count else None

            # Create thumbnails
            top_img = None
            side_img = None
            if top_tex:
                t = top_tex.resize((32, 32), Image.NEAREST)
                b = io.BytesIO()
                t.save(b, format="PNG")
                top_img = RLImage(io.BytesIO(b.getvalue()), width=thumb_mm * mm, height=thumb_mm * mm)
            if side_tex:
                t = side_tex.resize((32, 32), Image.NEAREST)
                b = io.BytesIO()
                t.save(b, format="PNG")
                side_img = RLImage(io.BytesIO(b.getvalue()), width=thumb_mm * mm, height=thumb_mm * mm)

            # Cell: side | top  /  count x name (text spans both thumbnails)
            text_w = cell_w - 2 * thumb_mm * mm - 4 * mm
            cell_content = [
                [side_img or Spacer(thumb_mm * mm, thumb_mm * mm),
                 top_img or Spacer(thumb_mm * mm, thumb_mm * mm)],
                [Paragraph(f"{cnt}x {pname}", styles["small"]), ""],
            ]
            cell_table = Table(cell_content, colWidths=[thumb_mm * mm, max(thumb_mm * mm, text_w)])
            cell_table.setStyle(TableStyle([
                ("SPAN", (0, 1), (1, 1)),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]))

            row.append(cell_table)
            if len(row) == cols:
                rows.append(row)
                row = []

        if row:
            while len(row) < cols:
                row.append(Spacer(cell_w, 1))
            rows.append(row)

        mat_table = Table(rows, colWidths=[cell_w] * cols)
        mat_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ]))
        flowables.append(mat_table)
        flowables.append(Spacer(1, 4 * mm))

    return flowables
