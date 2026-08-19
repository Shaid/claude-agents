# valkyrie — Valkyrie Profile (PSX), Valkyrie Profile 2: Silmeria (PS2)

**Project root:** `~/Development/valkyrie`

Two tri-Ace/Square Enix RPGs on different Sony platforms; a separate `game-id`/
platform pair each (`valkyrieprofile`/`psx`, `valkyrieprofile2`/`ps2`). Both
use the same in-house `"SLZ"`-tagged LZSS-family compressor — **confirmed
the identical bitstream codec**, not just shared naming (see below).

## VP1 (PSX, USA `SLUS_011.56`/`SLUS_011.79`) — SLZ compression fully solved

Almost the entire game (99.98% of each disc) lives in one ISO9660 file per
disc, `VALKYRIE.BIN` — no other real directory tree. Inside it: a 16-byte
`"SLZ"+subtypeByte` container (subtype 0 = stored, 1 = basic LZSS, 2 = LZSS
+ single-byte RLE-run extension), fully reverse-engineered from
`SLUS_011.56`'s disassembly (radare2 auto-detects PS-X EXE natively —
`format: psxexe`) and verified byte-exact against 75 real samples (0
deviation on declared vs. actual decompressed length). Confirms PSX TIM
textures (8bpp+CLUT structurally+visually verified, 4bpp visually verified)
and one plaintext Shift-JIS disc-check string (Node's built-in
`TextDecoder('shift_jis')` works with no `full-icu` flag needed).

**`VALKYRIE.BIN`'s resource-addressing mechanism — solved, via
`re-codebreaker` escalation** after two independently-stalled approaches
(blind structural/entropy scanning of both the executable and the
container; disassembly tracing of the CD-read call chain that got within
one `jal` of the answer but read a decompress+run as "a fixed destination
buffer"). The container's first 13 sectors are a 5,120-slot master
directory — packed `CdlLOC` structs (with the BIOS-unused 4th "track" byte
smuggling a sector-count high byte, see `game-re-tooling/psx.md`) — that
looked like ordinary high-entropy data to every scan because it's
**XOR-encrypted** with a simple rolling keystream; found only by tracing
the boot loader's own hardcoded, unconditional "read N bytes at fixed
position P" (see `game-re-lessons/encrypted-directory-defeats-structural-
scan.md` for the general pattern). Verified byte-exact against both discs'
real content (100% of 13,772/13,139 independently-scanned `SLZ` blocks fall
inside the decrypted directory's extents, 0 orphans; gapless, non-
overlapping, ascending partition, 0 deviation).

**Real dialogue/script text format — also solved, via a second
`re-codebreaker` escalation, closing the game's actual 15+-year
community blocker** (`romhack.org` "SLZ01/SLZ02" threads never published
an algorithm). The mechanism: every text resource ships its own **subset
font**, glyphs ordered by first use within that resource's own strings —
so no byte value has a fixed meaning game-wide (defeats any whole-corpus
plaintext/Shift-JIS/small-alphabet scan; confirmed 0 hits scanning 552M
decompressed bytes for ASCII). Cracked with a **permutation-invariant**
statistical test (sorted symbol-frequency shape + index of coincidence +
inter-separator gap distribution) that finds text without knowing which
byte means what, then resolved via a resource that happens to ship the
*complete* reference alphabet in deducible order, giving a byte-exact
bitmap→character dictionary for every other resource's subset font. See
`game-re-lessons/per-resource-subset-alphabet-defeats-corpus-scan.md` for
the general pattern. Verified: a rendered font bitmap is visually legible
ASCII; decoded strings include real VP character names (`Lezard Valeth`,
`Mystina`, `Arngrim`) and item names cross-checked 92/92 against a
published fan weapon list (5 apparent mismatches were guide typos, not
decode errors) — external-oracle-grade confirmation, not just internal
consistency.

A first-pass, then multi-block, per-slot content classifier (TIM/code-
overlay/text/other) also shipped, finding the first pass had undercounted
TIM sub-blocks by >50x (only the slot's first sub-block was inspected).

**PSX "STR" MDEC full-motion video — solved, VP1's first non-2D/audio-
video asset category.** The large (up to 24 MB) `raw-other` TOC slots
sharing a `60 01 01 80 …` prefix are standard PSX STR video (this game's
cutscenes) — confirmed field-for-field against the public `m35/jpsxdec`
spec (magic, chunk/frame counters, dimensions, quant scale, frame
version), and confirmed pixel-exact via a real decode: a hand-rolled MDEC
Huffman/IDCT decoder hit a genuine parse failure on real content, so the
raw logical sectors were instead wrapped into a synthetic CD-XA container
and fed to **ffmpeg's own independent `mdec` decoder** — real, coherent,
temporally-consistent frames (a growing fireball animation; the game's
actual opening movie, silver hair and a dramatic action scene). 122 clips
across both discs (~23 min combined), wired into a real Stage 2 that
shells out to `ffmpeg` (a new external tool dependency for this project,
gracefully skipped if absent) — `public/assets/valkyrieprofile/psx/
video/*.mp4`. See `game-re-lessons/standard-codec-delegate-to-trusted-
decoder-not-hand-reimplementation.md` for the general pattern (confirmed
standard/non-game-specific codec + a hand-reimplementation parse failure =
delegate to a trusted independent decoder, don't keep patching by hand).

**Audio — both halves solved, via two more `re-codebreaker` escalations.**
SFX/one-shot sounds are a **custom tri-Ace sample-bank container with no
magic string** (found only by a `0x0014` version word + a size invariant,
`tableEnd + 16 + max(end) == totalSize`, 0 deviation across 5,383 banks) —
this is *why* every magic scan for VAB/VAG/etc. came back empty, and a
generalizable lesson in its own right (`game-re-lessons/standard-codec-
delegate-to-trusted-decoder-not-hand-reimplementation.md`'s sibling case:
sometimes there's no standard container to delegate to at all). The
full-length **BGM score** — the actual soundtrack — was a second, harder
escalation: it is **not** hidden in an unmapped code overlay (a real, live
overlay-chain trace to a second base-confirmed overlay, the world-map
screen, came back negative — 0 SPU-register accesses under two census
methodologies). It's 80 ordinary TOC slots per disc (2212-2291,
byte-identical on both discs), each a **tri-Ace sequence format shared with
*Star Ocean: The Second Story*** (prior art: VGMTrans' `TriAcePS1` module —
romhacking-community-tools-first paid off directly here). The first
overlay-chase's "0 SPU accesses in 9/9 binaries" verdict was a genuine
false negative, not a real absence: the driver reads its hardware pointers
from a **resident constant table** in the boot exe rather than
`lui`-forming the address inline, so a census keyed on the addressing
*shape* (an immediate `0x1f80` upper-half) could never find it — see
`game-re-lessons/negative-from-addressing-root-not-shapes.md`, whose
general pattern predicted exactly this failure mode. Both audio decodes
independently re-verified (not just trusted): real byte-exact fixtures
matched against fresh reads of the actual discs, and — for BGM
specifically — a from-scratch, independently-implemented onset-
autocorrelation tempo measurement against real disc-read BPM header bytes,
plus a from-scratch port of the reference decoder into a committed,
tested module whose render of a real song is byte-for-byte identical to
the escalation's own already-verified output. 158 MB of SFX SPU-ADPCM
(~118 min/disc) + 80 full BGM songs (117 min combined) wired into the real
pipeline (`public/assets/valkyrieprofile/psx/audio/*.wav`).

**3D geometry — two stored mesh formats confirmed, plus a real billboard/
particle renderer whose semantic identity took three passes (two of them
wrong) to pin down, all via `re-codebreaker` escalations plus two direct
corrections from the user's own knowledge of the game.** §9.3's original
"0/7,931 blocks match PSY-Q TMD" scan only ever ruled out 3D content in one
specific `raw-other` character-bundle population — it was **not** evidence
the game has no 3D at all, and the user corrected this twice over. First
correction: VP1 genuinely uses 3D for the world map and combat backgrounds;
only character sprites stay 2D. Found via a GTE/COP2 opcode census across
all extracted code overlays (ranked candidates by real 3D work in one pass —
`LWC2 VXY0,(rN)` is literally the vertex fetch), then backward tracing
`LWC2` base registers: **world-map terrain** (§9.6.1, tri-Ace's own format,
not TMD — packed 6-byte vertex pool, four 20-byte draw-batch records per
chunk (spatially disjoint, jigsaw into the full cell; originally misread
as a "LOD table" and rendered one-at-a-time, dropping ~68% of the map —
see §9.6.1 Correction and `game-re-lessons/record-array-alternatives-vs-
parts-footprint-test.md`; vertical axis stored down-positive, §9.6.1a),
vertex indices
smuggled into an unused byte of packed GTE colour words; 68 chunks/disc) and
a small **object-model primitive-list format** (§9.6.2, TMD-shaped but not
TMD; five GPU primitive modes including three found only after a follow-up
escalation traced a runtime model registry's own `unk0` bundle-local-id
field). A whole-disc full-offset strict scan finds **58 models/disc, max 26
faces** — small marker/beacon shapes and 24 textured environment cubes,
nothing spell-sized.

A dedicated field-overlay resource-installer jump table (24 entries,
§9.6.4/§9.6.5) was then fully traced type-by-type looking for spell geometry
there and came back a clean, well-evidenced negative — but it was the
**wrong overlay**: spells are cast and rendered from the *battle* overlay
(slot 1490), not the field/exploration overlay this trace covered. Second
correction, from the user's direct first-hand experience of the game: spell
effects, even a basic fire spell, genuinely are rendered in 3D. This sent
the investigation back to the battle overlay's own already-known 28 `RTPS`
point-projection sites, previously dismissed as "just placing 2D
sprites/effect anchors, no mesh buffer" — a real diagnostic mistake, not a
search gap: tracing full data flow through one `RTPS` cluster (not just its
opcode shape) found a genuine, complete billboard/particle pipeline — a live
entity's dynamic world position, a per-instance texture/colour lookup (a
4-entry RGB palette, modulated by a live fade timer), `RTPS` projection with
the perspective-correction register (`IR0`) and a depth value (`SZ`-derived)
both saved (the signature of a scaled, depth-sorted draw, not flat
placement), and the resource merged into a real GPU primitive submitted for
rendering — paired with an object-spawn trigger. **This mechanism finding
held up; the semantic label attached to it — "spell effect", "elemental
colour palette" — did not.** A follow-up escalation, asked to tie a named
spell (Fire Lance et al., recovered separately from TOC slot 2179's real
per-string ids) to this pipeline's colour index, instead found the index's
*other* consumer: a `{80, 60, 40, 0}` diminishing-returns table (zero 4th
entry) feeding a 0-100 "combo gauge" field — the byte-exact signature of
Valkyrie Profile's **Purify Weird Soul** chained-special-attack mechanic
(4-chain cap, one per party member, refill amount shrinking per chain
position; confirmed independently against a published mechanics
description), not an open elemental-spell-id space. Every specific claim
was re-verified directly (gain table, pad-button table `{□,✕,△,○}`, two
sibling colour ramps at different brightness, the actor-Z-sort write site
for the field originally misread as an "effect type ID") — all matched
exactly. **Point-projection-only GTE usage is not proof of "no real 3D
effect", but a confirmed renderer's real content still needs its looked-up
index traced into its own other consumers before trusting a plausible
semantic label** — see
`game-re-lessons/point-projection-gte-usage-can-be-real-effect-geometry.md`,
the general lesson this two-stage mistake produced. **Still genuinely open**:
where a named spell's actual visual effect lives — nothing in the battle
overlay indexes anything by a magic/spell id (a 21-table jump-table census
found none), so the answer is likely in TOC slots 1021/1487/1491 (loaded by
literal constant from slot 1490) or the §13 battle-sprite/animation bundles,
neither searched yet. See `game-re-lessons/r2-string-heuristic-hides-
instruction.md` for a separate, real radare2 disassembly pitfall hit while
tracing the (correctly negative)
field-overlay half of this story (a genuine MIPS instruction misclassified
as inline string data because its raw bytes happened to be printable
ASCII).

**Terrain/object-model geometry is now really textured, and the town/
dungeon room compositor exports real parallax and content animation too
(2026-08-17).** The world-map terrain (100% of primitives, 21,238/21,238)
and the 24 field-area environment cubes resolve their decoded texture-page/
CLUT references against a corpus of on-disc TIMs (page-containment +
CLUT-row-range match — the same shape already solved for the 2D tile-
sprite compositor, §12.6 below, just applied to 3D geometry this time) and
export as real glTF with a baked atlas, replacing the earlier flat-fill/
placeholder-grey polygon-JSON render for those specific populations (the
30 untextured effect-object models stay polygon-JSON, unaffected).
Separately, the room compositor (`composeRoom`) gained an optional
main-camera parameter feeding its already-confirmed parallax formula, plus
a content-animation frame patcher for the section-5 torch/urn-flicker
table — whose per-frame "self-relative" offset field had a genuine,
undisassembled ambiguity resolved by a corpus-wide parse-success vote
(1,850/1,850 vs. 702/1,850 between the two candidate bases — see
`game-re-lessons/self-relative-offset-ambiguity-resolved-by-corpus-vote.md`).
901/1,118 rooms now export extra parallax/animation frames. A real design
mistake surfaced and was fixed mid-pass: panning the export camera by the
game's own full real camera range emptied the composited frame, because
the compositor's canvas is the room's own full extent, not a 320x224
viewport crop (see `game-re-lessons/offline-compositor-full-canvas-not-
viewport-crop.md`) — a quarter-screen pan fixed it.

Full writeup: `docs/valkyrieprofile/psx/data-structure.md` (§8 the
directory, §8.6/§8.7 the classifier, §9.3 the `raw-other` nested-sub-index
header format, §9.4 the STR video format, §9.6/§9.6.1-9.6.16 the 3D
geometry formats (including the texture-atlas export) plus the room
background/placement/parallax/compositor formats, the Purify Weird Soul
billboard renderer, and the still-open named-spell-effect question, §10
the text format, §11 the audio/BGM formats, §13.7 playable-character
battle-sprite identity/roster mapping), `docs/valkyrieprofile/TODO.md`.
Shared decoders:
`tools/shared/psx-cd.ts`
(raw CD-XA MODE2/2352 + ISO9660 reader — this project's first PSX target,
no prior `game-re-tooling/psx.md` existed), `tools/shared/psx-slz.ts`,
`tools/shared/psx-tim.ts` (also the shared texture-page/CLUT resolution
helpers `resolveTexPageRef`/`texRefSourcePixel`/`renderTimRow`),
`tools/shared/psx-vp-textured-gltf.ts` (small from-scratch glTF 2.0
exporter for atlas-mapped unindexed triangle geometry — no skin, one
shared texture per document, much simpler than a skinned-mesh exporter
would need to be), `tools/shared/psx-vp-toc.ts` (the directory
decoder — VP1-specific encryption, not a generic PSX pattern),
`tools/shared/psx-vp-text.ts` (the text/font decoder), `tools/shared/
psx-str.ts` (the STR video header parser + CD-XA rewrapper),
`tools/shared/psx-vp-audio.ts` (SFX sample bank + SPU-ADPCM),
`tools/shared/psx-vp-bgm.ts` (BGM sequence + variable-length instrument
bank + PCM renderer), `tools/shared/psx-vp-terrain.ts` (world-map terrain
chunk format), `tools/shared/psx-vp-model.ts` (the object-model primitive-
list format, 5 GPU primitive modes), `tools/shared/psx-vp-room.ts` (town/
dungeon room background/placement/parallax compositor, `composeRoom`),
`tools/shared/psx-vp-battle-bundle.ts`
/`psx-vp-battle-anim.ts` (playable-character battle-sprite bundle +
animation-directory format — **including the 2026-08-16 bit-13 patch-page
solve**: parts with flags bit 13 sample per-rect packed patch rasters from
the bundle's `other` block, page-selected by flags bits 8-10, with `(u,v)`
a VRAM-upload key rather than a TIM coordinate; this dissolved the old
"u+w>256 overflow" open item and closed the `other`-block format,
1,295/1,311 record-page groups byte-exact, `buildPatchSet`'s beam-search
order recovery + opacity-mask scoring — see `game-re-lessons/
source-rect-may-be-upload-key-into-packed-sibling-blob.md` for the
general pattern; per-frame durations are also exported now and the viewer
plays them at real decoded timing, closing the live
battle-anim-viewer-rendering user report).

## VP2 (PS2, EU SLES-54644) — TOC + "SL" container, FIS textures, TAC streamed audio, terrain heightmaps, and character mesh geometry (PS2 VIF1 display packets) all solved; `supported: true`

**tri-Ace's PS2 titles (VP2, Star Ocean 3: Till the End of Time, Radiata
Stories) store almost the entire game as raw, ISO9660-unlisted sectors**,
addressed only through an XOR-scrambled `(lba, sectors, unused)` table at a
fixed byte offset. See `game-re-lessons/iso9660-tree-near-empty-check-raw-lba-toc.md`
for the general pattern and `game-re-tooling/ps2.md` for the PS2-specific
tooling notes. The decode algorithm and per-game constants (seed/signature/
table-offset/entry-count for all 3 titles) came from a known-good fan tool
found by web search (CUE's `triAce-PS2.c`, 2011,
`https://www.bwass.org/bucket/triAce-PS2.c`) — ported byte-for-byte in
`tools/valkyrieprofile2/ps2-toc.ts`, verified against the real VP2 disc
(signature match, LBA+sectors contiguity chaining, 99.955% whole-disc byte
coverage). Only VP2's constants are exercised/verified by this project; SO3
and Radiata Stories constants are recorded for a future sibling project but
untested here.

**The inner "SL" resource-record container and its compression are fully
solved.** A 16-byte header (`"SL"` magic, 1-byte type `'Z'`/`'E'`, 1-byte
subtype 0-3, `compressedSize`/`decompressedSize`/`chainStride` as LE u32)
wraps every resource; `chainStride` links records into a chain, `0` marking
the last record — an early guess at this header's width (17 bytes, with a
spurious trailing field) had made `chainStride==0` look like an unsolved
edge case, see `game-re-lessons/resolved-edge-case-may-be-wrong-header-
width-artifact.md`. Subtypes 0-2 are VP1's `"SLZ"`-tagged codec (see above),
confirmed to decode VP2's bytes unmodified — same codec, reused across both
games and platforms. `type='E'` ("SLE") first looked like a genuinely
*different*, unidentified codec (VP1's decoders fail on it with an
out-of-bounds error within a few tokens) — a `re-codebreaker` escalation
that disassembled `SLES_546.44`'s loader found this was wrong: "SLE" is
just "SLZ" run through a position-dependent stream cipher (fixed 16-byte
key, itself derived via a deliberately obfuscated VU0 microprogram + IOP
RPC call at boot, but constant on the retail disc) — the loader decrypts in
place, rewrites the type byte to `'Z'`, and falls into the same subtype
dispatch. Subtype 3 ("LZSS16", a halfword-granularity LZSS variant VP1
never emitted) was solved by the same trace. All 125 real "SL" sub-records
on the disc decode byte-exact (10,082,942 bytes, zero deviation) — wired
into a committed Stage 1 extractor
(`tools/valkyrieprofile2/export-game-data.ts`) that writes every decoded
payload to `data/extracted/valkyrieprofile2/sl-payloads/`.

**Two payload formats are confirmed among the decoded bytes.** **MWo3 PS2
code overlays** — a generic Metrowerks-CodeWarrior-toolchain convention
(not tri-Ace-specific; cross-referenced against the GTAMods "PS2 Code
Overlay" wiki page, documented from an unrelated title, *GTA: San Andreas*
— see `game-re-lessons/romhacking-community-tools-first.md`'s "shared
toolchain convention" addendum), giving real recovered overlay filenames
(`ShopManager.ovl`, etc.) — not visual. **`"FIS\0"`-tagged records (101 of
125 decoded, the bulk of the corpus) are a full-colour PS2 GS texture
container — SOLVED end-to-end (byte-exact + visually verified against real
brand colours).** An early hypothesis ("field/scene data," built from
co-located sub-record tag names) was wrong; a first-pass render (rendering
the already-decoded bytes as raw greyscale pixels at width guesses of 128/
256) got a legible-but-incomplete answer — real images, but greyscale-only
and, it turned out, with the wrong header size and wrong width for two of
three UI-screen size classes. A `re-codebreaker` escalation found the real
shape: each `FIS` payload is a flat sequence of **PS2 GS texture-transfer
chunks** (`256-byte descriptor + variable-length data`, repeated) — exactly
2 chunks per real record, chunk 0 a `PSMCT32` CLUT (colour palette), chunk
1 an indexed (`PSMT4`/`PSMT8`) image with width/height as real parsed
fields, not a heuristic. What an earlier pass had correctly measured as a
"256-byte sub-header" with an unexplained byte-exact-consistent "family
constant" field was real data, just misread as belonging to one flat
header instead of a second, later instance of the same repeating chunk
shape — see `game-re-lessons/repeating-chunk-descriptor-mistaken-for-flat-
header.md` for the general pattern. The CLUT needs a PS2-specific
**CSM1 unswizzle** (swap palette-index bits 3/4) and the PS2 GS's
**0-0x80 alpha convention** (0x80 = opaque, not 0xFF); some images are
additionally **GS-swizzled** (block/column pixel order) and need the
standard PS2 8bpp unswizzle. Verified two ways beyond "looks right":
quantified structural checks (0/25,664 real CLUT alpha bytes exceed 0x80,
vs. ~50% expected for arbitrary bytes; the CSM1 permutation scores 26.5%
better than stored order on mean-adjacent-pixel-delta, with two
alternative bit-swaps both scoring *worse* than no permutation at all) and
external-oracle visual confirmation (the "tri-Ace created"/"SQUARE ENIX"
developer credit screen renders in its real, checkable brand colours).
All 101 real FIS records decode cleanly now — including the 31 that
previously "didn't render cleanly at any tried width" (they were ordinary
GS-swizzled images, not a distinct sub-format) and the one UI screen with
a doubled/ghosted-text artifact (was 4bpp data read as 8bpp). Wired into a
rewritten Stage 2 (`tools/valkyrieprofile2/build-assets.ts`,
`tools/shared/ps2-fis-image.ts`) producing genuine full-colour
`public/assets/valkyrieprofile2/ps2/` PNG output — **`supported: true`**
in `tools/shared/game-config.ts`. **A good worked reference for any future
PS2 GS texture format**: this exact container shape (chunked CLUT+indexed-
image, CSM1, GS swizzle) is plausible for tri-Ace's other PS2 titles too
(Star Ocean 3, Radiata Stories — see the TOC section above), not yet
checked. Still open: a `RMAC`/`FAS`/`DCM` sub-record family co-located
with `FIS` images — refined this pass from "candidate 3D model format" to
"title-screen/menu layout data" (`FAS` is a real repeating named-object
placement list; `RMAC` contains title-screen menu strings like `NewGame`/
`Continue`/`Config`) but `RMAC`'s dense binary interior is still undecoded
— the `PSMT4` CLUT sub-palette selector (GS `TEX0.CSA`, affects alternate
tints only), and a shared magic-less resource header on 2 decoded `SLE`
subtype-2 payloads. Full writeup, paths-tried tables, and the open TODO
list: `docs/valkyrieprofile2/ps2/data-structure.md`,
`docs/valkyrieprofile2/TODO.md`.

**General takeaway:** before disassembling a blocked compression/container
format from scratch, check whether a *sibling game* in the same project
(same developer/era, magic-string naming overlap) already has it solved —
see `game-re-lessons/cross-platform-decode-oracles.md`'s "sibling games,
not just platform ports" addendum for the general pattern. That cross-check
does not always cover *every* variant of a shared codec, though (SLE/subtype
3 needed their own escalation on top of the VP1 cross-check) — treat a
partial cross-game match as solving only the specific subset it was
verified against.

**A second, unprefixed top-level container solved — "resource directory"
(2026-08-07), no new codec work needed.** Of VP2's 2,511 TOC entries with no
recognized magic and no `"SL"` chain prefix, 1,046 (broadening a search that
started from 2 much-smaller prior-flagged candidate clusters into a full
leading-4-bytes histogram over the *whole* unrecognized population — see
`game-re-lessons/unflagged-cluster-beats-flagged-subset.md` for the general
pattern) turn out to share one more container shape: a flat directory (16-
byte header: `zero=0`/`count`/`dirSize=16+count*16`/`reserved`, then `count`
16-byte records of `tag`/`field1`/`size`/`offset`, `offset` a confirmed-
byte-exact running cumulative sum). Record tags are 4-letter resource-type
names stored **byte-reversed** (`"ANIM"` stored `"MINA"`, `"CHAR"` stored
`"RAHC"`, etc. — recognizable real words falling out of one uniform
reversal was itself the confirmation). Every record's payload is an
ordinary `"SLZ"`/`"SLE"` block in the *exact same* format already solved for
`"SL"` chain records — just without the `"SL"` 2-byte prefix used to locate
a chain, so the already-existing `decodeSlBlock` handles it with **zero new
codec work**. Verified byte-exact (24,472 records, zero cumulative-offset
deviations) and semantically (decoded payloads cross-link to 4 *other*
already-solved formats: `FAS`, `RMAC`, `FIS`, `MWo3` — including 126 more
real `"FIS\0"` images, visually verified: a Pause-menu icon sheet, a
chapter-select screen, dozens of new character portraits). New shared
module: `tools/shared/ps2-resource-directory.ts`.

**Streamed audio (352.6 MiB, 76 tracks) — solved via a third
`re-codebreaker` escalation: the codec is TAC, the tri-Ace Codec**, an
in-house MP3-like transform codec (static-model range coder → MDCT bands
→ alias reduction → synthesis) already identified and published by the
vgmstream project. Per this project's "delegate to a trusted independent
decoder" convention, the entropy/transform stage is **not**
hand-reimplemented — a small C harness wraps vgmstream's `tac_lib.c`
unmodified (`tools/valkyrieprofile2/tac-decode/`), the same
shell-out-to-a-known-decoder pattern VP1 used for its MDEC video. The
static scalar sub-decoder's own code location was searched for
exhaustively (shift-by-13/14 + CRC-poly censuses across both the EE
executable and the IOP sound modules, 0 hits — probably a code overlay
and/or VU1 microcode) but this doesn't block the format decoding, since
vgmstream's own decoder is used directly.

**A generic 16-byte chunk-chain container (`tag+length+backdist+length+16`,
`walkFpsChunks` in `tools/shared/ps2-fps-model.ts`) turned out to underlie
*two* previously-separate magics, `"FPS\0"` (character/face records) and
`"RMAC"` (originally thought to be title-screen-only menu-string data) —
the same container parses both with zero modification.** Inside it,
`IDOM` chunks are a confirmed, quantified **bone-palette skinning
structure** (global bone-index array + matching 3x4 transform-matrix
array, unit-magnitude rotation bases, real bilateral skeletal symmetry on
a sample) and `DNAL` (`"LAND"` reversed) chunks are **quantized int16
terrain/level heightmap grids** — byte-exact on 909/909 real chunks and
visually confirmed as real dungeon/corridor/outdoor-terrain shapes.
`DNAL`'s discovery is the key methodological turn of this arc: two prior
structural surveys of this same container's other chunk types (`FPS\0`'s
8 minor types, then `RMAC`'s 13) had both come back negative for mesh
geometry, and both were later found to have been **tuned around float32
magnitude classification**, structurally blind to the quantized/
fixed-point encodings the real geometry actually used — re-testing with
that lesson in mind is what found `DNAL`.

**Character mesh geometry — the project's biggest remaining visual gap —
is now SOLVED too, via a fourth `re-codebreaker` escalation, and the
answer was hiding in plain sight the whole time.** Both of the
"exhaustive" minor-chunk-type surveys above had, by construction, scoped
themselves to "every chunk type except `FPS\0` itself" (which already had
a role: "the character record wrapper") — nobody had ever actually
hexdumped and read the `FPS\0` chunk's *own* un-opened body, the single
largest region in every character record. It turned out to be a literal,
uncompressed **PS2 VIF1 display packet**: real hardware `VIFcode`s
(`UNPACK`/`STCYCL`/`STMASK`/`STROW`) with vertex position/normal/UV/
colour arrays inline as unpack payloads, a `GIF` A+D register block per
material, and a self-describing per-batch offset table (`h[10..14]`) that
lets a decoder read each stream's true encoding straight from its own
VIFcode rather than guessing — see
`game-re-lessons/main-chunk-role-masks-own-unopened-payload.md` for the
general pattern. Verified whole-corpus with zero deviation on every
structural invariant checked (190,118 real batches: batch counts, strip-
length sums, header-offset self-consistency) and confirmed visually (a
decoded record renders as an unambiguous humanoid character — ponytail,
armour, individually modelled fingers). `IDOM`'s previously-unidentified
header field `field0` turned out to be the batch count of the `FPS\0`
chunk it follows, tying the bone-palette and mesh-batch formats together.
Promoted to a tested TypeScript module (`tools/shared/ps2-fps-mesh.ts`),
cross-checked byte-exact against the escalation's own Python reference
decoder on both per-record and whole-corpus vertex/triangle totals — this
cross-check surfaced a real gap in the escalation's *own* corpus
verification (see `game-re-lessons/verify-escalation-artifacts-not-just-
claims.md`'s sixth instance: a manual per-observed-kind branch list had
silently excluded the single most common real encoding from ever being
checked, and a rarer 1-component shape produced literal `NaN` when
generic code finally exercised it). Wired into Stage 2 as a corpus-wide
stats index plus a bounded OBJ sample; a `"SEQW"`-tagged nested
sub-format (likely audio) remains undecoded. Full writeup:
`docs/valkyrieprofile2/ps2/data-structure.md` §§ 3.10.6, 3.10.7, 3.11,
3.12.

**Two more mesh follow-ups closed, and full-corpus export shipped.**
`IDOM`'s per-bone matrix is a real skinning **inverse-bind transform**
(`localSpace(P) = rotation^T * P + translation`) — a naive per-vertex
correlation on the raw translation column alone found nothing (max
`|r|`=0.276), but applying the **full** matrix and testing candidates by
distance-from-the-transform's-own-predicted-origin (not from each
group's own recomputed centroid, which is blind to any rigid transform
by construction — see `game-re-lessons/centroid-spread-blind-to-rigid-
transform-candidates.md`) resolved it decisively: the correctly-derived
joint position matches the mesh's own vertex bounding box within ~5% on
all 3 axes, zero permutation needed. Separately, per-batch texture
assignment (`TEX0_1.TBP0` is a load-time placeholder, unusable) was
resolved for 83.9% of texture-bearing records by matching `TEX0_1.PSM`
(a real, unpatched field) against each embedded texture's own descriptor
PSM, walking batches with PS2 GS register-state carried forward between
draw calls (see `game-re-tooling/ps2.md`'s new VIF1/GS section — most
batches carry no material block at all, and that's real hardware
semantics, not missing data). Full corpus now exported: 2,673 real
character records, 4.5M vertices / 2.65M triangles, real per-triangle
multi-material OBJ+MTL+PNG. Full writeup: data-structure.md §§ 3.12.9,
3.12.10, 3.12.11.

**Skeletal animation clips solved too — `MINA` ("ANIM" reversed)
records.** Same `"FAS\0"` magic already solved for an unrelated
title-screen placement-list format turns out, reached via a *different*
resource-directory tag, to be a completely different container: real
3ds-Max-Biped-named bone tracks (`"Bip01 Head"`, ...), each with a
32-byte-per-frame quaternion keyframe array located via a monotonically-
incrementing frame-counter field (see `game-re-lessons/same-magic-
different-format-by-referencing-context.md` and the Method §4 frame-
counter-as-oracle addendum). Verified on a real 231-frame clip: exact
sequential frame numbers, unit-quaternion magnitude every frame, smooth
bounded rotation deltas. Whole-corpus census: 275/5,182 real records
(5.3%) show a detectable keyframe track — real but partial coverage,
most `MINA` records are single-pose references. New shared module
`tools/shared/ps2-mina-anim.ts`. Full writeup: data-structure.md
§ 3.12.12.

**Both games' real geometry now has a real interactive web viewer, via
`@seer-project/engine-3d`** — confirmed a clean fit for the package's own
intended two-path split (its README's own justification for having two
paths at all): VP1's untextured terrain/object-model geometry goes through
the **polygon** path (`{verts,faces}` JSON, `buildPolygonModel`,
per-face colour reordered from the PSX GTE colour word — see
`docs/valkyrieprofile/psx/data-structure.md` § 9.6.2a), VP2's real-textured,
partially-skinned character meshes go through the **glTF** path (a
from-scratch exporter, `tools/shared/ps2-mesh-gltf.ts`, following flower's
`cavia-gltf.ts` precedent — new module doc, `game-re-method/
verification-techniques.md`'s "Bind-pose inertness" section, and
`game-re-lessons/decompose-quaternion-non-unit-needs-normalize.md` all came
out of this pass). VP2's skin decode promoted a previously-found-but-not-
committed "5th VIF stream" (per-vertex `IDOM` bone-palette binding,
`FpsMeshBatch.skin` in `ps2-fps-mesh.ts`) — real, verified
(`weightA+weightB≈1.0` on 117,242/117,242 sampled vertices), but **no
animation is baked**: there is still no known correlation between `IDOM`'s
numeric global bone-index space and `MINA`'s named bone tracks anywhere in
the decoded formats (open as `vp2ps2-mesh-animation-baking` in
`docs/valkyrieprofile2/TODO.md` — the concrete next step is tracing
whichever runtime code actually binds a `MINA` clip to a specific mesh's
`IDOM` palette, not a further structural/offset guess). Full writeup:
`docs/valkyrieprofile2/ps2/data-structure.md` § 3.12.22,
`docs/valkyrieprofile/psx/data-structure.md` § 9.6.2a.

## VP1 (PSP, `ULUS10107`, TOSE's "Valkyrie Profile: Lenneth" remaster) —
container cracked, first-reconnaissance pass (2026-08-18)

A **portable remaster by a different studio (TOSE)**, not a ground-up
rewrite — real, extensive format reuse with the PSX original confirmed at
multiple levels. Disc is a plain standard 2048-byte-sector ISO9660 UMD
image (no CD-XA raw-sector layer, unlike VP1/VP2's PSX/PS2 raw dumps —
new minimal reader `tools/shared/psp-iso9660.ts`). Almost the whole game
lives in one file, `PSP_GAME/USRDIR/PSPVAL1.PFS` (515 MB), produced by
Sony's own PSP SDK "MakePfs" tool (no public docs/tooling found for this
specific format — blind-RE'd, same as everything else in this project).
`PSP_GAME/SYSDIR/BOOT.BIN` is a **plain unencrypted PSP ELF** (Allegrex/
MIPS R3000, `Type: 0xffa0`) — unlike the retail `EBOOT.BIN` (`~PSP`-tagged,
encrypted) — radare2 auto-detects it with zero loader work, and it alone
was enough to crack the container (the `*_master.prx` per-mode overlay
modules, direct analogues of VP1/PSX's field/battle/world-map code
overlays, weren't even needed this pass).

**`PSPVAL1.PFS`'s directory is a trailer, not a header** — a 44-byte
header (`entryCount`, `dataSectorCount`, one always-zero reserved field)
is followed by real payload data immediately, and the actual directory (a
flat array of `entryCount` little-endian u32 **start sectors**,
monotonically non-decreasing, entry `i`'s length = `(start[i+1] -
start[i]) * 2048`) lives at the very *end* of the file
(`dataSectorCount * 2048`), sector-padded with the fill byte `0x98` —
found only by disassembling the header-consumer function in `BOOT.BIN`,
which computes the trailer's exact byte size from the header fields (see
the MIPS branch-delay-slot pitfall this produced,
`game-re-lessons/mips-delay-slot-instruction-always-executes.md`). Entry
index 0 is always a reserved/zero-length slot (see `game-re-lessons/
reserved-slot-zero-shifts-extractor-index.md`). Verified byte-exact: the
trailer-size formula matches the real 515,420,160-byte file with 0
deviation, and all 5,058 real entries decode to a monotonic
non-decreasing sequence, 0 deviations. New shared module:
`tools/shared/psp-vp-pfs.ts`.

**VP1 (PSX)'s `"SLZ"` codec is reused byte-for-byte, zero code changes
needed** — all 327 real `"SLZ"`-tagged `PSPVAL1.PFS` entries on the disc
decode successfully with the **unmodified** `tools/shared/psx-slz.ts`
decoder (0 failures). A third confirmed platform for this exact
tri-Ace-originated codec, after PSX and PS2 (see the VP2 section above) —
reinforces the general "check a sibling game/platform in the same project
before treating a container as unsolved" pattern
(`game-re-lessons/cross-platform-decode-oracles.md`).

**Two raw (uncompressed) `PSPVAL1.PFS` entries are genuine, byte-
compatible standard PSX MDEC "STR" video, reused verbatim** (same `60 01
01 80` magic, same header field shapes — `chunksInFrame`, `frameNumber`
sequencing, `320×240` — as VP1/PSX's own STR videos), confirmed by a real
decode through the *existing* PSX pipeline (`wrapSectorsAsCdxa` + ffmpeg
`-f psxstr`, zero new code): 204 real, coherent frames (a castle/tower
exterior scene). The PSP hardware has no MDEC decoder IP block, so this
is either a software MDEC decoder somewhere in the PSP code or an inert
repackaging leftover — undetermined this pass, a good example of
"structurally confirmed, consumer still unknown" being an honest stopping
point rather than a forced guess.

**A second movie file, `moviepac.dat` (157 MB), wraps standard Sony PSMF
containers — zero custom video codec work needed.** Its own directory is
simpler than `PSPVAL1.PFS`'s (a 16-byte **header**, not a trailer, holding
`count` **absolute**, sector-aligned byte offsets directly — confirmed
`headerSize + count*4` exactly equals the first offset). Each of the 74
real movies begins with the literal ASCII tag `PSMF0014`; `ffprobe`/
`ffmpeg` read the raw bytes directly with **zero flags** (auto-detected
via the generic `mpeg` demuxer) and produce a real decoded frame (a CGI
cutscene, hands bathed in blue magical light) — per this project's
established "delegate to a trusted decoder for a standard, non-game-
specific codec" convention. Audio-stream detection is a known open gap
(`ffprobe` reports 0 audio streams — the `game-re-lessons/generic-
demuxer-misses-custom-pes-audio.md` false-negative pattern).

**26 raw entries are literal standard PNG files** (480×272, the PSP's
native resolution) — no decode work at all, just a byte copy trimmed to
the real `IEND` end (PFS entries are sector-padded past their real
length). Visually verified: real "now loading"-style game artwork.

**A carried-over PSX-era developer debug string is a concrete clue about
the archive's internal ordering.** Two small raw entries near the very
start of the directory hold plaintext Shift-JIS text reading (translated)
"Valkyrie Profile / This is Disc 1" and "... Disc 2" — the same *kind* of
disc-check string this project's VP1 (PSX) doc already confirms exists on
the original two-disc masters, evidently kept verbatim by TOSE's
disc-unification tooling when repacking both PSX discs into one PSP
archive. A good general reminder that a remaster's own packaging debris
can hand you real structural facts about its container "for free."

First-reconnaissance pass only (matches this project's own established
"container cracked + a handful of asset types + one visual" bar for a
first pass, not full parity with the PSX side): the ~4,551 other raw
entries and the 326 untraced SLZ payloads are still open. Full writeup:
`docs/valkyrieprofile/psp/data-structure.md`,
`docs/valkyrieprofile/TODO.md` (`vp1psp-*` rows). New shared modules:
`tools/shared/psp-vp-pfs.ts`, `tools/shared/psp-iso9660.ts`.

**Second pass (2026-08-18): the `*_master.prx` per-mode module resource-
access mechanism is solved — direct literal PFS index, no id-translation
table.** All eight modules (`Battle_master.prx`, `Field_master.prx`,
`Camp_master.prx`, `GodCamp_master.prx`, `MiniMap_master.prx`,
`Staff_master.prx`, `Title_master.prx`, `WldMap_master.prx`, the PSP
equivalents of VP1/PSX's per-mode code overlays) were extracted and
disassembled for the first time. None reopen `PSPVAL1.PFS` themselves
(confirmed dead libc `open()` import in `Field_master.prx`, zero real
callers by both xref analysis and an exhaustive `jal 0x0` byte scan) —
instead, all eight import a shared `vpLibrary` API (109 functions)
exported by `BOOT.BIN` alongside a much larger 1,971-function
`libraryXP` (parsed directly from each PRX's raw `.lib.ent`/`.lib.stub`
ELF sections — 16/20-byte fixed records, NID arrays matched to stub jump
slots by `(addr - firstStubAddr) / 8`; new Python tool,
`parse_prx_exports.py`, not yet a shared TS module). Four `vpLibrary`
NIDs resolve (through tail-call trampolines) to real `BOOT.BIN` bodies
forming a complete `GetEntrySize`/`OpenEntry`/`ReadEntry`/`malloc` API.
**`GetEntrySize`'s disassembled body computes an entry's byte length with
the exact same formula already implemented independently in
`tools/shared/psp-vp-pfs.ts`'s `listPfsEntries()`** — decisive,
byte-for-byte algorithmic confirmation, not just plausible resemblance —
and the `index` argument it takes is a raw, 0-based `PSPVAL1.PFS`
directory index with **no separate resource-id translation layer at
all**: two real literal call-site indices (2175, 2182) found in
`Field_master.prx` were independently verified against the real disc
(non-degenerate, structured, embedded `SLZ` content) via the existing PFS
reader. This is the direct PSP-side analogue of VP1 (PSX)'s own confirmed
"TOC slot loaded by literal constant" convention (PSX doc §9.5) — same
studio-level design pattern surviving a full platform port. 204 total
`GetEntrySize` call sites were found across the 8 modules; only 1 had a
statically-resolvable bare-literal argument (the rest pass a
register/table-computed index, same "some literal, some dynamic" mix PSX
already showed) — a real, well-scoped stopping point (mechanism proven,
full per-call-site census left as future work), not a stall. A secondary
finding located `moviepac.dat`'s missing audio (open item since the first
pass): a manual PES start-code census found 313 `0xBD` (`private_stream_1`)
packets per movie sample with a consistent sub-header shape — the same
"audio hides behind a nonstandard PES stream id" pattern this project's
VP2 (PS2) FMV audio already hit (§2.10.2 above), confirming the technique
transfers across platforms within this project; the codec inside the
payload (plausibly ATRAC3+) is still unidentified. Full writeup:
`docs/valkyrieprofile/psp/data-structure.md` §7 (new), §5.2 (audio
update), `docs/valkyrieprofile/TODO.md`.
