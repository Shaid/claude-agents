# Tooling — format discovery (platform-agnostic)

`Read` this when you have an unidentified blob and no format hypothesis yet:
"where does the sprite bank start", "what stride/depth is this pixel data",
"where is the name table and what encoding is it in", "is any of this
compressed". Platform-specific conventions live in the per-platform files;
this is the cross-platform toolbox and the prior-art index.

## First move: has someone already solved this game?

`game-re-lessons/romhacking-community-tools-first.md` says search the
community before decoding blind. These are the specific places to look —
hit them before writing an entropy scan:

| Source | What it holds |
|---|---|
| [QuickBMS](https://aluigi.altervista.org/quickbms.htm) script DB | Archive/container layouts for thousands of games, as readable BMS scripts. Even when you don't run QuickBMS, the script *is* the format spec |
| [XeNTaX wiki backup](https://github.com/XeNTaXBackup/XeNTaXBackup.github.io) | The defunct XeNTaX format wiki and forum, preserved. The single largest body of community format specs |
| [Just Solve the File Format Problem](http://fileformats.archiveteam.org/wiki/Game_data_files) | ArchiveTeam's format wiki, game-data section |
| [RetroReversing](https://github.com/RetroReversing/retroReversing) | Retro-specific RE resources, tools and per-console documentation |
| [GameExtractor](https://github.com/wattostudios/GameExtractor) (4,000+ games), [dexvert](https://github.com/Sembiance/dexvert) (3,700 formats), [GARbro](https://github.com/morkt/GARbro) (visual novels) | Multi-game extractors — check whether your container is already in their format list before deriving it |
| [hogsy/formats](https://github.com/hogsy/formats), [010GameTemplates](https://github.com/Nenkai/010GameTemplates), [ImHex-Patterns](https://github.com/WerWolv/ImHex-Patterns), [gameyaml](https://github.com/Herringway/gameyaml) | Binary templates — struct layouts for hundreds of games, translatable straight to C or TypeScript |

An existing tool for the exact game is worth more than a hint: it usually
comes with a test corpus of known-good offsets and decoded sizes, which is a
ground-truth oracle you can verify against, not just a starting point.

## Scriptable: ReverseBox (`pip install reversebox`)

The one genuinely agent-drivable format-discovery library found. Python,
headless, and it covers exactly the sweep you would otherwise hand-roll:

- **100+ pixel formats** decoded via `reversebox.image.ImageDecoder`, including
  indexed `PAL4`/`PAL8`/`PAL16`, `RGB565`, `RGBA8888`, BC1–BC7, ETC2, ASTC.
- **Per-platform swizzle/unswizzle** — PS2, PS3, PS4, PS5, PSP, Vita, Xbox 360,
  GameCube, Wii, Wii U, Switch, Dreamcast.
- **Decompression** wrappers — ZLIB, LZMA, LZ4, LZO, BZIP2, MIO0, RLE variants.
- **CRC/checksum** family (CRC-8/16/32/64 variants) — useful when a header
  field looks like a checksum and you want to confirm which one.
- `reversebox.io_files.file_handler.FileHandler` for structured binary reads.
- `PillowWrapper.get_pillow_image_from_rgba8888_data()` to dump a candidate
  decode straight to PNG for eyeballing.

Use it to brute-force a pixel-format hypothesis: loop candidate
`(width, format, swizzle)` triples, write each to PNG, and look. That is the
same loop the GUI tools below run interactively, but scriptable — so prefer
it, and reserve the GUIs for handing a human a question you can't settle.

## GUI tools — for a human, not for you

These are the standard tools for this work and worth naming when you ask the
user to look at something, but **you cannot drive them**. Reimplement the
technique instead; each is a short script.

| Tool | Technique to steal |
|---|---|
| [binviz](https://github.com/VelocityRa/binviz), [binocle](https://github.com/sharkdp/binocle) | **Render the blob as pixels** — one pixel per byte (or per 4 bytes as a float). Compression and encryption look like noise, padding looks flat, structured records stripe, and image data looks like an image. Fastest way to find where a bank starts and ends inside an unstructured container. ~15 lines with PIL |
| [ImageHeat](https://github.com/bartlomiejduda/ImageHeat) | Interactive width/offset/format/swizzle sweep over unknown texture data. Its engine is ReverseBox above — script that instead |
| [RAW pixels viewer](https://www.kernellabs.com/rawpixels/) | Same idea, in a browser, no install — good to hand a user a URL |
| [Monkey-Moore](https://github.com/rjricken/monkey-moore) | **Relative search**: match on the *differences between consecutive bytes* rather than absolute values, so a text table encoded as `char − 2` (or any constant offset, or a custom charset) still hits. This is the move when ASCII/Shift-JIS scans come up empty on a name table. Boyer–Moore with wildcards; trivial to reimplement |
| [Bin2Obj](https://github.com/hogsy/Bin2Obj) | Dump candidate float triples as an OBJ point cloud — vertex data becomes obvious as a recognisable shape |
| [biodiff](https://github.com/8051Enthusiast/biodiff), [bdiff](https://github.com/ethteck/bdiff) | Sequence-alignment hex diff — for comparing two builds/ports where offsets shift |

## Also worth knowing

- **[binwalk](https://github.com/ReFirmLabs/binwalk)** (CLI) — signature-scans a
  blob for embedded known formats. Cheap first pass on any container.
- **[Kaitai Struct](https://kaitai.io/)** — declarative format description that
  generates parsers in many languages. Worth it when a format is confirmed and
  several tools need to read it; overkill mid-investigation.
- **[vgmstream](https://github.com/vgmstream/vgmstream)** — 1,000+ game audio
  formats. "Try vgmstream first" applies to *any* unidentified audio blob —
  but it's worth more than identification. Its `src/meta/*.c` source is
  routinely a **stronger, more complete reference than a community 010
  Editor/binary-template** for a format's field layout, especially for
  codec-ID or version-dependent branches a template's author never
  exercised (a template scoped to "the common case" has no reason to
  document branches it never saw; vgmstream's source, maintained across a
  huge real-world corpus, usually does — see
  `format-field-width-unexercised-by-first-corpus.md`'s 4th instance,
  where vgmstream's `ktss.c` even names the exact game in a comment for
  the codec branch a template missed). And once a from-scratch decoder is
  built from that source, `vgmstream-cli`'s own decoded WAV output is a
  strong ground-truth oracle: diff your decode against its output
  sample-by-sample (not just "plays and sounds right") for the strongest
  verification bar short of the game's own executable. Official pre-built
  CLI releases are a single self-contained binary in a `.zip` — no build,
  no install, no root needed; check `~/.cache/yay/vgmstream-cli-bin/` (or
  equivalent AUR-cache path) for one before downloading a fresh copy, it's
  sometimes already sitting there from a prior session's package research.

## Negative result — what this class of resource does not cover

Checked `awesome-game-file-format-reversing` (3,357 links, 4,118 entries,
2026-08) against this account's actual targets. **It has effectively zero
Amiga, Atari ST, Apple IIGS or 68k coverage**: one Amiga entry in the whole
list (a JavaScript MOD tracker), zero Atari ST, zero IIGS, and its 35
`IFF`/`ILBM` hits are all unrelated formats that happen to share the four
letters (GameMaker's IFF, The Sims' IFF, Pangya's IFF). Its bulk is modern
PC and console — Unity, Unreal, Source, PS3/4/5, Switch, Xbox.

**Do not re-check general "awesome game format" lists hoping for an Amiga or
ST shortcut.** For those platforms the prior art lives in the Amiga demoscene
and preservation communities (EAB, aminet, the `ancient` codec corpus), not
in game-modding directories — see `game-re-tooling/amiga.md` and
`game-re-tooling/atari-st.md`.
