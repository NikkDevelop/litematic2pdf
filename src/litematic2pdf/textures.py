"""Vanilla texture lookup: top/side candidates, tinting, cover-crop."""
from pathlib import Path

from PIL import Image, ImageChops

from .blocks import TINTS, WOOD_COLORS, apply_tint

# Hand-made artwork that replaces tiny vanilla sprites on schemes.
# Pictures are searched beside the tool / schematic files.
PHOTO_FILES = {
    "lantern": "lantern.png",
}

PHOTO_FILL = 0.9  # fraction of the cell the fitted picture occupies


def _key_color(img, rgb, tolerance=8):
    """Make pixels matching rgb transparent (flat art on a solid canvas).

    Strict per-channel match: palette flame whites like (255,255,212)
    stay intact, only the exact backdrop disappears."""
    r, g, b, a = img.split()
    planes = [c.point(lambda v, t=t: 255 if abs(v - t) <= tolerance else 0)
              for c, t in zip((r, g, b), rgb)]
    hit = ImageChops.multiply(ImageChops.multiply(planes[0], planes[1]), planes[2])
    return Image.merge("RGBA", (r, g, b, ImageChops.multiply(a, ImageChops.invert(hit))))


def _fit_square(img, fill=PHOTO_FILL):
    """Crop to visible content and center it on a transparent square,
    so every cell size keeps the picture proportions."""
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    w, h = img.size
    side = max(1, round(max(w, h) / fill))
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - w) // 2, (side - h) // 2), img)
    return canvas


def load_photo_overrides(search_dirs):
    """Load PHOTO_FILES artwork; returns {block base name: square RGBA image}."""
    out = {}
    for base, fname in PHOTO_FILES.items():
        for d in search_dirs:
            p = Path(d) / fname
            if p.exists():
                try:
                    img = _key_color(Image.open(p).convert("RGBA"),
                                     (255, 255, 255))
                    out[base] = _fit_square(img)
                except Exception:
                    pass
                break
    return out


TOP_OVERRIDES = {
    "water": "water_still",
    "lava": "lava_still",
    "redstone_wire": "redstone_dust_line0",
    "bookshelf": "oak_planks",
    "chiseled_bookshelf": "chiseled_bookshelf_top",
    "dispenser": "dispenser_front_vertical",
    "dropper": "dropper_front_vertical",
    "jack_o_lantern": "pumpkin_top",
    "carved_pumpkin": "pumpkin_top",
    # plants renamed / half-blocks
    "grass": "short_grass",
    "tall_grass": "tall_grass_top",
    "large_fern": "large_fern_top",
    "sunflower": "sunflower_top",
    # functional blocks with distinct top faces
    "piston": "piston_top",
    "sticky_piston": "piston_top_sticky",
    "observer": "observer_top",
    "barrel": "barrel_top",
    "hopper": "hopper_top",
    "cauldron": "cauldron_top",
    "composter": "composter_top",
    "furnace": "furnace_top",
    "blast_furnace": "blast_furnace_top",
    "smoker": "smoker_top",
    "stonecutter": "stonecutter_top",
    "loom": "loom_top",
    "cartography_table": "cartography_table_top",
    "fletching_table": "fletching_table_top",
    "smithing_table": "smithing_table_top",
    "lectern": "lectern_top",
    "jukebox": "jukebox_top",
    "target": "target_top",
    "daylight_detector": "daylight_detector_top",
    "sculk_sensor": "sculk_sensor_top",
    "calibrated_sculk_sensor": "calibrated_sculk_sensor_top",
    "sculk_catalyst": "sculk_catalyst_top",
    "sculk_shrieker": "sculk_shrieker_top",
    "crafter": "crafter_top",
    "beehive": "beehive_end",
    "bee_nest": "bee_nest_top",
    "campfire": "campfire_log_lit",
    "soul_campfire": "soul_campfire_log_lit",
    # blocks whose side texture is not the top one
    "hay_block": "hay_block_top",
    "bone_block": "bone_block_top",
    "mycelium": "mycelium_top",
    "podzol": "podzol_top",
    "dirt_path": "dirt_path_top",
    "sandstone": "sandstone_top",
    "red_sandstone": "red_sandstone_top",
    "quartz_block": "quartz_block_top",
    "quartz_pillar": "quartz_pillar_top",
    "purpur_pillar": "purpur_pillar_top",
    "bamboo_block": "bamboo_block_top",
    "mangrove_roots": "mangrove_roots_top",
    "muddy_mangrove_roots": "muddy_mangrove_roots_top",
    "ochre_froglight": "ochre_froglight_top",
    "verdant_froglight": "verdant_froglight_top",
    "pearlescent_froglight": "pearlescent_froglight_top",
    "respawn_anchor": "respawn_anchor_top",
    "ancient_debris": "ancient_debris_top",
    "basalt": "basalt_top",
    "polished_basalt": "polished_basalt_top",
    "blackstone": "blackstone_top",
    "reinforced_deepslate": "reinforced_deepslate_top",
    "end_portal_frame": "end_portal_frame_top",
    "lodestone": "lodestone_top",
    "chain": "iron_chain",
}


def texture_candidates(base):
    """Ordered candidate texture names for the top-down view of a block.

    Rule 1: explicit overrides (top texture has a different file name).
    Rule 2: automatic '{base}_top' when such a texture exists (logs, stems,
            grass_block, deepslate, cake, cauldron, hopper, anvil, ...).
    Rule 3: the base texture itself.
    Rule 4: block variants (slabs/stairs/fences/...) reuse the base block.
    """
    if base in TOP_OVERRIDES:
        yield TOP_OVERRIDES[base]
    yield base + "_top"
    yield base
    for suffix in ("_slab", "_stairs", "_wall", "_fence_gate", "_fence", "_button",
                   "_pressure_plate", "_carpet", "_sign", "_hanging_sign", "_head",
                   "_banner", "_bed", "_trapdoor", "_torch", "_door"):
        if base.endswith(suffix):
            b = base[:-len(suffix)]
            yield b
            yield b + "s"  # plural base texture: brick_stairs -> bricks
            if b.endswith("_wall"):
                w = b[:-5]   # oak_wall_sign -> oak, light_gray_wall_banner -> light_gray
                yield w + "_planks"
                yield w + "_wool"
            yield b + "_wool"  # white_bed -> white_wool
            if b in WOOD_COLORS:
                yield b + "_planks"


DYE_COLORS = {"white", "orange", "magenta", "light_blue", "yellow", "lime", "pink",
              "gray", "light_gray", "cyan", "purple", "blue", "brown", "green",
              "red", "black", "bone"}


SIDE_OVERRIDES = {
    # blocks with dedicated side textures
    "grass_block": "grass_block_side",
    "grass_block_snow": "grass_block_side",
    "mycelium": "mycelium_side",
    "podzol": "podzol_side",
    "snow": "snow_side",
    "farmland": "farmland_side",
    "dirt_path": "dirt_path_side",
    "stone": "stone",
    "cobblestone": "cobblestone",
    "stone_bricks": "stone_bricks",
    "mossy_cobblestone": "mossy_cobblestone",
    "mossy_stone_bricks": "mossy_stone_bricks",
    "deepslate": "deepslate",
    "cobbled_deepslate": "cobbled_deepslate",
    "deepslate_bricks": "deepslate_bricks",
    "deepslate_tiles": "deepslate_tiles",
    "polished_deepslate": "polished_deepslate",
    "tuff": "tuff",
    "calcite": "calcite",
    "dripstone_block": "dripstone_block",
    "blackstone": "blackstone",
    "polished_blackstone": "polished_blackstone",
    "basalt": "basalt",
    "polished_basalt": "polished_basalt",
    "smooth_basalt": "smooth_basalt",
    "netherrack": "netherrack",
    "nether_bricks": "nether_bricks",
    "red_nether_bricks": "red_nether_bricks",
    "end_stone": "end_stone",
    "end_stone_bricks": "end_stone_bricks",
    "purpur_block": "purpur_block",
    "quartz_block": "quartz_block_side",
    "quartz_bricks": "quartz_bricks",
    "sandstone": "sandstone",
    "red_sandstone": "red_sandstone",
    "prismarine": "prismarine",
    "prismarine_bricks": "prismarine_bricks",
    "dark_prismarine": "dark_prismarine",
    "mud_bricks": "mud_bricks",
    "packed_mud": "packed_mud",
    # wood logs have side textures
    "oak_log": "oak_log",
    "spruce_log": "spruce_log",
    "birch_log": "birch_log",
    "jungle_log": "jungle_log",
    "acacia_log": "acacia_log",
    "dark_oak_log": "dark_oak_log",
    "mangrove_log": "mangrove_log",
    "cherry_log": "cherry_log",
    "bamboo_block": "bamboo_block",
    "crimson_stem": "crimson_stem",
    "warped_stem": "warped_stem",
    "stripped_oak_log": "stripped_oak_log",
    "stripped_spruce_log": "stripped_spruce_log",
    "stripped_birch_log": "stripped_birch_log",
    "stripped_jungle_log": "stripped_jungle_log",
    "stripped_acacia_log": "stripped_acacia_log",
    "stripped_dark_oak_log": "stripped_dark_oak_log",
    "stripped_mangrove_log": "stripped_mangrove_log",
    "stripped_cherry_log": "stripped_cherry_log",
    "stripped_bamboo_block": "stripped_bamboo_block",
    "stripped_crimson_stem": "stripped_crimson_stem",
    "stripped_warped_stem": "stripped_warped_stem",
    # planks
    "oak_planks": "oak_planks",
    "spruce_planks": "spruce_planks",
    "birch_planks": "birch_planks",
    "jungle_planks": "jungle_planks",
    "acacia_planks": "acacia_planks",
    "dark_oak_planks": "dark_oak_planks",
    "mangrove_planks": "mangrove_planks",
    "cherry_planks": "cherry_planks",
    "bamboo_planks": "bamboo_planks",
    "crimson_planks": "crimson_planks",
    "warped_planks": "warped_planks",
    # bricks etc.
    "bricks": "bricks",
    "nether_brick_fence": "nether_bricks",
    "stone_brick_fence": "stone_bricks",
    "brick_fence": "bricks",
    # misc
    "hay_block": "hay_block_side",
    "bone_block": "bone_block_side",
    "dried_kelp_block": "dried_kelp_block_side",
    "melon": "melon_side",
    "pumpkin": "pumpkin_side",
    "carved_pumpkin": "pumpkin_side",
    "jack_o_lantern": "pumpkin_side",
    "cactus": "cactus_side",
    "bamboo": "bamboo",
    "sugar_cane": "sugar_cane",
    "ladder": "ladder",
    "vine": "vine",
    "scaffolding": "scaffolding_side",
    "target": "target_side",
    "lodestone": "lodestone_side",
    "respawn_anchor": "respawn_anchor_side0",
    "ancient_debris": "ancient_debris_side",
    "reinforced_deepslate": "reinforced_deepslate_side",
    "chain": "chain",
}


def side_texture_candidates(base):
    """Ordered candidate texture names for the side view of a block."""
    if base in SIDE_OVERRIDES:
        yield SIDE_OVERRIDES[base]
    yield base + "_side"
    yield base
    for suffix in ("_slab", "_stairs", "_wall", "_fence_gate", "_fence", "_button",
                   "_pressure_plate", "_carpet", "_sign", "_hanging_sign", "_head",
                   "_banner", "_bed", "_trapdoor", "_torch", "_door"):
        if base.endswith(suffix):
            b = base[:-len(suffix)]
            yield b
            yield b + "s"
            if b in WOOD_COLORS:
                yield b + "_planks"


class TextureSet:
    def __init__(self, root, photo_dirs=None):
        d = Path(root) / "block"
        self._textures = {}
        if d.is_dir():
            for p in d.glob("*.png"):
                try:
                    self._textures[p.stem] = Image.open(p).convert("RGBA")
                except Exception:
                    pass
        # custom artwork wins over vanilla sprites (both top and side views)
        if photo_dirs is None:
            here = Path(root)
            photo_dirs = [Path.cwd(), here, here.parent]
        overrides = load_photo_overrides(photo_dirs)
        self._textures.update(overrides)
        self.photos = list(overrides)
        self._cache = {}

    @property
    def count(self):
        return len(self._textures)

    def get(self, name):
        base = name.split(":")[-1]
        if base not in self._cache:
            found = None
            for cand in texture_candidates(base):
                img = self._textures.get(cand)
                if img is not None:
                    tint = TINTS.get(base)
                    found = apply_tint(img, tint) if tint else img
                    break
            self._cache[base] = found
        return self._cache[base]

    def get_side(self, name):
        """Get side-view texture for a block (for sidebar display).

        Falls back to the top texture: plants, campfires, panes and entity
        blocks (beds/signs/banners) have no dedicated side PNG.
        """
        side = self._get_raw_side(name)
        return side if side is not None else self.get(name)

    def _get_raw_side(self, name):
        base = name.split(":")[-1]
        cache_key = base + "|side"
        if cache_key not in self._cache:
            found = None
            for cand in side_texture_candidates(base):
                img = self._textures.get(cand)
                if img is not None:
                    tint = TINTS.get(base)
                    found = apply_tint(img, tint) if tint else img
                    break
            self._cache[cache_key] = found
        return self._cache[cache_key]


def cover_crop(img, w, h):
    """Scale-and-crop img to exactly cover w x h (aspect preserved)."""
    iw, ih = img.size
    k = max(w / iw, h / ih)
    nw, nh = max(w, int(iw * k)), max(h, int(ih * k))
    im = img.resize((nw, nh), Image.LANCZOS)
    x, y = (nw - w) // 2, (nh - h) // 2
    return im.crop((x, y, x + w, y + h))
