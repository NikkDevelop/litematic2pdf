"""Block palettes, biome tints, human names and stair/slab shapes."""
import colorsys
import zlib

from PIL import Image

AIR_NAMES = {"air", "cave_air", "void_air", "structure_void"}


BEIGE = (238, 230, 212)


WOOD_COLORS = {
    "oak": "#b8945f", "spruce": "#8a6b45", "birch": "#d8c394",
    "jungle": "#a97c50", "acacia": "#b57b4c", "dark_oak": "#5b452c",
    "mangrove": "#7d5642", "cherry": "#e2b7b3", "bamboo": "#cfa35f",
    "crimson": "#7d3c3c", "warped": "#3f8a78", "pale_oak": "#d8d3bd",
}


COLORS = {
    # stone family
    "stone": "#7f7f7f", "cobblestone": "#777777", "stone_bricks": "#8a8a8a",
    "mossy_cobblestone": "#6f7f6a", "mossy_stone_bricks": "#6f7f6a",
    "cracked_stone_bricks": "#7c7c7c", "chiseled_stone_bricks": "#888888",
    "smooth_stone": "#929292", "granite": "#9a6f5a", "polished_granite": "#a07963",
    "diorite": "#c2c2c2", "polished_diorite": "#c8c8c8",
    "andesite": "#8a8a8a", "polished_andesite": "#949494",
    "deepslate": "#5b5b5f", "cobbled_deepslate": "#56565a",
    "deepslate_bricks": "#5f5f63", "cracked_deepslate_bricks": "#5a5a5e",
    "deepslate_tiles": "#5b5b5f", "cracked_deepslate_tiles": "#57575b",
    "polished_deepslate": "#616166", "chiseled_deepslate": "#57575c",
    "reinforced_deepslate": "#505055", "tuff": "#6f6f6a", "calcite": "#d8d8d0",
    "dripstone_block": "#9a8a6f", "amethyst_block": "#8a5fc8",
    "budding_amethyst": "#8a5fc8", "smooth_basalt": "#4a4a4f",
    "basalt": "#4a4a4f", "polished_basalt": "#55555a",
    "blackstone": "#2b2b2b", "polished_blackstone": "#333333",
    "blackstone_bricks": "#2f2f2f", "polished_blackstone_bricks": "#363636",
    "chiseled_polished_blackstone": "#333338", "cracked_polished_blackstone_bricks": "#313131",
    "gilded_blackstone": "#3a3a33", "netherrack": "#6f3a32",
    "nether_bricks": "#2f2523", "red_nether_bricks": "#4f2323",
    "chiseled_nether_bricks": "#2f2523", "cracked_nether_bricks": "#2c2220",
    "netherite_block": "#3b3b3b", "ancient_debris": "#5f4630",
    "obsidian": "#17121f", "crying_obsidian": "#3a2f5f",
    "end_stone": "#dad8b8", "end_stone_bricks": "#c9c7a8",
    "purpur_block": "#b08ab0", "purpur_pillar": "#b08ab0",
    "purpur_slab": "#b08ab0", "purpur_stairs": "#b08ab0",
    "purpur": "#b08ab0", "smooth_quartz": "#e8e4dc",
    "quartz_block": "#e8e4dc", "quartz_pillar": "#e8e4dc",
    "chiseled_quartz_block": "#e0dcd4", "quartz_bricks": "#e0dcd4",
    "sandstone": "#d0c390", "chiseled_sandstone": "#d0c390",
    "cut_sandstone": "#d8c99a", "smooth_sandstone": "#d8c99a",
    "red_sandstone": "#b5623a", "chiseled_red_sandstone": "#b5623a",
    "cut_red_sandstone": "#bd6f3a", "smooth_red_sandstone": "#bd6f3a",
    "prismarine": "#5f9a8a", "prismarine_bricks": "#4f8a7a",
    "dark_prismarine": "#3f5f55", "sea_lantern": "#d0f0f8",
    "mud_bricks": "#6f5f52", "packed_mud": "#7d6452",
    # wood / leaves
    "oak_planks": "#b8945f", "spruce_planks": "#8a6b45", "birch_planks": "#d8c394",
    "jungle_planks": "#a97c50", "acacia_planks": "#b57b4c", "dark_oak_planks": "#5b452c",
    "cherry_planks": "#e2b7b3", "mangrove_planks": "#7d5642", "bamboo_planks": "#cfa35f",
    "crimson_planks": "#7d3c3c", "warped_planks": "#3f8a78",
    "oak_log": "#6f5738", "spruce_log": "#4f3f26", "birch_log": "#b5a17c",
    "jungle_log": "#5d4c33", "acacia_log": "#79503a", "dark_oak_log": "#3b2f1e",
    "cherry_log": "#4a352e", "mangrove_log": "#4f3d2c", "bamboo_block": "#5d4c2f",
    "crimson_stem": "#5f3a4a", "warped_stem": "#2f5f55",
    "stripped_oak_log": "#8a6f47", "stripped_spruce_log": "#6a5333",
    "stripped_birch_log": "#c8b48c", "stripped_jungle_log": "#7d6740",
    "stripped_acacia_log": "#9a6a45", "stripped_dark_oak_log": "#4f3d28",
    "stripped_cherry_log": "#6a4f40", "stripped_mangrove_log": "#6a5540",
    "stripped_bamboo_block": "#7d6f4a", "stripped_crimson_stem": "#7d4a5f",
    "stripped_warped_stem": "#3f7a6a",
    "oak_leaves": "#3d7a3d", "spruce_leaves": "#2f5f30", "birch_leaves": "#5f8a3f",
    "jungle_leaves": "#3f8a3a", "acacia_leaves": "#5f8a3f", "dark_oak_leaves": "#2f5f2f",
    "cherry_leaves": "#e8a3ab", "mangrove_leaves": "#3f7a3a", "azalea_leaves": "#4a7a2f",
    "flowering_azalea_leaves": "#4a7a2f",
    # natural
    "dirt": "#7a5230", "coarse_dirt": "#6a4628", "grass_block": "#5f8f3f",
    "grass_path": "#9a8a4f", "podzol": "#5f4a2a", "mycelium": "#7a6a70",
    "rooted_dirt": "#6f4a2c", "mud": "#4a3a4f", "clay": "#8a92a5",
    "sand": "#d8cf9a", "red_sand": "#bd6f3a", "gravel": "#8a8a8a",
    "soul_sand": "#5f4a3f", "soul_soil": "#55463a",
    "snow_block": "#f0f0f0", "snow": "#f0f0f8",
    "ice": "#a8d0e8", "packed_ice": "#9ab8d0", "blue_ice": "#6fa0c8",
    "sponge": "#c8c826", "wet_sponge": "#b8b830", "dried_kelp_block": "#4f3a24",
    "bone_block": "#d8d2b8", "hay_block": "#d9b43f",
    "pumpkin": "#e07a1f", "carved_pumpkin": "#e07a1f", "jack_o_lantern": "#e8a020",
    "melon": "#8fc04f", "mushroom_stem": "#c8c0b0", "red_mushroom_block": "#d05050",
    "brown_mushroom_block": "#a0784f",
    "cactus": "#3f8f3a", "sugar_cane": "#6faf3f", "bamboo": "#8faf4f",
    "lily_pad": "#2f7a2f", "scaffolding": "#cfb173",
    "ladder": "#8a6a3f", "vine": "#3f7a3f",
    # ores & raw blocks
    "coal_ore": "#575757", "deepslate_coal_ore": "#4f4f4f",
    "iron_ore": "#a08060", "deepslate_iron_ore": "#8a6f52",
    "copper_ore": "#b5754a", "deepslate_copper_ore": "#9a6640",
    "gold_ore": "#c8a020", "deepslate_gold_ore": "#b08f1a",
    "redstone_ore": "#b02f2f", "deepslate_redstone_ore": "#9a2828",
    "lapis_ore": "#3a4fb0", "deepslate_lapis_ore": "#33449a",
    "emerald_ore": "#2fa060", "deepslate_emerald_ore": "#298a55",
    "diamond_ore": "#4fd0d8", "deepslate_diamond_ore": "#45b8bf",
    "nether_gold_ore": "#c8a020", "nether_quartz_ore": "#b09a7a",
    "raw_iron_block": "#c8a080", "raw_gold_block": "#d0a53f", "raw_copper_block": "#b5754a",
    "coal_block": "#242424", "iron_block": "#d8d8d8", "gold_block": "#f6b600",
    "diamond_block": "#3fb7c6", "emerald_block": "#17dd62", "lapis_block": "#2648a8",
    "copper_block": "#b87333",
    "exposed_copper": "#9a8a6f", "weathered_copper": "#7f9a80", "oxidized_copper": "#4f9a8a",
    # wool
    "white_wool": "#e9e9e9", "orange_wool": "#f07613", "magenta_wool": "#bd44b3",
    "light_blue_wool": "#3aaaf9", "yellow_wool": "#f8c627", "lime_wool": "#70b919",
    "pink_wool": "#ed8dac", "gray_wool": "#3e4447", "light_gray_wool": "#8d8d8d",
    "cyan_wool": "#158991", "purple_wool": "#792aac", "blue_wool": "#35399d",
    "brown_wool": "#724728", "green_wool": "#546d1b", "red_wool": "#a12722",
    "black_wool": "#141519",
    # concrete
    "white_concrete": "#cfcfcf", "orange_concrete": "#e04e12", "magenta_concrete": "#a02bb4",
    "light_blue_concrete": "#2a9de0", "yellow_concrete": "#e5c912", "lime_concrete": "#5fbf18",
    "pink_concrete": "#e87b9e", "gray_concrete": "#3e3e3e", "light_gray_concrete": "#858585",
    "cyan_concrete": "#10878f", "purple_concrete": "#6f2aa0", "blue_concrete": "#2d3aa8",
    "brown_concrete": "#664322", "green_concrete": "#4f6a1e", "red_concrete": "#9c2626",
    "black_concrete": "#121212",
    # terracotta
    "terracotta": "#95644a", "white_terracotta": "#d0c8ba", "orange_terracotta": "#a65224",
    "magenta_terracotta": "#95576b", "light_blue_terracotta": "#6e7b9a",
    "yellow_terracotta": "#ba8524", "lime_terracotta": "#6a7033",
    "pink_terracotta": "#a4565f", "gray_terracotta": "#37393a",
    "light_gray_terracotta": "#857565", "cyan_terracotta": "#575b58",
    "purple_terracotta": "#6d4654", "blue_terracotta": "#4a3f59",
    "brown_terracotta": "#4d3226", "green_terracotta": "#4c522b",
    "red_terracotta": "#8f3f2f", "black_terracotta": "#2a2522",
    "white_glazed_terracotta": "#b8b8c0", "orange_glazed_terracotta": "#e05f25",
    "magenta_glazed_terracotta": "#b75a94", "light_blue_glazed_terracotta": "#5aa0e0",
    "yellow_glazed_terracotta": "#e8c030", "lime_glazed_terracotta": "#78c83a",
    "pink_glazed_terracotta": "#e895a8", "gray_glazed_terracotta": "#6a6a6a",
    "light_gray_glazed_terracotta": "#9a9a9a", "cyan_glazed_terracotta": "#2f9aa0",
    "purple_glazed_terracotta": "#8f3aa8", "blue_glazed_terracotta": "#3f6ae0",
    "brown_glazed_terracotta": "#8f5f30", "green_glazed_terracotta": "#4f9a30",
    "red_glazed_terracotta": "#c83a30", "black_glazed_terracotta": "#2a2a2a",
    # redstone & mechanisms
    "redstone_block": "#e01616", "redstone_lamp": "#9a6a3a",
    "piston": "#8a8a8a", "sticky_piston": "#6f9a6f", "observer": "#3a3a3a",
    "dispenser": "#8a8a8a", "dropper": "#7a7a7a", "hopper": "#5f5f5f",
    "rail": "#6f6f6f", "powered_rail": "#b8523a", "detector_rail": "#6f6f6f",
    "activator_rail": "#b8523a", "tnt": "#e03232", "target": "#c8c8c8",
    "lever": "#8a8a8a", "tripwire_hook": "#7a7a7a", "tripwire": "#cfcfc0",
    "daylight_detector": "#8a8a8a", "iron_trapdoor": "#9a9a9a",
    "iron_door": "#9a9a9a", "iron_bars": "#b0b0b0", "chain": "#9a9a9a",
    "lantern": "#e0c078", "soul_lantern": "#5f8a8f", "torch": "#d0b060",
    "soul_torch": "#4f8a8f", "glowstone": "#e8c678", "shroomlight": "#ed7d3a",
    "magma_block": "#e07a3a", "slime_block": "#7fbf4a", "honey_block": "#f0a030",
    "honeycomb_block": "#e8a028",
    # misc materials
    "bookshelf": "#8a6a3f", "chiseled_bookshelf": "#8a6a3f", "crafting_table": "#8a6a3f",
    "furnace": "#8a8a8a", "blast_furnace": "#6f6f6f", "smoker": "#7a6a5f",
    "chest": "#8a6a3f", "trapped_chest": "#8a6a30", "barrel": "#6f4f2f",
    "composter": "#7a5a35", "cauldron": "#5f5f5f", "anvil": "#3a3a3a",
    "chipped_anvil": "#3a3a3a", "damaged_anvil": "#3a3a3a", "grindstone": "#55555a",
    "stonecutter": "#888888", "enchanting_table": "#4f2f5f",
    "ender_chest": "#2f4f3f", "beacon": "#7fdbdf",
    "end_portal_frame": "#3f6f2f", "dragon_egg": "#1f1f2f",
    "respawn_anchor": "#4a3a8f", "lodestone": "#8a8a9a",
    # corals
    "tube_coral_block": "#d04050", "brain_coral_block": "#e07aa0",
    "bubble_coral_block": "#c060c0", "fire_coral_block": "#d03030",
    "horn_coral_block": "#d8c84f", "dead_tube_coral_block": "#6f6f6a",
    "dead_brain_coral_block": "#6f6f6a", "dead_bubble_coral_block": "#6f6f6a",
    "dead_fire_coral_block": "#6f6f6a", "dead_horn_coral_block": "#6f6f6a",
    # nether plants
    "crimson_fungus": "#d04040", "warped_fungus": "#3fc8a0",
    "crimson_roots": "#b03030", "warped_roots": "#2f9a7f",
    "nether_wart_block": "#6f1f1f", "warped_wart_block": "#2f8a7a",
    "nether_wart": "#9a3030",
    # flowers / plants
    "poppy": "#dd2b2b", "dandelion": "#ffdf1f", "cornflower": "#4f6fd8",
    "lily_of_the_valley": "#e8e8e8", "azure_bluet": "#e8e8d8",
    "blue_orchid": "#4f9ad8", "allium": "#c878c8", "orange_tulip": "#e07a2f",
    "pink_tulip": "#e89ab0", "red_tulip": "#cc3f3f", "white_tulip": "#e8e8e8",
    "oxeye_daisy": "#e8e8e0", "wither_rose": "#2a2a2a",
    "sunflower": "#e8c020", "lilac": "#b878c0", "rose_bush": "#d03030",
    "peony": "#e890b0", "tall_grass": "#4f8f3f", "grass": "#5f9f4a",
    "fern": "#4f8f3f", "large_fern": "#4f8f3f",
    "torchflower": "#e0782f", "pitcher_plant": "#4f8f3f",
    "crop": "#c8c836", "wheat": "#c8c836", "carrots": "#e88030",
    "potatoes": "#c8b858", "beetroots": "#c03030",
    "sweet_berry_bush": "#3f8f3f",
    "frogspawn": "#4f8f6f", "ochre_froglight": "#e5cf6a",
    "verdant_froglight": "#71c87e", "pearlescent_froglight": "#c29fd8",
    # entity-rendered blocks without block textures
    "skeleton_skull": "#d8d2b8", "wither_skeleton_skull": "#6a6a62",
    "zombie_head": "#5f8a3f", "creeper_head": "#3f8f3a", "player_head": "#b8946f",
    "dragon_head": "#2a2a1f", "piglin_head": "#c98d78",
}


TRANSPARENT = {
    "glass": ("#c8e0e8", 140), "glass_pane": ("#c8e0e8", 160),
    "water": ("#3f6fd8", 150), "lava": ("#e04a1f", 210),
    "powder_snow": ("#e8f0f8", 180),
}


for _c in ("white", "orange", "magenta", "light_blue", "yellow", "lime", "pink",
           "gray", "light_gray", "cyan", "purple", "blue", "brown", "green",
           "red", "black"):
    base = {
        "white": "#e8eef2", "orange": "#f09a3f", "magenta": "#d070d0",
        "light_blue": "#8fc8f0", "yellow": "#f0e070", "lime": "#90d060",
        "pink": "#f0a0b8", "gray": "#707070", "light_gray": "#a8a8a8",
        "cyan": "#70c8d0", "purple": "#a060c8", "blue": "#6090f0",
        "brown": "#806040", "green": "#70a040", "red": "#e05050", "black": "#303030",
    }[_c]
    TRANSPARENT[f"{_c}_stained_glass"] = (base, 160)
    TRANSPARENT[f"{_c}_stained_glass_pane"] = (base, 180)


FOLIAGE = "#48b518"


GRASS = "#91bd59"


TINTS = {
    "oak_leaves": FOLIAGE, "jungle_leaves": FOLIAGE, "acacia_leaves": FOLIAGE,
    "dark_oak_leaves": FOLIAGE, "mangrove_leaves": FOLIAGE,
    "spruce_leaves": "#619961", "birch_leaves": "#80a755",
    "pale_oak_leaves": "#a3ab84",
    "grass_block": GRASS, "grass": GRASS, "short_grass": GRASS,
    "tall_grass": GRASS, "fern": GRASS, "large_fern": GRASS,
    "vine": FOLIAGE, "lily_pad": FOLIAGE,
    "water": "#3f76e4",
    "redstone_wire": "#e9080c",
}


def hex_to_rgb(hx):
    hx = hx.lstrip("#")
    return tuple(int(hx[i:i + 2], 16) for i in (0, 2, 4))


def apply_tint(img, tint):
    """Multiply an RGBA image by a tint color (like Minecraft biome colors)."""
    tr, tg, tb = hex_to_rgb(tint)
    r, g, b, a = img.split()
    r = r.point(lambda v: v * tr // 255)
    g = g.point(lambda v: v * tg // 255)
    b = b.point(lambda v: v * tb // 255)
    return Image.merge("RGBA", (r, g, b, a))


def resolve_color(name):
    """Return (r, g, b) or None for air. Deterministic for unknown blocks."""
    name = name.split(":")[-1]
    if name in AIR_NAMES:
        return None
    if name in COLORS:
        return hex_to_rgb(COLORS[name])
    if name in TRANSPARENT:
        rgb, alpha = TRANSPARENT[name]
        r, g, b = hex_to_rgb(rgb)
        a = alpha / 255.0
        return (int(r * a + 255 * (1 - a)), int(g * a + 255 * (1 - a)),
                int(b * a + 255 * (1 - a)))
    # 'stripped_*' -> base wood color
    if name.startswith("stripped_") and name[9:] in COLORS:
        return hex_to_rgb(COLORS[name[9:]])
    # 'waxed_/exposed_/...' prefixes -> strip and retry
    for prefix in ("waxed_", "oxidized_", "weathered_", "exposed_", "chiseled_",
                   "cracked_", "mossy_", "smooth_", "cut_", "polished_"):
        if name.startswith(prefix):
            sub = name[len(prefix):]
            if sub in COLORS:
                return hex_to_rgb(COLORS[sub])
            if sub.startswith("stripped_") and sub[9:] in COLORS:
                return hex_to_rgb(COLORS[sub[9:]])
    # wood families cover stairs/slabs/fences/doors/buttons/...
    for wood, color in WOOD_COLORS.items():
        if wood in name:
            return hex_to_rgb(color)
    # block variants sharing the base block color
    for suffix in ("_stairs", "_slab", "_fence", "_fence_gate", "_door",
                   "_trapdoor", "_wall", "_button", "_pressure_plate",
                   "_pane", "_sign", "_hanging_sign", "_head", "_banner",
                   "_bed", "_candle", "_candle_cake", "_torch"):
        if name.endswith(suffix):
            base = name[:-len(suffix)]
            if base.endswith("_wall"):
                base = base[:-5]
            # plural base: brick_stairs -> bricks, stone_brick_wall -> stone_bricks
            if base + "s" in COLORS:
                return hex_to_rgb(COLORS[base + "s"])
            if base in COLORS:
                return hex_to_rgb(COLORS[base])
            if base + "_wool" in COLORS:
                return hex_to_rgb(COLORS[base + "_wool"])
    # stable fallback color (crc32, so it never changes between runs)
    h = (zlib.crc32(name.encode("utf-8")) % 360) / 360.0
    r, g, b = colorsys.hsv_to_rgb(h, 0.32, 0.78)
    return (int(r * 255), int(g * 255), int(b * 255))


_PRETTY_SPECIAL = {"tnt": "TNT"}


def pretty_name(name):
    """Human-readable display name: 'spruce_slab' -> 'Spruce Slab'."""
    if name in _PRETTY_SPECIAL:
        return _PRETTY_SPECIAL[name]
    return " ".join(w[:1].upper() + w[1:] for w in name.split("_"))


def block_shape(name, props=None):
    """Render shape for slabs/stairs, else 'full'.

    Uses block state properties from the schematic: slab 'type' (top/bottom),
    stair 'facing' (the full-height half lies on this side) and 'shape'
    (straight / inner_left.. / outer_left..) exactly as in vanilla stair models.
    """
    if name.endswith("_slab"):
        t = (props or {}).get("type", "bottom")
        if t == "double":
            return "full"
        return "slab_top" if t == "top" else "slab_bottom"
    if name.endswith("_stairs"):
        p = props or {}
        f = p.get("facing", "north")
        if f not in ("north", "south", "east", "west"):
            f = "north"
        shp = p.get("shape", "straight")
        if shp not in ("straight", "inner_left", "inner_right",
                       "outer_left", "outer_right"):
            shp = "straight"
        return f"stairs:{f}:{shp}"
    return "full"


_FACING_TURNS = {"east": 0, "south": 1, "west": 2, "north": 3}


_STAIR_BASE = {
    "straight": ({1, 2}, {0, 3}),   # tall east band, low west band
    "inner": ({1, 2, 3}, {0}),      # 3/4 tall, low NW quarter
    "outer": ({2}, {0, 1, 3}),      # tall SE quarter post only
}


def shape_parts(shape, s):
    """Cell sub-shapes as (x, y, w, h, dark).

    Top view mapping for axis y: north = up, south = down, west = left,
    east = right. Stairs are drawn from their real footprint: the full-height
    half/quadrants stay bright, the lower parts are shaded like a cast shadow,
    so the facing direction matches the schematic exactly (including
    inner/outer corner stairs via 'shape').
    """
    if shape == "full":
        return [(0, 0, s, s, False)]
    h = max(1, s // 2)
    if shape == "slab_bottom":
        return [(0, h, s, h, False)]
    if shape == "slab_top":
        return [(0, 0, s, h, False)]
    pieces = shape.split(":")
    facing = pieces[1] if len(pieces) > 1 else "north"
    shp = pieces[2] if len(pieces) > 2 else "straight"
    kind = "inner" if shp.startswith("inner") else \
        "outer" if shp.startswith("outer") else "straight"
    turn = _FACING_TURNS.get(facing, 3)
    if shp.endswith("left"):
        turn = (turn + 3) % 4  # blockstates: *_left = *_right rotated 270 cw
    tall, low = _STAIR_BASE[kind]
    # quadrant rects (local coords): index clockwise from NW
    quad = {0: (0, 0, h, h), 1: (h, 0, s - h, h),
            2: (h, h, s - h, s - h), 3: (0, h, h, s - h)}
    parts = []
    for q in sorted(tall | low):
        rx, ry, rw, rh = quad[(q + turn) % 4]
        parts.append((rx, ry, rw, rh, q in low))
    return parts
