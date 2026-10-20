# litematic2pdf

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey)
![Output](https://img.shields.io/badge/output-PDF-orange)

**Convert Litematica `.litematic` schematics into layer-by-layer PDF build guides.**

</div>

---

litematic2pdf reads a schematic file created in the [Litematica](https://www.curseforge.com/minecraft/mc-mods/litematica) mod and generates a structured PDF instructions document. Each page renders one horizontal construction layer viewed from above, accompanied by the complete block list for that layer with previews and counts. The document concludes with a consolidated materials summary — suitable for printing and offline reference during construction.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Graphical interface](#graphical-interface)
  - [Command line](#command-line)
  - [Command-line options](#command-line-options)
  - [Examples](#examples)
- [PDF contents](#pdf-contents)
- [Packaging as an executable](#packaging-as-an-executable)
- [Self-test](#self-test)
- [Project layout](#project-layout)
- [Notes](#notes)
- [Limitations](#limitations)

## Features

| | |
|---|---|
| **Cover page** | Custom title and description, statistics card, a preview of the 8 most-used materials rendered with in-game textures, and a symbol legend |
| **Layer-by-layer build** | One layer per page, ordered bottom-up: complete a level, then turn the page |
| **Faithful rendering** | Blocks are drawn with actual game textures; leaves and grass are tinted green, water blue, exactly as displayed in game |
| **Stair and slab profiles** | Stairs and slabs are visually distinct from full blocks: lowered stair sides are shaded and a red arrow indicates the block's facing (including inner/outer corner pieces) |
| **Adaptive rendering** | Raster quality scales with layer dimensions (4–24 px per block); page size grows automatically: ≤64 blocks → A4, ≤140 → A3, larger → A2. Tall builds are printed in portrait orientation |
| **Running header** | Every page carries the guide title on the left, "Layer-by-layer Build Guide" on the right, and page numbers |
| **Watermark** | Configurable multi-line diagonal watermark behind the build plus a signature mark in the corner; can be replaced or fully disabled |
| **Multi-region schematics** | A `.litematic` with several separate constructions lists them automatically and allows selecting which regions to process |

## Installation

Requires Python 3.9 or later.

```bash
pip install -r requirements.txt       # dependencies (once)
python fetch_textures.py              # download vanilla block textures (once, ~1100 files)
```

Run directly from the checkout:

```bash
python guide.py                       # graphical interface
python make_pdf.py your_scheme.litematic   # command line
```

Or install as a package to expose the console scripts `litematic2pdf`, `litematic2pdf-gui` and `litematic2pdf-fetch` system-wide:

```bash
pip install -e .
litematic2pdf your_scheme.litematic
litematic2pdf-gui
```

Textures are stored in `textures/` and are not part of the repository — they are downloaded once by `fetch_textures.py`. Without them, blocks are rendered with flat, deterministic colors instead.

## Usage

### Graphical interface

```bash
python guide.py
```

The interface provides schematic selection, guide title and description fields, region selection, cut-axis choice, watermark settings, and a one-click PDF generation with direct open of the result.

### Command line

```bash
python make_pdf.py villager_house.litematic
python make_pdf.py huge.litematic --axis z --regions kitchen
python make_pdf.py build.litematic --title "Modern house" --page a3
```

### Command-line options

| Option | Description |
|---|---|
| `-o file.pdf` | output file name |
| `--title "..."` / `--description "..."` | cover page title and description |
| `--scale N` | pixels per block (default: 4–24, auto-selected from build dimensions) |
| `--max-size N` | hard limit on layer raster size in px (default: 8192) |
| `--page auto\|a4\|a3\|a2` | paper size (default: auto-selected from the build) |
| `--axis y\|x\|z` | cut axis: `y` horizontal layers, `x`/`z` vertical side sections |
| `--list-regions` | print the scheme's regions and exit |
| `--regions kitchen,cellar` | process only the listed regions |
| `--no-grid` | omit the coordinate grid |
| `--watermark "text"` / `--no-watermark` | replace or disable the default page watermark |
| `--background image.jpg` | page background image (default: `background.png` near the schematic if present) |
| `--textures-dir path` | custom block texture directory |
| `--force` | bypass the schematic size guard (2 million blocks) |
| `--debug` | show a full traceback on unexpected errors |
| `--version` | print version |

## PDF contents

- One page per layer: caption in the form `Layer Y=3 (4/9 from bottom) — 65 blocks` and the layer's complete block list with side/top previews (e.g. "23x Spruce Planks").
- Real block textures; the lantern is drawn from `lantern.png` (resolved next to the program or schematic) with a transparent background and fitted into its cell.
- Coordinate grid with edge labels; on dense grids, labels are printed every 5/10/25 cells to remain readable.
- Layers with more than 29 distinct block types show the top 29 plus "…and N more types".
- Large layers are encoded to PNG incrementally, so memory use stays flat (measured: a hollow 260×200×40-block build — 11 s, 406 KB PDF, 42 A2 pages).
- The generated PDF is in English; pages are numbered and carry a running header.

## Packaging as an executable

```bash
pip install pyinstaller
pyinstaller --noconfirm litematic2pdf.spec
```

The resulting executable is written to `dist\`. Bundled payload includes block textures, fonts, and the demo schematic; all data is referenced from `litematic2pdf.spec`, so the built exe requires no external files.

Equivalent single-line invocation, when a spec file is not desired:

```bash
pyinstaller --noconfirm --onefile --windowed --paths src ^
  --add-data "textures;textures" --add-data "lantern.png;." ^
  --add-data "villager_house.litematic;." guide.py
```

## Self-test

<details>
<summary><b>Verifying an assembled build</b></summary>

The bundled demo schematic (a small villager house) enables a headless self-test of the executable:

```bash
dist\litematic2pdf.exe --selftest
```

It runs the full pipeline internally and reports success — if a PDF is produced, the build is functional.

</details>

## Project layout

<details>
<summary><b>File tree</b></summary>

```
litematic2pdf/
├── guide.py                    — GUI launcher (and exe entry point)
├── make_pdf.py                 — CLI launcher
├── fetch_textures.py           — texture download launcher
├── pyproject.toml              — package metadata, dependencies, console scripts
├── requirements.txt            — runtime dependencies
├── lantern.png                 — lantern image used for schematic rendering
├── litematic2pdf.spec          — PyInstaller build specification
├── villager_house.litematic    — demo schematic (self-test, exe bundling)
├── src/litematic2pdf/
│   ├── __init__.py             — package constants and version
│   ├── __main__.py             — enables `python -m litematic2pdf`
│   ├── blocks.py               — block palette, tinting, naming, stair/slab profiles
│   ├── textures.py             — top/side texture resolution, overrides
│   ├── schema.py               — .litematic (NBT) parsing, regions, slicing
│   ├── render.py               — layer rasterization: blocks, shadows, arrows, grid
│   ├── fonts.py                — primary and signature (handwritten) fonts
│   ├── pdf.py                  — cover, layer pages, materials summary, watermark
│   ├── cli.py                  — argument parsing and the main pipeline
│   ├── gui.py                  — Tkinter interface panel
│   ├── fetch.py                — vanilla texture downloader
│   └── errors.py               — user-facing error types
└── textures/block/             — textures (not in git; downloaded via fetch_textures.py)
```

</details>

<details>
<summary><b>Pipeline overview</b></summary>

1. `schema.py` parses the NBT structure, locates regions and applies the chosen cut axis;
2. `render.py` rasterizes each layer to PNG as it goes, keeping peak memory flat;
3. `blocks.py` / `textures.py` resolve actual top/side textures and tint colors;
4. `pdf.py` assembles the cover, layer pages and materials sheet (ReportLab);
5. `gui.py` wraps `cli.py` for point-and-click use.

</details>

> Note: the launchers are named `guide.py` / `make_pdf.py` rather than `litematic2pdf.py` — a root-level file sharing its name with the package would shadow it during import and exe assembly.

## Notes

**Legacy or "negative" region sizing** — handled automatically; both older and current Litematica `Size`/`Position` formats are supported.

**Vertical (side) sections** — `--axis x` or `--axis z` render a cut suitable for facades and walls.

**Multiple constructions in one schematic** — `--list-regions` enumerates them; `--regions kitchen,cellar` restricts output to the selected ones.

**Flat colors instead of textures** — simply skip `fetch_textures.py`; unknown blocks receive stable dedicated colors.

**Custom page background** — place a `background.png` next to the schematic or pass `--background photo.jpg`; the image underlays all pages.

## Limitations

- Minecraft textures are the property of Mojang; this tool downloads them from an unofficial asset mirror. Personal use only — do not redistribute.
- One page equals one layer; very large builds produce proportionally thicker PDFs. This is intentional and convenient during construction.
- Orientation in top-down view: north at the top of the page, east on the right.
- The Windows executable is unsigned; SmartScreen will warn on first launch.
