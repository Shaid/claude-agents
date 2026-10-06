# Powermonger (Bullfrog) — corpus notes

Project: `~/Development/powermonger`. Games: Powermonger (Amiga, classic
edition — fully worked; WW1 edition — same disk/compression scheme
confirmed, formats not yet individually re-verified). A DOS/VGA port also
has its own doc tree (`docs/powermonger/dosvga/`) using a completely
different compression scheme (Huffman `.HUF` files, not this project's
custom LZ) — not directly reusable across platforms except for the
`MAPDATA` record layout, which Viridian Games' PC-side reverse engineering
(https://viridiangames.com/2008/06/04/powermonger-map-file-format/)
independently confirmed is byte-identical to the Amiga side.

Docs: `docs/powermonger/amiga/data-structure.md` (formats),
`docs/powermonger/amiga/runprog-code.md` (68k disassembly findings),
`docs/powermonger/TODO.md` (open items).

## Solved (Amiga, classic edition)

- **Disk container**: a custom Bullfrog track-based filesystem, NOT
  AmigaDOS OFS/FFS (`xdftool` rejects it outright) — 5632-byte tracks,
  directory block at track 1 (`DIR\0`/`WAR\0` magic + fixed 16-byte
  entries). TS: `src/assets/formats/disk.ts`.
- **Two custom LZ codecs**: variant A (backward bitstream, MSB-first,
  gamma-coded values — used only inside the intro sequence `INTRODAT`) and
  variant B (backward bitstream, LSB-first-per-longword, a 3-way
  match/literal grammar with a trailer-carried checksum that must XOR to
  zero — used for every other standalone disk file, including RUN_PROG's
  own in-place self-depack stub). TS port of variant B:
  `src/assets/formats/depack-b.ts`.
- **Full-screen pictures**: raw, headerless Amiga planar bitmaps — no
  container at all, the depacked file *is* the bitmap. Five of six are
  320×200×4bpp plane-major (QAZ.PAK, END_PIC1, LOSE.PAK, WIN.PAK, and a
  taller 320×608 map-background screen, MAP.PAK); the sixth (CAPGRAPH, a
  6-portrait "choose a captain" screen) is the same size/depth but
  **word-interleaved** instead — see
  `single-image-in-uniform-corpus-uses-different-planar-layout.md`. TS:
  `src/assets/formats/screen.ts`.
- **OCS palette**: three 16-colour tables (main game / victory / defeat) in
  a 5-entry runtime work table inside `RUN_PROG`'s data segment. Not
  findable by any static byte-pattern scan — the copper list itself is
  built by a loop at runtime, not stored as a static table — see
  `runtime-built-lookup-table-defeats-static-scan.md`. Confirmed against
  six independent screenshots from lemonamiga.com (pixel-exact on static UI
  regions). TS: `src/assets/formats/palette.ts`.
- **Sprite/texture banks**: flat, fixed-stride, headerless arrays of small
  planar bitmaps. Two distinct sub-formats, not one: SPRITE16/24/32/8. are
  **masked 4bpp** (1 transparency-mask bitplane + 4 colour bitplanes, 16
  colours — not a straight 5bpp/32-colour index as first assumed), word-
  or byte-interleaved depending on width; TEXTURES is genuinely plain 4bpp
  row-interleaved (no mask plane — flat terrain swatches never need
  transparency). The masked-bank correction was cracked on SPRITE24 first
  via a shared-blit-dispatcher disassembly trace, then shown to generalize
  to its 3 siblings (same blit code family; narrower siblings' byte
  *layout* was already accidentally correct, only their bit *semantics*
  needed fixing) — see `narrow-width-masks-a-planar-layout-correction.md`.
  Sprite/texture-bank pixels index whichever screen palette is currently
  active (palette A during gameplay) — there is no separate 32-entry
  sprite palette (a byte-identical COLOR16-31 copy in the palette table
  was a red herring from the superseded model). TS:
  `src/assets/formats/sprite-bank.ts` (`decodeSpriteBank` for TEXTURES,
  kept unchanged since the DOS/VGA port's own pipeline cross-compares
  against it — see `shared-decoder-behavior-is-a-cross-platform-contract.md`;
  `decodeMaskedSpriteBank`/`MASKED_SPRITE_BANK_DIMENSIONS` for the other
  four). MAP.PAK's screen palette (A) is also now disassembly-confirmed
  (its level-select redraw loop calls the same "apply palette A" helper
  every redraw).
- **FX.PAK audio container**: not IFF/8SVX/SMUS — a small, flat,
  Bullfrog-proprietary directory of fixed-size 16-byte descriptor records
  (8 big-endian u16 words each), confirmed against RUN_PROG's own
  "trigger sound" routine. Record fields resolve via real 68k
  `(An,Dn.W)` signed-16-bit-displacement addressing from each record's own
  start; 6 of 8 fields resolve to sample-pointer-shaped offsets fed
  straight into Paula-hardware-channel-like structs (confirmed structure;
  "these are raw signed-8-bit PCM sample pointers" is corroborated by
  entropy/autocorrelation evidence but still hypothesis — no explicit
  length/sample-rate field was found). Wired into the real asset pipeline
  per the project's runtime-WebAudio-decode convention: raw depacked bytes
  staged verbatim to `public/assets/.../audio/fx.pak.bin`, a JSON sidecar
  (`data/fx.json`) lists every record + derived candidate sample byte
  range with a `playable` flag (false only for the one known-degenerate
  self-test record). See `docs/powermonger/amiga/audio-format.md`.
- **A sparse delta-patch animation format** (`END.PAK`): not a bitmap at
  all — a stream of small records patching disjoint 4-byte-aligned spans of
  a copy of another already-decoded screen's raw buffer, across 7
  cumulative (not independent-overlay) frames. See
  `cumulative-delta-frames-not-independent-overlays.md`. TS:
  `src/assets/formats/end-pak.ts`.
- **Runtime resource loader**: a 16-entry descriptor table
  (`{namePtr, loadAddr, length}`) driving a single `LoadResource(index)`
  entry point — closes the "how does each `.PAK` land in memory" question
  that had been open since the container/codec work.
- **Terrain generation — walk + smoothing (`$F860`/`$FCCA`) now
  LIVE-VERIFIED byte-exact**, not just disassembly-confirmed: a new
  `tools/musashi-verify/` harness (a bare vendored-Musashi 68000-core
  golden-model unit test — no Kickstart, no custom chips, not a live
  Amiberry capture) runs RUN_PROG's own real `$F860` code directly against
  real MAPDATA records and diffs the resulting heightfield against the TS
  port; 6/6 tested records (spanning walkLength 1024-25779, smoothPasses
  2-4) now match with 0 byte differences, after this same harness caught
  and this session fixed a real off-by-one in the TS port's walk-loop
  iteration count (`$f884`'s `dbra d7` loads the counter directly with no
  pre-decrement, so real hardware runs `walkLength + 1` iterations, not
  `walkLength` — see `docs/powermonger/amiga/runprog-code.md`'s "Musashi
  terrain-gen cross-check" section for the full derivation, the harness
  bugs hit and fixed along the way, and how to re-run/extend it). Resolves
  this project's prior "no live-emulator verification" caveat for
  terrain-gen specifically; object placement (`$B488`) and the
  terrain-type classifier (`$F912`), described next, remain
  disassembly-confirmed only, not yet run through this harness. MAPDATA's
  332-byte record layout (6-word terrain-gen param block + 40x4-byte
  object-placement table), a straight memcpy from record to game-state
  globals (the "record parse" turned out to be no parse at all — see
  `self-modifying-code-parameter-passing.md` for how the record index
  itself is passed), the master RNG (a 32-bit LCG, corrected — see
  `reverify-raw-opcode-before-porting-bitexact-algorithm.md`), the
  random-walk heightfield generator, and the smoothing pass all have real
  8-bit-wraparound arithmetic and Gauss-Seidel in-place ordering. Object
  placement (village circular stamp via a real ROM sine-table complex
  multiply, tower flattening, road DDA rasterizer) and the terrain-type
  classifier are now **both fully ported to TS**
  (`src/assets/formats/terrain-objects.ts`, `terrain-classify.ts`):
  the classifier is a **marching-squares** water/land corner classifier
  whose case-index direction a prior pass had **backwards** (see
  `classifier-case-index-direction-unverified-against-handler-semantics.md`),
  now corrected and all 16 cases' output-value formulas traced (a small
  shared library of corner-gradient formulas + flat/thresholded wrapper
  functions). The road rasterizer's height ramp turned out to only work
  for shallow slopes — a real 68000 `DIVS.W` overflow quirk with a
  well-defined outcome, not "undefined" — see
  `cpu-overflow-instruction-leaves-destination-unchanged-not-undefined.md`.
  A previously-documented road-segment entry-pairing/consumption rule was
  also found backwards and incomplete on re-derivation from raw bytes
  (corrected in `runprog-code.md`). `BITMAP.PAK` (a previously-
  "unaccounted" resource) turned out to be a canned base-terrain template
  for one specific historical map (MAPDATA record #195) — and its
  `LoadResource(7)` call, though genuinely present with a real caller, is
  itself provably unreachable in the shipped game (the one MAPDATA record
  that needs it can never be selected through the level-select UI's own
  15x13-cell grid bound, confirmed four independent ways). See
  `guarded-call-confirmed-called-but-precondition-unreachable.md` for the
  generalizable pattern. Finding all real accessors of the
  shared mask/type/height buffer family needed a full-binary displacement
  census, not a literal-address grep — see
  `literal-address-census-misses-buffer-family-aliasing.md`. TS:
  `src/assets/formats/mapdata.ts`, `terrain-gen.ts`, `terrain-objects.ts`,
  `terrain-classify.ts`.

## Entity/AI subsystem — separate investigative thread, `docs/powermonger/amiga/entity-ai.md`

Three sessions targeting `RUN_PROG_depacked.bin`'s live simulation state
(RAM-only structures, never present in any file under `data/` — see
`docs/architecture-overview.md`'s zone split). Confirmed: the entity pool
(`$77B7A`, variable-size linked records, 231 xrefs), a 23-entry per-type
update/draw dispatch, a 5-slot team-record table (`$7754C`, stride `0x13C`)
with a 6-company-slot interleaved sub-layout and a roster attach/detach
mechanism (`$222C`/`$228A`), a home-settlement population chain (`$7592A`),
and — the deepest finding — `entity.+0x1F`, a `>=75`-case "current task"
byte dispatched through a PC-relative jump table at `$144A2`. That
dispatch's only caller in the whole binary turned out to be the **real
per-frame main loop** (`$1286C`, found by tracing backward from the
dispatch site rather than forward from suspected consumers — 2 prior
sessions failed via the forward direction), applied to one **fixed** pool
offset every frame, never a walked entity — i.e. there is no generic
per-entity tick driver; ordinary entities' task codes are instead consumed
piecemeal by type handlers and by other task handlers. The same session
also found a complete, previously-unlocated **mouse/order-issuing UI
chain** (command-icon selection, a per-entity mouse hit-test with 9
confirmed call sites, a target-legality switch, and a per-team
order-staging array) by running an exhaustive literal-address census on
one *suspected UI-state global* rather than a whole-binary keyword search
for mouse/click/order terms (the keyword approach had failed twice) — see
`game-re-lessons/ui-state-global-census-beats-keyword-search.md`. TS:
`src/assets/formats/entities.ts` (documentation-as-code reference, no
binary to decode).

## Still open

A byte-count discrepancy between TEXTURES's descriptor-declared and actual
decoded size, TEXTURES's own palette-consumer trace (very likely palette A
by the same reasoning as the now-confirmed sprite banks, but not itself
disassembly-traced), FX.PAK's remaining open questions (word0's type byte,
ptrA/ptrB's role vs. ch0-3, whether a sample-rate/period field exists
anywhere, real per-event sound-trigger call sites — none found in
RUN_PROG itself, must be in overlay/level code not captured), the mapping
from `$F912`'s confirmed terrain-type output values onto specific
`TEXTURES.PAK` frame indices, 7 still-unnamed post-generation pipeline
calls, and a season/weather data-block lead — see the project's own
`docs/powermonger/TODO.md` for the live list; per this account's
convention that file is not duplicated here.

## Reusable tooling this project confirmed

`@seer-project/gfx`'s `decodePlanar` handled all three bitplane layouts
encountered (plane-major, row-interleaved, word-interleaved) with zero
format-specific decoder code — see `game-re-tooling/amiga.md`.

## Corpora-index row text formerly inline in `game-re.md`

Moved verbatim from the always-loaded agent prompt during the 2026-10 restructure.

| `~/Development/powermonger` | Powermonger (Bullfrog, Amiga classic + WW1 edition) — custom track-based disk filesystem (not AmigaDOS) + two custom LZ codecs solved; all full-screen pictures, sprite/texture banks, a delta-patch ending animation, the OCS palette table, and the runtime resource loader all solved + verified, spanning three different bitplane layouts (plane-major, row-interleaved, and — for one outlier image — word-interleaved) inside what looked like one uniform corpus. A separate live-entity/AI investigative thread (RAM-only structures, `docs/powermonger/amiga/entity-ai.md`) has confirmed the entity pool, team/company/settlement records, a >=75-case per-entity "current task" dispatch, the real per-frame main loop (its only caller), and a full mouse/order-issuing UI chain | `game-re-corpora/powermonger.md` |

## Lessons sourced from this corpus (full list)
`single-image-in-uniform-corpus-uses-different-planar-layout.md`, `runtime-built-lookup-table-defeats-static-scan.md`, `narrow-width-masks-a-planar-layout-correction.md`, `shared-decoder-behavior-is-a-cross-platform-contract.md`, `cumulative-delta-frames-not-independent-overlays.md`, `self-modifying-code-parameter-passing.md`, `reverify-raw-opcode-before-porting-bitexact-algorithm.md`, `classifier-case-index-direction-unverified-against-handler-semantics.md`, `cpu-overflow-instruction-leaves-destination-unchanged-not-undefined.md`, `guarded-call-confirmed-called-but-precondition-unreachable.md`, `literal-address-census-misses-buffer-family-aliasing.md`, `ui-state-global-census-beats-keyword-search.md`
