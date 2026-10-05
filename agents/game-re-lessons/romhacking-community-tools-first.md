# Search the romhacking community for the exact game before decoding blind

**When it bites:** about to reverse-engineer an unfamiliar compression scheme or binary format for a commercial (esp. pre-2000) game — before the first entropy scan or hypothesis probe. Also: a community tool/rip/doc is already in hand and you are deciding how far to trust it.

Most such games have a romhacking/speedrun/preservation community that has already published what you are about to re-derive: standalone de/compressors reversed from disassembly, often with a same-game test suite of known-good offsets and decoded sizes — a ground-truth oracle, not a hint. This is distinct from the "other platform port" oracle (`cross-platform-decode-oracles.md`): search for *standalone community tooling* (GitHub, romhacking.net, VOGONS/XeNTaX threads, dev-community wikis), which often exists when no port or full disassembly does. It is one WebSearch; do it first, not after blind scanning stalls.

**Canonical example:** Jungle Strike (Genesis): a WebSearch for the three Strike games + "compression format disassembly" found `infval/StrikeLZSS` — an LZSS reimplementation with a per-game breakpoint (PC + source-pointer register) and a test suite of 34 compressed-block ROM offsets. All 34 decoded with the exact declared size against the project ROM, and the routine at the documented PC matched its constants (window size, initial position, control-byte refill). A multi-day blind effort became an hour of verification.

## How to search

- **Name first, then fingerprint.** If a game-name search is empty but a scan has found a concrete magic/tag/constant, search *that token* + platform (VP2 PS2: `"SLZ" OR "SLE"` found CUE's `triAce-PS2.c` with matching `#define`s). If still empty, drop every game/developer term — a fourcc can be a **toolchain** convention (VP2's `MWo3` = Metrowerks PS2 code overlay, documented on the GTA:SA modding wiki; 64-byte header matched exactly).
- **No dedicated tool ≠ no decoder.** Check multi-format collections (libxmp's ProWizard, `ancient`, texture/archive libraries). DM2 Amiga (`crawl`): `P41A` "music" was The Player 4.1A, decoded by libxmp `p40.c` `depack_p4x()`, found by searching the magic.
- **Forum attachments that 404:** fetch the raw thread HTML (not a markdown summary) and grep for the attachment id's other URL shape (VOGONS: `download/file.php?id=N`, not the displayed `download.php`). Pull *every* linked archive in a thread — original engine source and an independent fan tool cross-check each other (AESOP: Miles' `DEFS.H` + DAESOP `convert.c` converged on the same offsets as a from-scratch derivation).

## What to pull out of a found project

- **`git clone` and read source**, don't trust a web summary of its docs (EOB3/ThirdEye `res.cpp`, `cps.cpp`).
- **Prefer a self-describing rip definition** (JSON declaring addresses, strides, pointer tables, char tables) over its extractor logic or disassembly — FFIV `everything8215/ff4` `ff4-en-rip.json` decoded 12 text pools with zero disassembly. Its addresses are still **unmapped CPU addresses** (see `game-re-tooling/snes.md`).
- **When a rip locates data but the decode still fails, find the shared codec module** (`*_codec`, `romtools`, a `decode()`/`encode()` pair). FFVI-J: `text_codec.py` (~30 lines) *was* the byte-stream spec (2-byte lookup before 1-byte; `:b`/`:w` codes consume parameter bytes — `escape-code-parameter-bytes-silently-misdecoded.md`).
- **Runtime questions live in the runtime module**, not the format parser. EOB3 palette↔bitmap pairing was a hardcoded `kFirstColor[5]` VGA-DAC window table in ThirdEye's `runtime/graphics.cpp`; with it, 265/312 bitmaps got real colour.
- **A classifier is an oracle.** Multi-game tools that fingerprint inputs carry byte-pattern constants you can whole-ROM grep with no disassembly (vgmtrans `AkaoSnesScanner.cpp` per-title `FF*_VCMD_LEN_TABLE` → exact driver version in FFIV/V/VI).
- **Run self-contained extractors and diff their *output*** against your decoder (FFV `everything8215/ff5` `make rip`): it caught an MTE/icon-glyph range collision and a terminator-scan bug (`multi-byte-code-second-byte-collides-with-terminator.md`) that reading code would not.
- **A CLI that hardcodes another variant is often a few-line patch**: grep for an enum/version branch naming your variant (`fe2-intro` `AssetsRead_Amiga_Orig`, 12-line `-orig` flag, `hunter`).
- **Check coverage tables before writing "may not support platform X"** (ScummVM `detection_tables.h` had full `kPlatformAmiga` EOB1/2 entries).
- **Re-check reused repos for other assets** — a JSON-rip repo may also ship labelled `.asm` (`ff4` `sound/`, `notes/` missed by three sessions).
- **A zero-xref grep for a declared resource symbol** means the community never traced it either: grep loader-name patterns (`Tfr*Gfx`, `Load*`, `*SpriteGfx`) instead (FFV → `TfrPartyGfx`).

## How far to trust it

- **Offsets transfer only to the byte-identical binary** the tool recorded against — never "same game/engine". Phantasie I Amiga and II ST offsets worked unchanged; III's ST offsets were garbage on the Amiga build. Different binary → budget full re-derivation.
- **Script dispatch beats prose bank-maps.** FFVI monster gfx labelled "compressed" in prose; the extractor only LZSS-decodes targets ending `.lz`, and the region is raw.
- **Re-derive offsets from a doc's own cited values.** ThirdEye's `item_dat_format.md` values were right but every offset was 2 bytes off across 27 records.
- **Verify each table's record *shape* against its load routine.** `ff4` `monsterProperties` was declared flat 20-byte; real data is pointer-indexed, overlapping (gaps 10–19, one alias) with a flags byte gating optional bytes. Tell: sort the pointer-table offsets and diff — a fixed-stride table gives one gap. Named variants without a selector field (`"Default"`/`"Golbez/Anna"`) need the disassembly.
- **A supported format is not a supported file**: count the code paths (ThirdEye's GFF sequencer handles only `INTRO.GFF`).
- **A script failing end-to-end can still have right offsets** if it assumes an upstream preprocessing step (Drakengard 3 UE3 importer: counts matched `umodel`; the walk needs the author's decompressor first).
- **No test suite → re-verify byte-exact** against your own files; source comments may record real engine behaviour (Phantasie III trap-message off-by-one vs II).
- **Unlicensed or copyrighted source is a spec, not code to vendor**: clean-room reimplement, credit it, never cite scratch paths; cross-diff the two implementations' outputs. Porting C faithfully: keep `for(;;)`+`continue` as a JS `for` (`decompressor-port-loop-condition-iteration-shift.md`, `standard-codec-delegate-to-trusted-decoder-not-hand-reimplementation.md`).

**History:** ~20 recorded techniques (Jungle Strike, ceres, nicodemus, crawl, flower, valkyrie, hunter) — full detail in `_archive/romhacking-community-tools-first.md`.
