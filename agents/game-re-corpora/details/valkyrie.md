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

**Field-overlay 2D sprite animation (dungeon slots, §9.6.19) fully solved
(2026-08-22, `re-codebreaker`).** The per-dungeon-slot sprite-animation
container — directory → `SLZ` record blocks → self-length-prefixed
sub-record chains — decodes to real, engine-wide PSX `SPRT` (GP0 0x64/0x66
textured-rectangle) sprites: a 14-byte part struct (`u8 u,v,w,h,w2,h2; i16
dx,dy; u16 clut; u8 tpage,flags`) and a tail that's collision/priority
geometry (not a texture quad) ending in a `{u8 boundsW, u8 boundsH}` box.
Confirmed via a 0-deviation structural sweep (3,136 real parts, 4 slot
pairs) and a strong visual oracle — rendered sprite sheets matching
Lenneth's known field appearance plus the same treasure chest in three
different CLUT-recoloured variants, independently confirming both the
part geometry and the palette-row formula. The renderer
(`fcn.800367d8`→`fcn.8003947c`→`fcn.8003865c`, field overlay slot 2292)
turned out to be VP1's *universal* 2D sprite-animation engine, not
dungeon-specific — its `SetAnimation`/`SetFrame` entry points have 84+6
call sites overlay-wide. Six direct search passes (stride-14 scans,
offset-signature scans, a full taint trace of every access to the object's
`+0xc8` "current sub-record" field) all failed because the renderer never
reads that field at all — it reads the sub-record pointer from a per-frame
draw-list entry instead; the escalation that finally cracked it succeeded
by abandoning that root entirely and searching from a different, low-fanout
anchor (the record-block registry pointer, only 7 xrefs overlay-wide) — see
`game-re-lessons/negative-from-addressing-root-not-shapes.md`.

**Follow-up passes closed the rest of the container, no escalation
needed.** The 77% of parts drawing from a runtime per-character tile bank
(`tpage>=32`) are now fully resolved: the bank's installer (slot-directory
type 13, confirmed via the field overlay's own resource jump table),
binding (an object matches its own resource id against each installed
bank's tag, `fcn.80036750`), and internal pixel layout (a table lookup
plus the part's own already-decoded `w`/`h` fields, ending in a genuine
PSX `LoadImage`-shaped VRAM upload — confirming the resolved bytes are
already native packed pixel data) are all traced and verified
(603/605 real parts resolve to real, non-degenerate, in-bounds pixel
data). Getting there required a real correction to the container's own
top-level directory format first: the `{u32 offset, u16 type, u16 flags}`
reading documented above was itself a one-record, 4-byte-staggered
misreading of the project's *already-solved* group-directory format
(same family as the `raw-other` nested sub-index below) — the type/flags
fields happened to keep reading correctly (they're the low/high halves of
one `u32` at the same address the group directory's own type tag
occupies) while the offset field was silently the *next* record's size.
Fixing it raised real-`SLZ`-magic resolution from 2/18 to 11/18 slot-
directory entries with zero effect on already-shipped pixel output (the
extractor never trusted the broken field to begin with — it blind-scans
for `SLZ` magic). The last population, type 12, turned out to be a small
16-colour CLUT/palette upload (`{x,y,w=16,h}` VRAM rect + BGR555 pixel
rows) — confirmed by rendering real regions and looking at the result
(clean flat palette swatches, one smooth gradient), and independently
cross-validated against an *earlier*, separately-reached finding on a
different slot recorded elsewhere in the same doc (`regionSize == 12 +
2·nx·ny`, "16×16 5:5:5 CLUT bank") — a live instance of
`game-re-lessons/doc-self-cross-reference-before-fresh-disassembly.md`
that should have short-circuited a full investigation round via one grep.
Whole container now closed at the research level; only ordinary
extractor/compositor engineering remains (`vp1psx-field-anim-tilebank`).

**`vp1psx-3d-spell-effect-representation` is now CLOSED (§9.6.20-9.6.21,
2026-09-04)** — a well-bounded structural negative, not an unfound
format: VP1's battle spell/skill visuals are drawn by a small, shared,
parametric GTE-billboard routine (§9.6.6, confirmed, runtime
position/colour arguments) rather than selected from any per-effect
asset table. The one id-indexed table this whole investigation ever
found in that call graph resolves to the SPU audio driver (real SPU MMIO
writes at `0x1F801D88`-`0x1F801D8E`, Voice KON/KOFF, a 24-entry array
matching the PSX SPU's 24 hardware channels exactly — Ghidra FunctionID
auto-named the base pointer `PTR_VOICE_00_LEFT_RIGHT`), not to visual
data. Confirmed via `ghidra_psx_ldr`'s native `PS-X EXE` loader tracing
the resident-exe call chain a first round couldn't resolve without it.

Full writeup: `docs/valkyrieprofile/psx/data-structure.md` (§8 the
directory, §8.6/§8.7 the classifier, §9.3 the `raw-other` nested-sub-index
header format, §9.4 the STR video format, §9.6/§9.6.1-9.6.16 the 3D
geometry formats (including the texture-atlas export) plus the room
background/placement/parallax/compositor formats, the Purify Weird Soul
billboard renderer, §9.6.20-9.6.21 the spell-effect closure, §9.6.19
the field-overlay 2D sprite-animation format, §10 the text format, §11 the
audio/BGM formats, §13.7 playable-character battle-sprite identity/roster
mapping), `docs/valkyrieprofile/TODO.md`.
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
`tools/shared/psx-vp-field-anim.ts` (dungeon-slot 2D sprite-animation
container + `SPRT`-accurate compositor, §9.6.19), `tools/shared/
psx-vp-battle-bundle.ts`
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
battle-anim-viewer-rendering user report). **2026-09-03 correction (§13.7.1c):**
`decodeBattleBundle`'s raw-record gap scan stepped by 4 from `gapStart`
(an SLZ span's end, only coincidentally 4-aligned) instead of the next
true 4-byte boundary, silently missing the animation record in 21/26
playable-character bundles including both of Lenneth's own (TOC 1488/1489)
— a Stage 2 build session had misread the resulting garbage-colour render
as Lenneth uniquely lacking a body texture and needing a new cross-slot
compositor feature, when every one of the 26 bundles is in fact fully
self-contained. Fixed by snapping the scan start to the true boundary; see
`game-re-lessons/fixed-stride-scan-from-unaligned-anchor-misses-true-boundary.md`.
`src/battle/scene.ts` now drives Lenneth via `AnimCanvas`/`entryForAnimId`
off her own TOC-1488 record, same mechanism as the enemy.

**VP1's battle *gameplay logic* (not asset formats) is a separate, actively-
growing thread — `docs/valkyrieprofile/psx/battle-logic.md`.** Started
from TOC slot 1490 (battle overlay) plus a second battle overlay, TOC slot
1491 (a group-directory slot never in any position-0-only census's file
list — finding it needed a `re-codebreaker` escalation, and it turned out
to hold the whole roster-construction/stat pipeline: actors are a
per-battle `malloc(0x6ac)`, but ATK/DEF/HP arrive as one 64-byte `memcpy`
from a persistent 236-byte stat record, `charTable[charId-1]` for party or
a scratch enemy record). By this session it had independently solved the
core ATK-DEF damage formula, turn structure (no speed stat — enemy phase
is strict array-slot order behind a one-at-a-time mutex; player phase is
real-time simultaneous four-button combat, one pad button per party slot),
EXP crediting (byte-exact against a published table), and enemy move
naming (a literal text-bank id passed to the on-screen banner spawner).

A same-session sibling thread, **`docs/valkyrieprofile/psx/item-skill-
system.md`**, worked the item/skill/spell mechanics layer on top of that
foundation and closed every item the coordinator opened it with: a
weapon/defender elemental-effectiveness system (a real static 6×6
matchup matrix, `{-50,0,25,50}`, joining all 5 of the game's own UI damage-
tier labels via one `mult = value + 100` formula — a corpus-wide "table is
`0xFFFF`-filled, RAM-resident" doc claim turned out to be simply wrong,
never actually bytes-checked); the 612-entry static item stat table
(`itemTable32`, found via a `re-codebreaker` escalation whose real blocker
was a wrong function boundary — `r2`'s xref list was bogus because the
address it named was a mid-function label, not a real entry point,
findable by walking the epilogue's stack-adjust back to its matching
prologue); the full accessory-bonus formula (all four "further derived
stats," including a strong RST candidate); and — after a full 6-angle
static census came back empty and got escalated — the "second item
struct" that turned out not to exist at all: `word[actor+0x570]` is the
already-documented § 13.6 stat-record back-pointer, and the census had
actually found the exact right store instruction on its first pass, just
mislabelled its base register as the shared battle-context pointer
instead of `actor` (see `game-re-lessons/indexed-operand-needs-base-
provenance.md`'s third worked example). That same escalation also caught
that the answer had been sitting, verbatim, in this project's own
`battle-logic.md` for hours already — see
`game-re-lessons/doc-self-cross-reference-before-fresh-disassembly.md`'s
now-recurring Valkyrie Profile pattern. Also found along the way: Purify
Weird Soul chain attacks are real-time and gauge-driven, not menu- or
learned-list-selected at all (no "learned skill" list was ever found
because there isn't one for this half of the system); magic/spell casting
remains a genuinely separate, still-unlocated menu subsystem. Both docs
share `docs/valkyrieprofile/TODO.md` as their single open-item tracker.

**Continuation (2026-08-23): dialogue portraits substantially named,
BGM/TIM formats fully closed, and a "leftover field" turned out to be a
whole undecoded skill-progression system.** The scene-script bytecode
VM's own operand-word census (5 structurally distinct techniques, all
documented real negatives) had exhausted every literal-operand path for
naming the 207 dialogue portraits — a `re-codebreaker` escalation found
the real mechanism was never in that search space: a "show still image"
opcode's TOC-slot argument arrives as a *script-function call argument*
via a shared library, invisible to any per-instruction operand census.
Named 176-178/207 portraits and located 10/24 event CG, cross-disc
verified and independently spot-checked (both cited handler addresses
re-disassembled directly before trusting the report), then wired into
the real pipeline (`character-portraits.json`). Tracing the same brief's
own target function (a 19-opcode "property setter" that turned out to be
a command-enqueue, not a setter) also answered a second open row: the
runtime entity-id registry is resolved by a *different* opcode (99.2%
vs. 0.0% resolution) than previously assumed. Separately, a stat-record
byte long characterised only as "+200 max HP, no writer found" turned
out not to be an individual field at all: the record's whole persisted
`+0x38..+0x95` range is two parallel 47-entry per-skill-id arrays (CP
accumulated / current level), confirmed 14/14 byte-exact against the
game's own skill-description text stating its formulas' constants
verbatim (`in-game-text-states-own-formula-constant.md`, harvested from
this exact session) — the writer lives in a "menu sub-overlay" family
whose load base is `knownOverlayBase + knownOverlaySize`, not a fixed
constant (`sub-overlay-base-is-parent-base-plus-size.md`). Also closed
outright: a BGM header field previously read as "truncated ASCII/
Shift-JIS song-title fragments" is confirmed real Shift-JIS composer
category tags (battle/fixed/spirit/anxiety/...), not titles — several
values repeat across unrelated songs, the signature of a closed
vocabulary, not per-song text; and 16bpp TIM decoding, previously
"implemented but unverified," is now a confirmed **genuine absence**
after an exhaustive both-discs SLZ-block scan (8,562 real TIMs, 0 at
16bpp/24bpp). Both new 47-skill and 25-character template tables
promoted to committed extractors (`skills.json`, `character-initial-
stats.json`), each independently re-verified against real disc bytes
before committing, not just `tsc`/tests. Full writeup:
`docs/valkyrieprofile/psx/data-structure.md` §17.10,
`docs/valkyrieprofile/psx/battle-logic.md` §§24-25,
`docs/valkyrieprofile/psx/item-skill-system.md` §5.7.9/§5.7.9a.

**Continuation (2026-08-23, later same day): the battle move-entry struct
closed on a refuted premise, a real animation-trigger mechanism found, and
a scratch-field multiplexing trap surfaced twice.** A `re-codebreaker`
escalation found the move-entry array's own "5 x 24-byte entries copied
verbatim" premise was wrong — the copy loop is an *expanding* one (20-byte
source stride, 24-byte dest stride, 6 iterations, not 5), closing the
field accounting to 15/20 bytes with a confirmed consumer, 3 provably
reserved, 1 real-but-unconsumed; independently re-verified byte-exact
before committing (raw instruction words re-decoded from the cached
overlay, both new probe scripts re-run, every cited figure reproduced).
Following up by hand found the real "start animation N" entry point
(writes a new confirmed field, `actor+0x5c`) and confirmed 5 of 8
"universal" animation-directory ids as real code-triggered literals via a
corpus-wide call-site census — then a clean, quantified negative on the
other 3 (0 literal hits across the sibling animation drivers' 58 combined
call sites), narrowing the open question to "needs register dataflow
tracing" rather than "needs a wider census." Separately, a stale "decode
the paired code overlay" lead for a small UI-icon bundle's undecoded
per-instance fields was refuted outright (0 references to the expected
context global at the now-correct load base), and the real blocker was
found instead: the loader's own generic "load a resource, cache its
pointer in a scratch context field" sequence is reused **byte-for-byte,
differing only in the literal TOC-slot argument**, for at least 3
unrelated resource kinds (the UI-icon bundle, the battle overlay, and an
already-known VRAM save/restore buffer) — a real, concrete instance of
`scratch-slot-dual-role-verify-against-real-platform-struct.md`'s trap,
confirmed via a *different* proof technique from that file's original
worked example (finding the identical loader instruction shape reused
with a different literal, rather than checking field reads against a
known external struct). A plausible-looking candidate reader was
deliberately **not** attributed to the target resource once this
surfaced. Also closed the damage formula's last open hedge (its "not
fully re-derived" scale-table indexing turned out to be the *same*
move-entry `×24` idiom, reading the current move's own already-named
Q8.8 scale field) and fully disassembled a spell-learning gate's trigger
structure (2 mode-sentinel checks plus a bitmask test, 5 concrete global
addresses now named, upstream writers still unlocated). Full writeup:
`docs/valkyrieprofile/psx/battle-logic.md` §§9, 11.13, 22.3-22.3d,
`docs/valkyrieprofile/psx/data-structure.md` §9.6.11 (2026-08-23 updates),
`docs/valkyrieprofile/psx/item-skill-system.md` §5.7.9b.

**Continuation (2026-08-23, still later): a battle-outcome dispatch
mechanism found, a room-layer id resolver's exact arithmetic re-derived,
and an enemy-record field pair solved by trying the game's *other* known
addressing idiom.** Tracing more of the shared damage-popup spawner's
call-site worklist found a previously-undocumented battle-context field
(`battleCtx+0x644`) that fully nullifies party- or enemy-side damage by a
2-bit flag; its one writer turned out to be gated on the *already-
confirmed* global party/save-state struct's own multi-bit flags field —
and a second write site to a *sibling* field (`battleCtx+0x630`, an
exit-reason code), previously logged in this project's own paths-tried
table as an unrelated same-offset-collision false positive for a
different search, turned out to hold real content once re-examined from
this new angle: together the two confirm a real, systematic
battle-outcome-dispatch scheme (exit-reason code -> its own subset of
save-state flag checks), not one-off init plumbing. Separately, a
scroll-record "kind" enumeration's logical-id-to-record resolver
(`fcn.80039ae8`) was disassembled in full: 3 confirmed sub-ranges,
including a genuine "10 distinct thematic extra-layer ids all alias to
the same fallback record" scheme (not an approximation) and a real,
useful negative — one specific kind value is never reachable through
this function at all, meaning its real consumer uses a different, more
direct access path (searched two genuinely different ways, both
negative, left open rather than forced). Best result of the round: an
enemy-stat-record field pair (`+0x6A`/`+0x6B`) marked "no known consumer"
for several passes was solved outright once the search tried this
project's **other** already-confirmed enemy-record addressing idiom
(`battleCtx + k*116 + 0x394 + offset`, not the `actor+0x570` redirect the
earlier searches used) — a textbook instance of this account's own
`negative-from-addressing-root-not-shapes.md` pitfall, not a new
technique but a clean confirming case: a real, fully-disassembled
one-shot proc-chance check, `random(100) < (attacker's record+0x6A -
defender's record+0x6B)`, clamped to a floor for one specific already-
named command code. Full writeup: `docs/valkyrieprofile/psx/
battle-logic.md` §§6.1, 15.1, `docs/valkyrieprofile/psx/data-
structure.md` §9's "kind" resolver update, `docs/valkyrieprofile/TODO.md`.

**Continuation (2026-09-16): VP1's battle is a real 3D scene, not a 2D side
view — arena geometry, per-unit world position, and the camera all solved,
and unit position turns out NOT to be cosmetic.** Prompted by the owner's
first-hand play of the original release. Findings: per-unit world position
lives at `actor+0x7a/0x7c/0x7e` (X / height / depth) driven by a 26.6
fixed-point integrator; **one** shared world-to-screen projector,
`fcn.80060044` (51 call sites, battle overlay TOC slot 1490, load base
`0x8002f824`), issues a single GTE `RTPS` against an *inherited* rotation
matrix (0 `ctc2` of its own) and returns screen X/Y plus a perspective scale;
the camera is **not fixed per arena** — it is a software camera in four
battle-context fields that eases toward a zoom target (step saturating at
512, ramping to a 128 distance floor) and **freezes entirely during the
90-frame PWS input window**, both camera routines short-circuiting on the
same flag. All five regions of the 51 arena bundles (TOC slots 1436-1486) are
decoded: two TIMs, a layered parallax textured-quad scene description, a
20x12 ground tile map, and the arena's own draw module — which was confirmed
to share the unit camera exactly (9 COP2 instructions, 0 `ctc2`, byte-identical
`RTPS` words, same depth term). **Position affects combat math**: `resolveHit`
projects the impact point through `fcn.80060044` and runs a screen-space AABB
test against each candidate's projected box to gate area attacks — documented
but deliberately not implemented in the position-free `src/engine/` core.
This session sourced `game-re-lessons/differential-oracle-blind-to-harness-
injected-state.md`: the projector port matched the real routine 896/896
byte-exact under the project's own MIPS interpreter (with a discriminating
negative control) while the assumed resident GTE matrix was wrong, because
the harness fed that matrix identically to both sides; a browser render
caught it instantly, and a 791-point distance sweep then *refuted* an identity
matrix outright rather than merely failing to confirm it. Also a third worked
instance of the "two independently-authored constants agreeing to the unit"
oracle (a screen-Y formula derived in one routine reproducing a standalone
literal in another; a zoom-target literal equalling the initializer's own
zoom; an OFX/OFY pair restored identically at two unrelated call sites). Full
writeup: `docs/valkyrieprofile/psx/battle-engine-spec.md` §§12-13; runtime
module `src/battle/scene3d.ts`, disc-byte oracle
`tools/valkyrieprofile/vp-battle-projection.ts`, arena parser
`tools/shared/psx-vp-arena.ts`. Still open: the resident rotation matrix's
real value and install site (outside slot 1490).

**Continuation (2026-09-17): VP1 has NO random encounters and no encounter
pool — the tracker row asking for them asserted a mechanic the engine cannot
express.** The field overlay's battle-start task spawner `0x8004227c` has
exactly **two** callers corpus-wide (a census over 1,682,433,476 decompressed
bytes per disc, 0 materialisations of its address): scene opcode 134's own
handler `0x80078774`, and the battle-transition task `0x8006474c`. The scene
VM's fully-enumerated 238-entry dispatch table contains **no RNG opcode**, so
a script physically cannot randomise its argument — a free disproof that was
available on day one (see `genre-mechanic-asserted-by-tracker-needs-primitive-
existence-check.md`). The 1,147 "runtime-computed" launchers reduce to three
producer shapes, all reading local 0 = parameter 0 of one statically-linked
helper `startBattle(encounterSlot, sysset0, sysset1, counterSlot)` replicated
into ~1,118 scripts, whose callers push literals; the small minority is an
`if/else` storing a literal via `STI.l` (a **story flag**, not chance). Every
battle in VP1 is therefore compile-time authored by the room. A genuinely new
mechanic fell out of the trace — the **container ambush**: opcode 204
(`PLACE_CONTAINER`) operand word 3 byte 0 is an engagement-effect kind (read
only when container type >= 2, at `0x8006fdb0`); value **8** selects entry 7
of the jump table at `0x8007dee8` -> `0x8005ff78`, installing `0x8006474c`,
which fights the bundle named in operand word 5 — i.e. a chest that attacks
you when opened. Encounter coverage rose 346 -> **391 of 414** bundles; the
residual 23 are real named rosters assessed as unused content (well
supported, not proven). Encounter *rate* does not exist, but the per-scene
128-byte counter at `globals[0x16c..0x1ec]` (opcode 134's second argument,
indices 1..51, cleared by opcode 120) is real with its consumer still
untraced. Spec `docs/valkyrieprofile/psx/battle-engine-spec.md` § 12.16b;
modules `tools/shared/psx-vp-encounter-source.ts`,
`tools/valkyrieprofile/verify-container-ambush.ts`,
`src/battle/encounter-source.ts`. Sourced three lessons: the two named above
plus `runtime-valued-script-operand-is-usually-a-parameter.md`, and sharpened
`spawner-install-literal-outranks-backscan-prologue.md` with the
hoisted-load-above-`addiu $sp` variant (real entry `0x8005edfc`, not the
back-scanned `0x8005ee04`) and the "a 0-hit address census indicts the
address, not the code's reachability" tell.

**The dungeon/field layer — the real-time, player-controlled half of the
game, underneath the scene-script VM — is now substantially solved across
three passes** (`docs/valkyrieprofile/psx/dungeon-field-mechanics.md`, 17
sections; ported to `src/engine/field/`, dependency-free). Everything lives
in the **field code overlay, TOC slot 2292**, runtime base `0x8002f824`,
369,036 B — so subtract `0x8002f824` from any address below for a file
offset into the decompressed overlay, and note the resident `SLUS_011.56`
text only reaches ~`0x8002d808`, i.e. most "resident-looking" addresses in
the `0x8003xxxx` range are actually overlay code.

Solved: player physics (walk `0x200`/frame, dash ×2, air control saturating
at ±`0x100`, a three-stage variable-height jump with a 6-frame windup and a
`×4/3` or `×2/3` launch scale), the 96-slot × 264-byte field actor table at
`*(0x8007f0e4)` with the player as **actor 0** — the *same* table the
scene-script VM's property opcodes address, so field collision is not a
separate actor system — and a byte-swapped pad word whose **D-pad is in the
high nibble** (`0x1000`/`0x2000`/`0x4000`/`0x8000` = Up/Right/Down/Left),
with the action buttons runtime-remappable through **seven** masks at
`ctx+0x31a`..`+0x324` so their physical defaults live outside this overlay.

Three structurally significant findings, each a reusable shape:

- **Per-area native code (`regionType` 18).** Each dungeon area ships its own
  compiled MIPS module inside its room resources, loaded raw to `0x800899b0`
  — *exactly* `0x8002f824 + 0x5a18c`, the byte after the overlay — so module
  and overlay form one contiguous image and the module calls straight into
  engine code. 61 distinct modules on Disc 1 across 376 rooms. This is where
  per-dungeon set-piece mechanics live. The largest shared one (11,556 B,
  100 rooms) is the **Karakuri/Clockwork Mansion's 5×5 rotating-room grid
  puzzle**, fully decoded and ported — and it answered a *different* open
  question than the one it was opened for (see the corpus's own § 10/§ 14
  correction: a rotating-grid puzzle does exist, it is just attached to
  room-to-room movement rather than to chests, and is never named in-game).
  Its three script-callable routines are reached from *outside* the module,
  as entries 30/31/32 of the overlay's `TASK` table — an exhaustive in-module
  caller scan correctly finds zero references.
- **Object interaction is two-staged and scripted.** Pressing attack runs
  `FUN_80044e34` (40 × 16 B scripted trigger volumes at `*(0x8007f1c8)`,
  each with its own button-select mask) and then, only if that found
  nothing, `FUN_800444dc` — a linear sweep over actors 1..95 testing the
  player's current animation hitboxes, dispatched per target through a
  6-entry jump table at `0x8007dbc8` keyed on `actor+0xc6 & 0xf`. Anything
  not in that table invokes the target's **own scene script** from
  `actor+0xd8` via `0x80071c70`, which is already documented elsewhere in
  this project as the VM's opcode-20 `CALL`. So the *content* of a field
  interaction is script data, not native code — which is why native searches
  for specific behaviours (a "purify a field enemy" mechanic) can never
  succeed regardless of effort. Sourced
  `game-re-lessons/index-writer-may-be-a-loop-counter-not-a-selection.md`:
  two passes hunted "what *selects* the engaged-actor index" before noticing
  the writing register was just the sweep's counter.
- **Room collision geometry.** The list at `roomBlob + u32[roomBlob+0x0c]`
  (cached at `*(0x8007f0f4)`) is a **chain of broadphase cell blocks**,
  `{s32 cellKey; u32 blockBytes; primitive[]; u16 0xffff}`, not a flat
  array. Each 0x24-byte primitive is a slab: `s16` bbox, a 24.8 X span, and
  an upper and lower surface Y pair, then a type byte at `+0x20`. Nine
  types, `0..8`; the engine special-cases exactly `{4,5,6,8}` (ladder /
  drag volume / grabbable ledge / confining slow zone) and sends the rest to
  one shared solid path, with 2 and 3 separated *elsewhere* as slopes.
  1,117/1,117 Disc 1 rooms walk a clean chain, 13,708 primitives, values
  exactly `{0..8}`. Sourced two lessons —
  `traced-enum-label-corroborated-by-carrier-name-set.md` (type 8 occurs in
  exactly three hazard-themed named rooms including a literal swamp; type 4
  is median 32×242 px and type 6 median 240×5 px, a ladder and a ledge lip)
  and the code-side variant of the partition oracle in `game-re.md`'s
  verification techniques (three unrelated functions each carry their own
  skip-list for the same four values, read two different ways).
- **Collision response** (`src/engine/field/room-collision-response.ts`,
  2026-09-18): a full end-to-end disassembly of the shared solid-geometry
  dispatcher (`FUN_80031194`, 1,246 instructions) hardened "nothing
  distinguishes types 0/1/7" from a data-statistics inference into an
  instruction-level negative — the type byte is read exactly once, at
  entry, on both discs (byte-identical field overlay). The engine's cosine
  table (`rcos`) is confirmed exact over its *entire* 4096-value domain
  (every possible masked input, not a sample) against
  `round(4096*cos(...))`, so the port drops the embedded table for the
  closed form outright. The slope-velocity projection, the one-way
  drop-through gate (a real five-condition check, not just "Down held"),
  and a wall-contact impulse decay are fully disassembled and ported. The
  wall push-back arithmetic (`~10` "interdependent scratchpad globals" from
  the 09-18 pass turned out to be nothing but the current primitive's own
  fields plus a much smaller real accumulator set) is now also fully ported
  — box construction, the six-condition wall-hit test, the closed-form
  push-back, and the velocity commit that consumes the corrected box — see
  the position-integration entry below for how the *last* open piece
  (turning that corrected velocity back into a position) was found.
- **Per-frame position integration — the general `actor.x += actor.velX`
  commit (2026-09-19, `vp1psx-collision-position-integration`, now
  resolved).** Three independent static passes (an exhaustive
  register-tracked dataflow scan, a move-idiom-tolerant successor, and a
  168-function reachable-call-graph sweep) all missed it because every one
  keyed on the *literal* `0x94`/`0x98` struct-offset byte in the store
  instruction; the real commit, `FUN_80039b5c`, biases its own base pointer
  first (`addiu $a2,$t0,0x98`) and so never contains either literal
  displacement anywhere in its body — see
  `game-re-lessons/struct-field-scan-blind-to-biased-base-pointer.md`
  (sourced from here). Escalating to `re-codebreaker` with a symbolic
  base-plus-offset tracker (negative offsets included) found exactly three
  biased-base stores in the whole 369,036 B overlay, all inside this one
  function — a uniqueness proof, not just a discovery. `FUN_80039b5c` is
  the 5th of 12 calls in the field engine's own master per-frame dispatcher
  (`0x80046f8c`, found this session but itself still statically
  unreachable — a real, unexplained loose end, not a blocker). Ported as
  `integrateActorPosition` in `src/engine/field/room-collision-response.ts`
  (both the ordinary path and the "slaved to another actor," `actor+0xe4 &
  0x200000`, anchor-relative variant) and wired into
  `src/engine/field/index.ts` for the first time — that barrel had never
  re-exported any of `room-collision-response.ts`'s functions before this
  session. Full derivation: `docs/valkyrieprofile/psx/
  dungeon-field-mechanics.md` §§ 21.19-21.20.

Deliberate negatives worth not re-running: **no "Soul Crush"/"Purify Weird
Soul" field mechanic exists** — 0 text hits on either disc, no native branch
that defeats an actor, and the name belongs to the *battle* combo-gauge
mechanic this project already extracted (`item-skill-system.md` § 6's 68/68
PWS attack-skill table, `data-structure.md` § 9.6.8's chain index at
`globalCtx+0x113a`). **Nothing distinguishes collision types 0/1/7** — now a
hardened, full-disassembly negative, not an inference (see above). Still
open: gravity's constant, the field engine's own master per-frame
dispatcher being statically unreachable (§ 21.19.4), the authored meaning
of each `actor+0xc6` object kind, and the low-priority
`vp1psx-field-slaved-actor-offsets` (the slaved-actor path's `+0xd0`/`+0xd4`
anchor-offset fields are decoded but not semantically named or fully
traced).

**All four player field sprite banks are now closed** (§§ 18.3/19.6/19.7/
21.21): 3604 is orphaned content (no area-table row selects it, and it
carries no tile bank to draw from); 3605 and 3607 are both Lenneth in
Valkyrie form on two different art sets (same entity id, animation count,
frame count and effect banks); 3608 is Arngrim (his only two rooms' own
text names him outright); and 3606 -- the town/story walking form -- turned
out not to be one fixed character at all. A full 156-room dialogue-speaker
census (not the 2-room spot check the row was originally closed on) found
91 distinct named speakers and zero dominant identity, refuting the
"Lenneth out of armour" hypothesis in its strong form; Valkyrie is a real
but minority speaker (15/156 rooms). It's the engine's one shared
non-combat overworld sprite, reused by room authors across 34 locations
(every town's own recruitment arc, the prologue, the Valhalla flashbacks)
rather than reserved for a costumed identity -- confirmed to be a static,
per-room authoring choice with no live "active player character" selector
anywhere in the scene-script VM. The census also caught a real decode bug:
the whole-disc font/text pairing heuristic's same-slot-neighbour fallback
silently mispaired 38/156 rooms (all from one block of near-identical
`Castle of Dipan(past)` template rooms) to the wrong font, producing
plausible-looking short garbage rather than an error -- resolved by
decoding each room's own chained font directly instead of trusting the
heuristic. See `game-re-lessons/proximity-pairing-fallback-fails-on-near-
identical-siblings.md`, sourced from here.

**Continuation (2026-09-24): the ending staff roll (TOC slot 4795) solved
end-to-end via `re-oracle`, correcting a mislabeled "world-map texture
bank" that had produced two separately-hardened negatives.** Two TODO rows
(`vp1psx-region-type-21-slot4795`, `vp1psx-worldmap-command-table-
slot4795`) had each reached a "needs a live trace/emulation" verdict after
a `ghidra-disasm` escalation plus two static-census passes. Both were the
same single wrong premise, not two independent problems: an earlier
session's doc citation "slot 4794 (0x8005e8c4)" was the *call site* inside
the field overlay (slot 2292) that loads and runs slot 4794 — the identical
convention every other overlay in the same citation list used explicitly
("slot 1490 (battle, jal 0x800105b0 at 0x80042e24)") — misread as slot
4794's own runtime load base, then "confirmed" by a file-offset-0 prologue
check that is actually position-independent and proves nothing about the
base. Every downstream literal-address census (direct-jal, raw-pointer,
`lui`+`addiu`/`ori`-pair) and even a full `ghidra-disasm` decompile then
searched addresses shifted by the same `0x2f0a0` delta, producing several
mutually-reinforcing-looking negatives from one wrong number — see the new
pitfall `call-site-address-misread-as-load-base.md`, sourced from this
session. `re-oracle` found the real base (`0x8002f824`) three independent
ways (the main exe's own overlay-decompression destination; the ORIGINAL
citation's own instruction; and an address-independent internal-consistency
check on slot 4794's own bytes) and the whole subsystem fell out: slot 4794
is a small C++ overlay (real vtables, `jalr`-dispatched) rendering VP1's US
ending credits scroll from slot 4795 (219 pre-rendered text sprites + a
165-entry layout script + 6 art TIMs — "Fin", two feathers, "I think
together, we will be able to find happiness.", "The End"). TOC slot 4795 is
corrected from "world-map texture bank" (the § 9.3/§ 9.6.1 label) to
"ending staff roll asset bank" — never co-resident with the world-map
overlay at all (7 of this project's 8 top-level code overlays share the
identical runtime base `0x8002f824`, a one-at-a-time swap scheme, not
simultaneous residency). Before escalating, this session did real
additional static work distinguishing the negative from the prior passes
(per this project's own standing lesson to test "needs live capture"
verdicts via `re-oracle` rather than accept them at face value):
disassembled the mystery per-entry-handler address in all seven
base-sharing overlays (not just the one file the prior `ghidra-disasm` pass
checked) and searched for any static reference to the containing loop
function's own address across 11 overlay files plus both executables via
three independent techniques, finding zero in every case. Verified
end-to-end (49 checks, both discs, `tools/valkyrieprofile/verify-staff-
roll-slot4794.ts`) and shipped via a new pipeline stage
(`tools/valkyrieprofile/staffroll-assets.ts`); rendered PNG output visually
confirmed the complete, legible English credits roll (every playable
character, VA cast, tri-Ace/Enix/ACTAS staff) and the six art TIMs. Two
narrow follow-up leads left open: `vp1psx-staffroll-launcher-vcall` (the
field overlay's own launcher for slot 4794 is reached through an untraced
virtual call) and `vp1psx-worldmap-texbank-recheck` (re-run § 9.6.1's
world-map TIM resolution against slots 4797/4799 only, since it previously
also pulled TIMs from 4795). Full writeup: `docs/valkyrieprofile/psx/
data-structure.md` § 9.6.30.

**Round 121 (2026-09-25) closed almost all of `vp1psx-room-layer-placement`'s
remaining sub-items.** 18 D1/16 D2 image layers that failed to parse were a
single, deliberate byte signature — a `[u16 byteLength][u16 flags]` payload
whose stream is nothing but the `0xFFFF` terminator with zero preceding
commands (a genuinely, deliberately EMPTY layer, not corrupt data);
`parseRoomTileStream` now accepts this shape (32/33 both discs still
placement-referenced, 2/33 confirmed Section-5 animation-patch targets). A
separately-documented "handful of layers render as noise" claim was closed
as **stale, not a real defect** — both cited examples render clean through
the current, unmodified compositor; the original observation predated later
decoder corrections and had never been re-verified (re-verifying it via a
fresh standalone reimplementation first manufactured a second false
positive from an unrelated bug in that reimplementation — see
`fresh-reimplementation-reverify-manufactures-false-confirmation.md`,
sourced from this session — before an ablation/diff technique built on the
real, unmodified compositor showed the content is genuinely clean). The
scroll record's `unk8` field on records 3/4 (kinds 130/140) turned out to
be read by a previously-uncited shared "actor default-field init" helper
that seeds every newly-spawned actor's `obj+0x102`/`obj+0x103` — exactly
the two fields `scene-script-vm.md`'s `SET_ACTOR_TAIL_BYTES` opcode already
named as script-overridable, closing a cross-reference that had sat
unlinked since an earlier round (record 2's `unk8` remains confirmed
genuinely unread). The runtime placement "pan X/Y" fields (`+0x20`/`+0x24`)
had resisted two independently-built static negatives — both blind to the
same root cause, a struct-field census keyed on the literal offset while
every real access goes through a base pointer biased by `+0x38`, `+0x24` or
`+0x1c` (a second confirmed instance of `struct-field-scan-blind-to-biased-
base-pointer.md` in this project). A `re-oracle` escalation found the real
writers: **61 small native-code modules embedded as `regionType 18` region
payloads inside each room's own data slot** (not TOC-level overlays at
all — loaded contiguously right after the shared field overlay), a genuine
architectural discovery that these per-room "modules" are real compiled
code hooks, not just background-art containers. Exactly 2 of the 61
(the two shipboard rooms) write pan Y with a sine bob; none writes pan X.
This also surfaced the second real consumer of the scroll record's `kind`
field: an "extra" record's kind is a **private per-room selector id** the
room's own module matches by literal, not part of the shared enumeration.
See `overlay-census-blind-to-region-embedded-code-modules.md`, sourced from
this session, for the generalizable "a corpus-wide overlay census misses
code embedded as data-slot region payloads" trap. Only remaining open items
in that TODO row: `flags` bit 2 (weak/inconclusive after a broad but
unfocused static sweep), plain-English names for the fixed `kind` values
(needs a deep per-site register-dataflow trace across 15 call sites, not
attempted this round). `tools/valkyrieprofile/verify-room-empty-image-
layers.ts`, `verify-room-noise-layers-stale.ts`, `verify-actor-default-
field-init.ts`, `verify-room-module-pan-writers.ts`.

**Round 161 (2026-09-26) solves flag `0x3F7`'s setter — a genuinely new
(4th) story-flag-write channel, via `re-oracle` after 6 differently-shaped
static negatives — and closes a stale premise in an already-"resolved" row
it happens to touch.** `0x3F7` (world-map event 15's end flag) is set by
`CompleteEvent(endFlag)`, a statically-linked **scene-script bytecode**
library routine (linked into ~half of all scripts, same 30-flag routine for
all 30 story-event end flags `0x3E9`-`0x406`, 0 ids outside the run),
called via `PUSHI 0x3f7; CALL <routine>` from the Flenceburg magic-school-
hall script. The write itself is the VM's memory-operand ALU family's
**computed-address ("ACC-indirect") bit-store form**: when the instruction
word's address field is all zero, the target bit (`bitBlock + (ACC>>3)`,
bit `ACC&7`) is computed entirely at run time from the accumulator
register, never as a literal anywhere — a genuinely new 4th channel for a
story-flag write, beyond the already-catalogued fresh-literal-call,
computed-argument-call, and compile-time-inlined-byte-poke channels (the
last cracked flag `0x449` the round before). Escalated after 6 exhausted,
genuinely different static negatives (literal-immediate MIPS census,
`jal SetFlag` census, `STOREBIT`/`LOADBIT` operand census, direct byte-poke
census, room-module scan, engine-capability check); independently
re-verified by disassembling the call site, the routine body, and the
native `resolveBitAddr`/`STI`-handler trace fresh from disc bytes (matched
the escalation's citations exactly, including that the resolved bit index
patches the *caller's own stack copy* of the instruction word, not the
bytecode stream — bytecode is never self-modifying here). Confirmed
byte-exact both discs, 48 checks
(`tools/valkyrieprofile/verify-flag-3f7-scene-completion-setter.ts`). See
`negative-from-addressing-root-not-shapes.md` (new worked example) for the
generalizable "a VM's own opcode family can have a computed-address store
form invisible to any literal census — shape-match the consuming routine,
not the value" pitfall.

Reviewing the diff surfaced a stale premise in the already-"resolved"
`vp1psx-slot4807-sacred-phase` row: its closing argument had claimed the
scene-script VM "implements no `GetFlag`/`SetFlag`-shaped accessor at
all" (checked, at the time, only against *native*-code bit-index idioms)
— directly falsified by the finding above. Re-checked the row's actual
conclusion (no scripted setter for flags `0x448`/`0x4CE`) directly rather
than reopening or ignoring the contradiction: a corpus-wide `PUSHI`/
`PUSHI32` literal census for both ids (the only way a constant enters
bytecode) came back clean on disc 2 and, on disc 1, its only 2 hits are
confirmed-by-inspection unrelated actor-placement coordinates. Conclusion
unchanged; premise corrected in place. See
`refuted-premise-does-not-imply-refuted-conclusion.md` for the general
technique.

Same round, independently: the long-standing "two-slot drop-rate"
hypothesis for enemy-stat-record fields `+0x24`/`+0x26`
(`battle-engine-spec.md`) is now known to be wrong for both fields, which
is exactly why it never correlated against published drop lists. `+0x24`
is a percentage threshold-reduction term inside the already-documented
core hit-gate function `fcn.8003a39c`'s "code-12" special-accuracy branch;
`+0x26` gates a `RNG(100)` roll into a real ~32-case post-death "special
behaviour" dispatcher (`fcn.80034838`), structurally disjoint (0 shared
references anywhere in the battle overlay) from the actual item-drop
mechanism, which is `+0x3C`/`+0x3E` (already correctly documented
elsewhere). Verified 78 checks, both discs
(`tools/valkyrieprofile/verify-enemy-record-0x24-0x26.ts`). The
dispatcher's own downstream per-case behaviour remains open
(`vp1psx-enemy-death-dispatcher`).

**Round 163 (2026-09-26) confirms `item-skill-system.md` § 5.7.5's
difficulty-menu column order (`c0=Easy, c1=Normal, c2=Hard`) byte-exact,
closing a long-standing "not oracle-confirmed" hedge, and closes ~10 stale
in-doc cross-references across `item-skill-system.md`/`save-system.md` —
the two files a recurring cross-doc sweep hadn't yet reached.** The order
was previously a plausibility guess with no menu-order trace; resolved by
chaining the title screen's own screen-1 drawer (cursor global
`0x8005d6dc`, the same one every other title sub-screen uses) through the
already-cited difficulty-byte writer (`cursor − 4` = the saved index) to
each cursor-gated UI list's own flavour-text id, resolved via TOC slot 6's
variant-A string table to explicit English naming each difficulty in exact
order — see the new "Cursor-dispatch + save-value arithmetic + string-table
join" technique in `verification-techniques.md` (sourced from here). 44/44
checks, both discs (`tools/valkyrieprofile/verify-difficulty-menu-order.ts`).
The remaining closures were pure `doc-self-cross-reference-before-fresh-
disassembly.md` repair (a stale `§ 12.18` renumbering artifact affecting 4
references, and several bullets whose actual resolutions already existed in
`battle-logic.md`/elsewhere in the same doc but had never been linked back)
— no fresh disassembly needed for those.

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

**VP2 battle *gameplay logic* (not asset formats) is a new thread as of
2026-08-22 — `docs/valkyrieprofile2/ps2/battle-logic.md`.** Unlike VP1,
VP2 has no single "battle overlay" TOC slot to start from; a systematic
census ruled out the main boot ELF, the IOP module chain, and all 120
confirmed `"MWo3"` code overlays (dungeon scripts + 3 UI managers only) as
holding battle code, then found the real lead: two "SL"-chain records
sharing `MWo3`'s header shape but an all-zero magic (`vp2ps2-sle2-shared-
header`, previously only a structural hypothesis) are **confirmed real
compiled MIPS/EE code** — the largest code module found anywhere in this
project for VP2 (2,560 functions, 10.6% float-op density, real cross-refs
into the main ELF). **This is also where this project's R5900 MMI-
disassembly blocker (`game-re-tooling/ps2.md`) got a real general fix**:
Ghidra headless batch analysis (`analyzeHeadless` + stock `BinaryLoader` +
`ghidra-emotionengine-reloaded`'s own `r5900:LE:32:default` SLEIGH
language id, no live GhidraMCP server or GUI needed) decoded 277,453
instructions with zero unimplemented opcodes, where radare2/capstone had
misread the same bytes as DSP-ASE garbage — see `game-re-tooling/ps2.md`'s
new subsection for the reusable recipe. Damage formula/stat records/the
Action-Reaction combo mechanism are all still open; a 14-function
decompiled sample found timer/state-machine, VU0-collision, UI, and spline
code, not yet a damage formula.

**Continuation of the same session (2026-08-23): the gameplay-data model,
text encoding, and master data file are now solved** (9 escalations total
across `ghidra-disasm`/`re-codebreaker`/`re-oracle`), **the damage formula
and a ~579 MB / 1,094-entry mystery TOC population's runtime consumer both
end as real, exhaustively-verified negatives** (not stalls — every
concrete lead, including two independent candidate resource tables found
in the main ELF, was traced to a dead end and independently re-verified
byte-exact before being written up as closed; see `battle-logic.md`
§§ 8-11.4), and a second half of the same session pivoted to pure
structural/statistical analysis (no further disassembly) using the
project's own already-shipped decoders and decoded data as cross-check
oracles — landing several more real, quantified wins: `ECS\0` (a
resource-directory tag) is a named per-character scene-attachment
directory (bone/light/camera-point/shadow/effect names, decisively
cross-confirmed against this project's own already-shipped `MINA` bone
data) sitting atop a much deeper generic recursive typed-value tree
(**108 distinct type tags found**, `groupId` confirmed as a blend-target
index via a touches-per-distinct-element ratio technique — see
`game-re-method/verification-techniques.md`); `ECAF`'s `IDOM` facial
morph-delta format's `deltaB` field is a tangent-plane (not normal)
displacement, confirmed via a properly-null-controlled statistical test
against the record's own paired mesh geometry (also see
`verification-techniques.md`); the master gameplay data file's `+0x20`
section is a 16(tier)×7(growth-stage) stat curve table, not the
originally-guessed 56×2 roster pairing (a within-group-monotonicity
technique, same method doc); and `PAMM` (another resource-directory tag)
embeds a real dungeon/area-name catalog (Seraphic Gate, Yggdrasil,
Dragonscrypt, Dipan Castle, Valhalla, Lezard Valeth, 43 words total,
404/404 real records) under a two-part hybrid cipher discovered by
noticing a flat-shift decode recovered real words each missing exactly
one leading character (`game-re-lessons/near-complete-word-decode-
missing-one-char-is-hybrid-cipher-boundary.md`).

**Continuation, same session: the still-open music-titles join closed
as a real negative, the overlay-slot gap narrowed and partly named, and
the first disassembly of VP2 dungeon-mechanism code.** The `ghidra-
disasm` escalation for the music-title-to-track join (VP1 PSX's already-
solved § 11.8.12 cursor→slot precedent) landed a clean, well-scoped
negative: the debug-menu code that would resolve it is confirmed
code-stripped from this EU retail build (`0/192` nonzero in its declared
text region), and every secondary lead resolves to either the same dead
table or a genuinely unrelated feature (an audio-output options screen).
Separately, the master gameplay data file's own `+0x20` section was
re-solved from a wrong "56×2 roster pairing" guess to a real 16(tier)×
7(growth-stage) stat curve table via a **within-group-monotonicity**
technique (`game-re-method/verification-techniques.md`) — 6 of 10
candidate fields strictly non-decreasing across all 16 groups of 7,
combinatorially decisive. The project's own "18/20 empty ELF overlay
slots" finding was narrowed to 16/20 via a whole-disc scan checking
*every* known container type against *both* known overlay header shapes
(not just the original narrow classifier) — finding real content for 1
more slot, whose 116 files were then named via the overlay header's own
embedded-filename field as exactly 10 real dungeon/area-mechanism
scripts, each duplicated byte-identically across every TOC entry in that
area's own real contiguous TOC-index range (a reusable landmark for
identifying which in-game area an arbitrary mid-range TOC index belongs
to). 3 of those 10 scripts were then disassembled for the first time —
a real, shared C++-style construction/registration convention (a shared
allocator, a vtable-pointer cascade, registration with one global
scene-manager singleton) driving 3 real gameplay mechanisms (a 2-plate
pressure-trap trigger, a teeter-totter using genuine VU0 macro-mode
float physics, a two-phase lazy-spawn countdown hazard) — independently
re-verified by hand-decoding the cited raw MIPS opcode bytes myself
(`game-re-lessons/verify-escalation-artifacts-not-just-claims.md`'s
tenth instance). Full writeup: `docs/valkyrieprofile2/ps2/battle-logic.md`
§§ 6-12.1, `docs/valkyrieprofile2/ps2/data-structure.md` §§ 3.10.11-
3.10.16, §§ 3.12.33-3.12.34, §§ 7.4.1-7.4.2.

**Continuation, same session: 2 more dungeon-mechanism scripts traced
(5/10 total), a real Ghidra headless tooling gap found+fixed, and the
`onoda`/`onodb` lead fully solved.** A second `ghidra-disasm` escalation
extended the shared construction/registration template (§ above) to
`SPWorldMap.bin` (the overworld travel/warp-point screen, a confirmed
7-record travel-node table) and `SPPillerManager.bin` (a multi-pillar
coordinator driving a confirmed textbook LCG PRNG,
`x=x*1664525+1013904223 mod 900`) — every claim independently
re-verified byte-exact by hand-decoding raw MIPS opcodes, sharpening the
prior pass's "indirect virtual call" into a real, traced two-level
vtable dispatch. Along the way, found and fixed a real, generalizable
Ghidra tooling gap: headless auto-analysis's Function Start Search
misses the true entry point on a raw `BinaryLoader` import with no
declared entry point (it only finds functions reachable from an
existing entry/call-target, and a raw code blob has neither) — fixed
with a one-line post-script forcing `disassemble()`+`createFunction()`
at `getMinAddress()+0x80` (`getImageBase()` returns 0 for a raw
import). See `game-re-tooling/ps2.md`. Separately, the `onoda`/`onodb`
lead (short lowercase strings found near a `PAMM` record's own
embedded `FIS\0` tag, resistant to every text cipher tried and left as
"a real, caught-in-time overclaim, not a solved mystery" after 2 prior
passes) was solved not by new disassembly but by re-reading a **sibling
shared-decoder module's own pre-existing doc comment**:
`tools/shared/ps2-fis-image.ts`'s module doc already named a field at
chunk-descriptor offset `0x14-0x19` as "a short ASCII exporter-session
tag," found during an unrelated earlier CLUT/sub-palette investigation
and never cross-referenced against the `onoda` thread — despite an
exact numeric match (the tag sits exactly `0x14`/20 bytes past the
`FIS\0` magic in both contexts). Whole-corpus verification (own script)
confirmed it decisively: all 23 distinct `PAMM` content templates match
this field position with zero deviation, cross-corroborated against all
126 real, ordinary `FISP`/`NOCI` textures elsewhere on disc carrying
the identical field under a different tag family (`"JOHN"`) — a real
disc-wide developer/exporter-tool session-tag convention, not game
text and not `PAMM`-specific, which is why no cipher ever matched it.
See `game-re-lessons/doc-self-cross-reference-before-fresh-
disassembly.md`'s fourth addendum for the generalized lesson (the
cross-reference gap was in a shared-library source doc comment, not a
findings-doc section — this project's fourth confirmed hit on the same
root pattern). Full writeup: `battle-logic.md` §§ 12.2-12.3,
`data-structure.md` § 3.10.17.

**Arc conclusion, same session: all 10/10 `SP*` dungeon scripts traced,
a real inlined-C++-constructor-chain pattern found, one hybrid-cipher
misattribution self-corrected, and the shared singleton's field layout
censused whole-corpus.** The remaining 5 scripts were traced the same
way (independently hand-verified, not trusted from escalation reports
alone), surfacing a genuinely new structural pattern: what earlier
passes called "a vtable-pointer cascade" is really a **multi-level
inline vtable-write chain** — 2-5 sequential writes to the same object
field, only the last one live, consistent with an inlined C++
multi-level base-class constructor sequence — confirmed byte-exact
(every value, every instruction offset) on 2 independent files. A real
self-correction along the way: a 41-entry string table initially
characterized as "a new hybrid-cipher item/menu bank matching `PAMM`'s
own cipher" turned out, on closer inspection, to be an ordinary
instance of this project's **already-solved** `mcps2lib` bank format
(just the first one found embedded in a compiled overlay rather than a
`ZLS\0` container) — corrected in place once noticed, not left standing.
A separate near-miss false negative (a claimed LCG PRNG that a
`MULT`/`MULTU` opcode census found zero evidence for, resolved by
hand-tracing a real compiler strength-reduction shift/add chain instead
— see `game-re-lessons/narrow-opcode-form-census-false-negative.md`'s
newest addendum) and a whole-corpus shared-singleton field census
(ranking candidate struct fields by cross-file recurrence across all 10
files, validated by reproducing 2 already-known fields before trusting
new ones — see `game-re-method/verification-techniques.md`'s "Cross-file
field-recurrence census" section) both round out the arc as reusable
technique, not just per-file findings. Full writeup:
`battle-logic.md` §§ 12.4-12.17.

**Later session: mesh-pipeline masked-normal + alphaBlend wiring closed,
SEQW top-level audio taken from 95/184 to 184/184, TOC `unused` field
narrowed.** `tools/shared/ps2-fps-mesh.ts`'s masked-`UNPACK` "1-component
normal stream" (previously degenerate all-zero output) is now resolved to a
real constant per-batch normal read from the immediately-preceding VIF1
`STROW` register, trying both an int16-scaled and a plain-float32
interpretation and keeping whichever gives unit magnitude — 5,041/5,041 real
masked batches whole-disc (`game-re-lessons/unit-magnitude-oracle-
disambiguates-numeric-encoding.md`). `tools/shared/ps2-mesh-gltf.ts`'s
already-decoded per-batch `alphaBlend` field is now wired into a composite
texture+blend material key (previously computed but never consumed) — 352
BLEND materials / 152 mixed BLEND+MASK records across a 401-record sample.
Separately, `tools/shared/ps2-seqw-audio.ts`'s top-level `seq` TOC sample
table — documented as a fixed 28-byte-stride record from an earlier
285-record sample — was found to be genuinely self-describing variable-
length (a real minority of records are 48/52 bytes, not 28); walking by
cumulative declared size instead of a fixed stride took real-corpus coverage
from 95/184 to 184/184 top-level entries
(`game-re-lessons/self-describing-length-field-mistaken-for-corpus-
constant.md`). A follow-up on the TOC `unused`/cumulative-sector-count
field's 165 non-participating entries refuted its own "second hidden
mega-block" hypothesis (159/164 looked byte-contiguous sorted by offset, but
2,683/2,685 already-known *participating* entries also fell in that same
span — a small-sample-contiguity artifact, not a boundary;
`game-re-lessons/subset-contiguity-needs-complement-check.md`) and instead
found a real, zero-deviation `[u32 count][u16 offset,u16 length]*count`
self-describing index-table header on 85/93 candidates — narrowed, not
closed. Full writeup: `docs/valkyrieprofile2/ps2/data-structure.md`
§§ 2.8-2.9.1, § 3.12.31, § 3.12.37.

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
full per-call-site census left as future work), not a stall.

> **Update (2026-09-04): the per-call-site census, done — 79/204 (39%)
> literal, not 1/204.** A general classifier
> (`build/cache/valkyrieprofile-psp/census_getentrysize_calls.py`) walked
> every one of the 204 call sites across all 8 modules and recovered 79
> real literal PFS indices (span `1`-`4933`, several recurring identically
> across modules — shared/common resources), splitting the rest into
> `load-other-base` (49, a newly-distinguished shape: a temp/return-value
> register base, not a saved local), `struct-field` (40, extends the
> already-known cached-per-object-field pattern to more offsets),
> `register-passthrough` (33), and genuinely `unclassified` (3). A real
> classifier bug was found and fixed mid-pass: a naive backward scan
> missed the common `jal <stub> ; addiu $a1,zero,N` **delay-slot** idiom
> and could misattribute an *earlier, unrelated* call's own delay-slot
> argument as the one being classified — fix: check the delay slot
> explicitly first, and stop the backward walk the instant it crosses an
> earlier call's own delay-slot boundary rather than classifying anything
> found there. One recovered literal (`Battle_master.prx` vaddr
> `0xe6104`, index `1985`) is a real PSP-side code site using the *other*
> of VP1 (PSX)'s two ambiguous "1985/1987" candidate values for the
> 13th (`roki`) combat-clip slot — flagged as a lead for that PSX-side
> question, not resolved on the PSP side. Full writeup:
> `docs/valkyrieprofile/psp/data-structure.md` §7.7.

**`BOOT.BIN`'s own two static `.pmf` movie-name tables are SOLVED,
byte-exact (2026-09-04)** — settling `vp1psp-summon-movie-hypothesis`
outright. Both tables are `[u32 namePtr, u32 value]` 8-byte records over
one shared, tightly-packed NUL-terminated string pool; located by finding
every 4-byte-aligned word matching a discovered `.pmf` string's vaddr,
then the longest 8-byte-stride run (table 1: **sequential** string-pool
order distinguishes it from table 2, whose records point at the same
pool in a *different* order — an unordered-only first pass had merged
both tables into one 137-entry run before this distinction was added).
Table 1 (74 records) names every one of `moviepac.dat`'s own 74 movies,
`value` = byte offset, **74/74 exact match against that file's own
internal directory, 0 deviation**. Table 2 (63 records) names legacy
`PSPVAL1.PFS` STR-video entries, `value` = PFS directory index — 2 of its
entries independently match this project's own already-confirmed legacy
STR-video PFS indices, and its 13 short single-word names (`absol.pmf`,
`efreet.pmf`, `roki.pmf`, ...) are a **13/13 exact numeric match** against
VP1 (PSX)'s own already-confirmed "13 version-2 combat-clip STR video"
id set — an independently-derived number (PSX-side disassembly idiom
scanning vs. PSP-side pure string/pointer-table scanning) agreeing
exactly, this project's own "two independently-located tables agreeing
on a specific number" oracle. **Settles the open question decisively**:
the PSP port's short "summon-sounding" movie names are VP1 (PSX)'s own
already-solved dungeon-mechanism/combat-clip STR videos, reused
byte-compatibly and finally named — **not** a PSP-exclusive
pre-rendered-FMV replacement for 3D spell effects (directly relevant to
the PSX-side `vp1psx-3d-spell-effect-representation` investigation,
independently closed the same day as a structural negative for any
asset-table-driven spell VFX — see the PSX section above). New shared
module `tools/shared/psp-vp-boot-movie-names.ts`, 6/6 tests. One of
table 1's own consumer functions (`RegisterMovieCatalog`) was first
mis-traced as having zero static callers — the real bug and fix are a
generalizable MIPS trap, see
`game-re-lessons/file-offsets-vs-segment-relative.md`'s 5th
manifestation. Full writeup:
`docs/valkyrieprofile/psp/data-structure.md` §5.0.

A secondary
finding located `moviepac.dat`'s missing audio (open item since the first
pass): a manual PES start-code census found 313 `0xBD` (`private_stream_1`)
packets per movie sample with a consistent sub-header shape — the same
"audio hides behind a nonstandard PES stream id" pattern this project's
VP2 (PS2) FMV audio already hit (§2.10.2 above), confirming the technique
transfers across platforms within this project; the codec inside the
payload (plausibly ATRAC3+) is still unidentified. Full writeup:
`docs/valkyrieprofile/psp/data-structure.md` §7 (new), §5.2 (audio
update), `docs/valkyrieprofile/TODO.md`.

**Third pass (2026-08-23): moviepac.dat audio solved and pipeline-wired;
the group-directory container confirmed reused byte-for-byte for ~39% of
raw PFS entries; a whole class of character art SOLVED via `re-
codebreaker` after this project's own width-sweep stalled.**
`moviepac.dat`'s audio is real **ATRAC3+ in PSP's standard `sceMpeg`
private-stream-1 framing** — identified from PPSSPP's own
`Core/HW/MpegDemux.cpp` source (a generic ffmpeg-devel mailing-list
convention was tried first and did *not* match this game's real bytes,
reinforcing "verify against the exact target, not a same-era generic
reference"): each 384-byte PSP mux slot is `0x0F 0xD0` sync + 2 size-code
bytes + 4 still-unresolved bytes + a 376-byte raw ATRAC3+ frame with no
sync/header of its own (confirmed against `libavcodec/atrac3plusdec.c`,
which has none). Wrapped in a hand-built 96-byte Sony EA3 container
(fields derived from `libavformat/omadec.c`) and decoded via ffmpeg's
stock `oma`/`atrac3plus` support to verified non-degenerate PCM (lag-1
autocorrelation 0.976). New shared module `tools/shared/psp-atrac3p-
audio.ts`, wired into the real pipeline — confirmed on a live run, 6/6
sampled movies export with real `h264`+`aac` muxed. **Genuinely different
from PSX**, not reused: PSX's own FMV audio is hardware CD-XA ADPCM, no
software codec at all.

VP1 (PSX)'s § 9.3/§ 9.6.10 nested `{count,field1,{regionType,regionSize}}`
group-directory sub-index container (see the PSX section below) is reused
**byte-for-byte, unmodified**, for a real 38.9% (1,761/4,525) of PSP's raw
`PSPVAL1.PFS` entries — verified all the way down to real content, not
just container-mechanism resemblance: nested `SLZ` regions decode
correctly, and a `0x1600`-tagged region cross-decodes with the
**unmodified PSX** `parseEnemyStatRecord` reader to 996/996 plausible
enemy records, the exact corpus size PSX's own pass independently
confirmed. Promoted to `tools/shared/vp-group-directory.ts` (moved out of
the PSX-only `tools/valkyrieprofile/vp-corpus.ts` once confirmed
cross-platform). A second, real cluster in the same raw-entry population
is confirmed **not** this format — a genuinely different, PSP-specific
~88-byte header — giving this pass's PSX-vs-PSP comparison both a
"reused verbatim" and a "redesigned" data point from the same
investigative thread.

**The 25 same-size "sparse tail" raw entries — SOLVED by `re-codebreaker`
after this project's own width-sweep found no discriminating width.** A
prior pass had confirmed (via an alpha-channel statistical test) that the
first 1,024 bytes of each entry was "RGBA8888, width undetermined" and
left the remaining ~53,760 bytes "sparse, low-entropy, unidentified" — an
escalation brief laid out the full paths-tried table (RGBA8888 whole-blob
and region-isolated, ADTS AAC, all refuted for the tail) and asked what
the tail actually was. **The premise itself was wrong, not just the
search.** The "1,024-byte image at an undiscoverable width" was a
256-entry RGBA8888 **CLUT** (a palette and 256 RGBA8888 pixels are
byte-identical — see `game-re-lessons/rgba-clut-vs-image-byte-identity.md`,
harvested from this exact escalation), and the "unidentified 53,760-byte
tail" was simply the rest of a **256×256 8bpp palette-indexed bitmap**
through that same palette (`1,024 + 256×256 + <2048 padding = 67,584`,
exact). All 25 entries render as VP1's 25 playable characters' portraits,
**in the game's own already-confirmed 25-name playable-roster order**. A
whole-archive scan generalizing the shape found a second, previously
unnoticed population too: 27 entries of 512×512 buffers each holding a
real 480×272 (the PSP's exact native screen) full-screen character
artwork. New shared module `tools/shared/psp-vp-clut8.ts`, plus a
re-runnable whole-archive verification script
(`tools/valkyrieprofile/psp-verify-clut8.ts`) — independently re-run
after the escalation (9/9 structural checks pass on real disc bytes), 3
portraits + 1 artwork visually confirmed by name, and the claimed
`Camp_master.prx` reader call sites (a bare literal `4906`, and `(x % 5)
+ 4767`) independently re-disassembled and confirmed byte-exact before
trusting any of it. Corpus-bounding check: 0 of 327 `SLZ`-compressed
entries hold this format (the one palette-shaped `SLZ` hit is a
already-solved PSX TIM).

**Those 27 artworks' consumer is now SOLVED on both platforms (2026-09-24,
`re-oracle`; psx `docs/valkyrieprofile/psx/data-structure.md` § 18.24, psp
§ 9.3 correction block).** A "hardened, exhaustive negative" (§ 18.23: four
static searches over 1,530 nested code sub-blocks + 8 top-level overlays +
both boot executables, 0 hits for PSX TOC slots 4772-4793) was overturned —
the consumer sat in TOC slot 1, inside that corpus, as a **35-record
16-byte-stride per-character descriptor table** (`0x8005ff90`, plate at
`+14`, voice-clip first/last slot at `+10`/`+12`, thumbnail tpage/CLUT row
before that) read via the `lui/addu/lh` indexed idiom and carried to the
loader in a task object's `+0x10` field by a materialised-address callback;
see `resource-id-in-strided-record-field-carried-by-callback-object.md`
(sourced from here). The screen is the title menu's **Sound Mode → Voice
Collection** viewer (named from TOC slot 6's own string bank via the widget
lists drawn on the way — "Sound Mode"/"Voice Collection"/"Open voice"), a
7×5 grid with one plate per roster member in the game's roster order (25/25;
22/22 agreement with the PSP pass's earlier by-eye subjects; per-character
unlock at `heard*100/total == 100` voice clips). Only 4771 is absent (the
`(rand()%5)+4767` disc-swap pool is its sole consumer); 4787 is a 34th,
non-roster cell. The PSP twin (`Title_master.prx` vaddr `0x3841a`, 28 × 16 B,
identical 25 slot numbers in identical order) is that script's positive
control. Verify: `tools/valkyrieprofile/verify-voice-collection-character-art.ts`
(both discs, 55 exact instruction words) and
`verify-character-intro-psp-oracle.ts`. Also corrected in passing:
`save-system.md` § 11.3's "one-shot boot memory-card screen" reading of
`moduleDesc+0x0c` (`0x8003bc84`) — it is the **title screen's per-frame main
loop**; `u8 0x8005e041` is the title sub-screen selector (0 title menu, 1 New
Game difficulty, 2 memory-card load, 3 Sound Mode, 4 Configuration, 5 Voice
Collection) with paired jump tables `0x80051b9c` (drawer) / `0x80051bb4`
(constructor), and `0x8005d6dc` is the cursor into a 48 × 32-byte UI-record
table at `0x8005f888` (`+0` confirm fn, `+4` cancel fn, `+8` left/right fn,
`+0xc..+0x12` neighbour links, `+0x14`/`+0x16` x/y). Open residue:
`vp1psx-voice-collection-extra-cells` (subjects of 4771/4787, the 8
plate-less voiced cells, persistence of the 1,536-bit heard-bitfield).

Tracing `*_master.prx`'s ~200 remaining table-driven `GetEntrySize` call
sites (the census left open by the second pass) found they are a
**family of >=4 distinct index-sourcing shapes**, not one mechanism —
a real static lookup table (one instance fully decoded: a 10-byte-stride
`Field_master.prx` table, with a conditional `+1124`-index branch
confirmed to resolve to a real byte-identical duplicate asset, though
that local duplication does **not** generalize archive-wide — a
corpus-wide sweep found only noise-level matches, refuting a tempting
"systematic PSX-disc1/disc2-inherited duplication" theory), a "compute
once via the table, cache into a per-object struct field, other call
sites just read the cache" pattern (two different struct offsets seen),
and a plain global variable read. Full writeup:
`docs/valkyrieprofile/psp/data-structure.md` §5.3, §7.6, §9.1-9.3,
`docs/valkyrieprofile/TODO.md`.

**Continuation (2026-09-04): the 996-record cross-decode above is now a
fully closed, named, wired battle-data population — and the reused-format
hypothesis turned out to preserve exact numeric addressing too, not just
codec/container shape.** PSX locates its "reference alphabet" (the glyph-
order chart that bootstraps every subset-font text decode, see the VP1
PSX section above) at TOC slot 6 and its enemy name table at TOC slot
1500; on PSP the analogous resources sit at the **numerically identical**
`PSPVAL1.PFS` index 6 and index 1500, inside a completely different outer
container (ISO9660 + a custom PFS archive vs. PSX's raw encrypted sector
TOC) — confirmed by direct decode (0/25 mismatches against the
independently-derived 25-name playable roster, real enemy names like
"Undead Carcass" and "Dragon Servant"), not assumed from the slot-number
coincidence alone. This closed all 996/996 enemy stat records (414
bundles) with every unit named, and — reusing PSX's `decodeBattleBundle`
-> `parseBattleAnimBlock` -> `buildPatchSet` -> `composeAnimFrame` ->
`packAtlas` battle-animation pipeline completely unmodified — composited
10,941 real creature battle-animation sprite sheets (443 confirmed-
creature bundles of 1,647 textured / 1,761 candidate, 3,898 real TIM
textures), visually verified non-degenerate at corpus scale (a coherent
dragon/lizard walk cycle, a hydra-type creature, a tentacled horror). One
deliberate scope cut: PSX's disc-wide cross-bundle patch-page supplement
index was not ported, so PSP's own-bundle-only patch resolution reaches
95.3% (1,324/1,389) vs. PSX's 99.9% — tracked as
`vp1psp-battle-anim-supplement-index`. See
`game-re-lessons/port-preserves-bootstrap-resource-slot-numbers.md` for
the general technique this pass confirmed: once a container/codec reuse
is confirmed byte-identical across a port, the next near-zero-cost check
is trying the *old* platform's own special/bootstrap-resource index
numbers directly against the *new* container, before any structural
re-derivation. Full writeup: `docs/valkyrieprofile/psp/data-structure.md`
§10, `docs/valkyrieprofile/TODO.md`.

**Room/dungeon background compositing — CLOSED, a third confirmed instance
of the same slot-number-reuse pattern (2026-09-04).** PSP's room
containers are VP1 (PSX)'s own §9.6.11-9.6.16 group-directory room format,
byte-for-byte, at the identical `PSPVAL1.PFS` index as the PSX TOC slot
number. Verified the strong way — a real render + byte-diff against
PSX's own already-shipped output, not structural resemblance alone: all
1,118 PSX-confirmed rooms and all 901 extra-frame (parallax/content-
animation) atlases render **0 bytes different** via the unmodified PSX
`tools/shared/psx-vp-room.ts` compositor fed PSP bytes. Per-room names
transfer too (1,118/1,118, via the same PFS-index-6 reference-alphabet
convention §10.1 already established); PSX's separate dungeon-map
*area*-name join does not (PFS index 4734 is a genuine zero-length entry
on this disc — tracked as `vp1psp-room-area-names`). New:
`tools/valkyrieprofile/psp-room-data.ts`; `collectRoomExtraFrames`
promoted PSX-build-assets-local -> `tools/shared/psx-vp-room.ts`, and
`psp-battle-data.ts`'s `openPspArchive` promoted -> `tools/shared/
psp-vp-pfs.ts` as `openPspArchiveFromIso`, both now that a second (PSP)
consumer needed them. Full writeup: `docs/valkyrieprofile/psp/
data-structure.md` §12.

**Dialogue/script/menu text (`vp1psp-text-tables`) — base decode SOLVED,
not yet pipeline-wired (2026-09-26).** Generalizing the already-confirmed
enemy-name font/text tag pair (PFS index 1500, `0x300810`/`0x300910`) into
a per-PFS-entry census, reusing VP1 (PSX)'s own `pairFontsWithText` pairing
logic **completely unmodified** (it turned out to be entirely
container-agnostic — see `game-re-lessons/
port-preserves-bootstrap-resource-slot-numbers.md`'s "second instance"
addendum, sourced from here), finds **1,140 font+text pairs / 37,955
decoded strings** across `PSPVAL1.PFS` — including all 1,118/1,118
already-confirmed room entries' own dialogue text (room *background*
compositing had already transferred byte-identically, §12 above, but
nobody had looked at room *text* until this pass) plus the room-name bank
and every menu/item/skill string bank. Verified byte-exact against PSX's
own already-shipped `extractTextResources` decode of the identical
TOC-slot/PFS-index number on 8 sampled slots spanning both content shapes
(scene-script dialogue vs. plain variant-A menu tables) and all 3 pairing
rules, plus a null control (0 pairs at a code-overlay entry) and a
corpus-scale positive check. New: `tools/valkyrieprofile/psp-text-data.ts`
(`collectPspTextResources`, the reusable module) + a standalone verify
script + 8 real-disc vitest tests. Not yet wired into Stage 1/2 (no JSON/
manifest output shipped) — that's the next mechanical step. Full writeup:
`docs/valkyrieprofile/psp/data-structure.md` §13.

Remaining open PSP gaps: the supplement-index cross-bundle patch closure
above, audio format compatibility (`vp1psp-audio`), the dungeon-map
area-name gap noted above, and 3D model geometry (`vp1psp-3d-models`) —
none of the latter three investigated yet.

**VP1's `src/engine/` browser-runtime battle engine** (a real MIPS-derived
implementation, not just format docs — `battle.ts`/`realtime.ts`/
`commands.ts`, evidence trail `docs/valkyrieprofile/psx/battle-logic.md`
§1-42) has all 24 command codes + specials 32/46 traced and classified, and
now models all three real trigger classes an engine needs: action-commit,
per-landed-hit rider, and — closed this session (§42) — genuine per-frame
`unit+0x08` tick handlers. Of the four codes flagged as tick handlers, only
code 0 "First Aid" needed new runtime behaviour: it's an autonomous
background scan (`RNG(100)<15` per living First-Aid holder per frame,
CATEGORY_CHECK-gated), not action-triggered at all, with a confirmed
76-frame arm-to-fire delay before its already-known `HP += maxHP*3*P/100`
lands — modelled as a new `'tick'` `CommandTrigger` alongside `'action'`/
`'hit'`/`'none'`. Codes 8 and 10 turned out to need zero new engine
behaviour (a presentation-layer projectile-travel delay around an
already-modelled attack, and a purely cosmetic facing flag, respectively);
code 46's two tick sites are narrowed to a small residual
(`vp1psx-code46-tick-handlers-not-fully-closed`) rather than fully closed.
Sourced `spawner-install-literal-outranks-backscan-prologue.md`: a
pooled-instance handler's true entry point was mis-scoped by manual
back-scanning and only caught by finding its *spawner's own* literal
`sw <handlerAddr>,0(inst)` vtable-install instruction, which names the
real address directly and is authoritative on a fixed-width ISA where two
different back-scan candidates can both disassemble as plausible code.

**VP1's field engine per-frame position-integration commit — CLOSED
(2026-09-19), plus a scene-script actor-command sweep, a battle-arena
effect-seat table, and a save-preview/PocketStation icon closure.**
`FUN_80039b5c` (`actor.x += actor.velX`; `actor.y += actor.velY +
actor.gravityVelY`) evaded three independent register-tracked/call-graph
dataflow scans because it biases its own base register (`addiu
$a2,$t0,0x98`) before addressing fields, so the literal displacement bytes
`0x94`/`0x98` never appear in the function body — see
`game-re-lessons/struct-field-scan-blind-to-biased-base-pointer.md` for the
general trap and the forward-symbolic-offset fix that finally found it (a
`re-codebreaker` escalation). Ported to `src/engine/field/
room-collision-response.ts` (`integrateActorPosition`), including a
"slaved to another actor" variant, now wired into `src/engine/field/
index.ts`'s barrel for the first time. Same session: all 16 field
scene-script actor-command opcodes plus the `EVENT_CG` hook module traced
and closed (`docs/valkyrieprofile/psx/scene-script-vm.md` §16); the battle
arena effect-seat allocate/claim table promoted from engine stub to native
(`src/engine/interpreter/hooks.ts`); the save-preview vs. save-icon
confusion resolved as a PocketStation mono-icon, not a second preview
render (`docs/valkyrieprofile/psx/save-system.md` §3.2c); and a `baseArg`
self-pointer re-entrancy chain traced to two real overlay-reload call
sites (`docs/valkyrieprofile/psx/battle-logic.md` §80). Sourced
`lui-addiu-negative-low-half-borrows-from-high-half.md` (an eyeballed
`lui`/`addiu` pair read one page high, caught by re-deriving the address
programmatically). After ~17 TODO rows closed/narrowed across this and
adjacent sessions, a strict read-only backlog re-triage (all 92
`docs/valkyrieprofile/TODO.md` rows plus a stub/TODO grep of `src/engine`/
`src/battle`) concluded VP1 PSX's tractable, static-analysis-solvable
gameplay-logic backlog is now **exhausted** — every remaining open row is
either cosmetic/content-identification residue (portrait/character-art
naming, audio/text bookkeeping with no gameplay consumer) or explicitly
blocked on live capture, a real memory-card image, or a human
architectural decision, each already stating its own "needs X". Don't
dispatch a fresh (b)-category `game-re` pass against this project without
either a new lead or one of those blockers lifting.

**`vp1psx-battle-arena-3d-resident-matrix` fully CLOSED** after an
extended, ~15-round static-only dispatch chain (`docs/valkyrieprofile/psx/
battle-engine-spec.md` §12.13-§12.13a.J): the resident GTE matrix's four
projection inputs, its predecessor-overlay, its install mechanism, a
room-transition bulk-clear, and — the final residual — whether the
resident task pool's own backing memory survives a battle round-trip. The
last piece closed on a cold-boot tagged-pool-slab allocation (a
previously-blank tag in an already-documented cold-boot allocator table
turned out to be exactly this pool, confirmed by direct disassembly of
both the `malloc()` call and its tag-registration/publish routine) plus a
**null-controlled** corpus-wide free-scan: the same free-detection
technique was first proven to find a real, known "frees this global
directly" instruction sequence elsewhere in the same function before being
trusted for a zero-hit result on the pool's own base pointer — the kind of
positive-control discipline this project's chain has leaned on repeatedly
(see `negative-from-addressing-root-not-shapes.md`'s own "single cheapest
way to test any zero-hit negative" section) and which is what let a static
"never freed anywhere" negative be shipped as **provably safe**, not merely
presumed. The pass also caught a real, project-wide tooling gap: the
standard nested-code-block corpus builder several prior rounds' widened
censuses were built on silently drops any overlay whose first decoded
chunk doesn't start on a function boundary (an `isPrologue(word0)` gate) —
which is exactly why a repeated "0 write sites" PASS across multiple
rounds had never actually seen the one overlay that mattered. See
`game-re-lessons/nested-block-census-isprologue-gate-drops-non-function-aligned-chain-link.md`.

**`vp1psx-portrait-scene-script-join` fully CLOSED** (round 120,
`docs/valkyrieprofile/psx/data-structure.md` §17.14) — one of the exact
"portrait/character-art naming residue" rows the prior backlog-exhaustion
note above flagged as cosmetic/content-identification, not gameplay logic.
A `re-oracle` escalation (after a static fresh-angle pass motivated by a
same-day sibling finding — GODCAMP's own text-control-code grammar hides
a computed `arg+K` TOC-slot accessor a literal/table census can't see —
came up clean but informative) found the real bug wasn't in the game: the
project's OWN naming helper only paired a portrait push with a speaker
name when a specific text-call opcode followed it, and a subset of rooms
drew dialogue with a sibling opcode family the helper never modeled, so 8
real, already-censused portrait pushes were misfiled "unreferenced" for
several rounds; a 9th (a lone stack-form "runtime variable" reading) was
really a script-local function's own parameter, its 11 real call sites all
literal. 19 of 37 previously-"unreferenced" slots were real references all
along (pipeline bug, now fixed + regression-tested); the residual 18 are a
well-supported unused-content verdict, not a further search gap. Two
generalizable lessons sourced from here: `game-re-lessons/reference-census-
built-from-named-output-not-raw-pushes.md` (new) and a sharpened
`runtime-valued-script-operand-is-usually-a-parameter.md` (a single
ambiguous stack-form occurrence deserves the same "is this really a
callee's own parameter" check a large inflated count would trigger).

**`vp1psx-room-layer-placement` fully CLOSED** (round 123,
`docs/valkyrieprofile/psx/data-structure.md` §§ 9.6.13/9.6.50) — the last
two open sub-items on this row. (1) The room scroll-record `kind` enum's
individual numeric values (0/10/20/130/140/150 + free-choice "extras") were
named not by more per-call-site disassembly (already exhausted) but by
finding the record's own already-decoded placement `order` field is an
EXACT function of `kind` — `order = 17*floor(kind/10)+kind%10`, 0 deviation
across 25,287 non-main placements, both discs — byte-identical to an
already-documented repack rule for an unrelated subsystem
(`SPAWN_PLATFORM`'s own `kind` parameter), pinning `kind` as a shared
project-wide depth/z-order-slot numbering rather than ad-hoc content tags.
New lesson: `game-re-lessons/enum-value-named-via-cross-subsystem-formula-
reuse.md`. (2) The scroll record's `flags` bit 2 — twice-negative under
literal-offset and then bias-agnostic idiom-complete bit-mask censuses —
was closed by a `re-oracle` escalation that found the two remaining false-
negative causes (a value-consumer census must root taint on a pointer's
*publish* `sw` sites as well as its loads, and must scan each function to
its real end, not the first `jr ra`) and, once those were fixed, closed the
question two ways at once: a complete non-runtime explanation (bit 2 is
set iff the record's index is 6..n-2, a pure positional "extra record"
marker, 0 deviations on 16,112 records) plus an independent second-
compiler oracle (the PSP recompile `Field_master.prx`, built by a
different MIPS toolchain, reproduces the identical zero-consumers result).
Two new lessons: `game-re-lessons/dataflow-census-root-must-cover-publish-
sites-and-full-function-body.md` and a sharpened
`cross-platform-decode-oracles.md` (same-source-port-as-second-compiler is
also a code-absence oracle, not just a table-role oracle).

> **Update:** "fully CLOSED" above was premature — round 124 reopened the
> same row name (`vp1psx-room-layer-placement`) for a new, unrelated batch
> of residual items (the `TASK` table's room-resolved entries), worked
> across rounds 124/125/127/128/129 and fully closed again in round 129
> (`docs/valkyrieprofile/psx/data-structure.md` § 9.6.55). That final round
> also produced two account-wide lessons worth noting here since they were
> found on this project: `unreachable-return-explained-by-self-overwriting-
> overlay-swap.md` (a PSX field-overlay cutscene controller's `jr $ra` was
> genuinely unreachable — both by linear disasm and a CFG walk — because it
> terminates by handing off to a confirmed overlay-swap primitive that
> overwrites its own code region) and `static-image-zero-dump-refutes-
> authored-template-hypothesis.md` (two "GPU template bank" structures
> turned out to be all-zero at rest on both discs, inside a documented BSS
> zero-run — settling a two-round-old "decode the full field content" open
> item as dissolved rather than answered). This is a recurring shape for
> this row specifically: a TODO row gets closed, then a *later, structurally
> unrelated* discovery reopens the identical row name rather than opening a
> new one — worth checking a row's own history for this before assuming
> "CLOSED" notes in this file are current.

**Round 130 (`vp1psx-asset-naming-classification`, `game-re`) closed the row's
last open item, both halves.** Part A: `collectBattleSpriteBundles`'s
"raw-other TOC slot + any nested SLZ-wrapped TIM found anywhere" gate was a
real classifier false positive, not just a documented over-count — it swept
1,123 already-solved room/field slots (923 mapped + 195 town/story rooms +
5 object-model slots) into the battle-sprite-bundle population purely
because rooms and object-model bundles also legitimately embed their own
SLZ-wrapped TIM textures. Fixed by excluding any candidate that
independently passes `collectRooms`'s own room-decode acceptance test
(`regionType` 2 TIM + `regionType` 0 header/scroll/layer-directory + >=1
composited layer) or is a confirmed object-model slot — not by adding a new
positive discriminator to the offending classifier. Population dropped
1,669→541, 0 residue in range on either disc. See
`individually-failed-fixes-may-combine-cleanly.md`'s sibling lesson,
`sibling-classifier-exclusion-via-already-solved-acceptance-test.md`
(new this round). Part B: STR/FMV video clips have no on-disc title at all
(confirmed at the code level too — the Great Magic debug menu renders its
element as a bare `sprintf("%d", elem)`, not a name), but the room whose
scene script triggers a dungeon-range clip (opcode 196 direct, opcode 211's
`videoSlot-1` companion) already has a real name/dungeon (§ 9.6.17/18) —
joined into a real *location* for 87/92 clips across both discs, the same
technique already used once for battle-arena backgrounds (§ 12.16f). One
slot (3578, disc 1) is a genuine two-location clip (a direct trigger from
one room and a companion load from an unrelated other room), correctly
left unresolved rather than guessed — see
`traced-enum-label-corroborated-by-carrier-name-set.md`'s new "direct
trigger binding" variant. Both verified end-to-end from raw disc bytes,
both discs: `tools/valkyrieprofile/verify-battle-bundle-room-overlap.ts`
(11/11) and `verify-str-video-location-names.ts` (9/9). TODO row deleted.

**`vp1psx-scene-script-opcodes`'s field-actor flag word (`obj+0xe4`/`obj+0xe8`)
narrowed further across rounds 4-5 (2026-09-25).** Round 4 closed bit 11's
two readers (both are landing-impact animation-selection handlers sharing a
table at `0x80080330`, a byte-selector at `0x8007fd7e`, and a `0x201`
threshold) and found `SetAnimation`'s own bit-22 (property 27) "animation
change lock" gate plus its `a2`/"obeyLock" parameter's real semantics
(corroborated by an 84-call-site corpus census); it also widened the
already-hardened bit-12-SET/bit-29 negative to four independently-shaped
static techniques (literal `lw`/`andi` window scan, a from-scratch
register-chain forward-dataflow tracer, an `ori`-based census, and a
same-src/dst corpus filter) and, having earned it, escalated to
`re-oracle`. The escalation closed both bits (plus bonus-closed bit 27's
SET side) via a single shared root cause: `FUN_800367d8` (the field
draw-list walker/animation ticker) biases `$s2 = actor + 0xc8` and
addresses the flag word as `0x1c($s2)`, never as the literal byte `0xe4` --
the third instance of `struct-field-scan-blind-to-biased-base-pointer.md`
in this project, now sharpened with this instance's own failure mode (a
biased hit hand-reviewed and dismissed as "a different field," and a
same-project sibling doc that had already documented the identical sites
under the resolved `obj+0x1c` label a day earlier). Round 5 independently
re-verified the escalation's delivery before committing it -- re-ran its
35-check verify script byte-exact on both discs, found and fixed a real
portability defect (the delivered script read from gitignored
`build/cache/` files instead of deriving the overlay from raw disc bytes;
confirmed the cache was byte-identical first), and confirmed the doc edits
use the project's correction-block convention with no content silently
dropped. `tools/valkyrieprofile/verify-e4-bit12-bit29-oracle.ts` (35/35,
both discs); `docs/valkyrieprofile/psx/scene-script-vm.md` §20 (20.1-20.6).
Round 6 closed `obj+0xe8` bits 6/7 (type-5/type-8 collision-volume
occupancy flags, refreshed every frame via a per-frame dedup global whose
CLEAR side used a sign-extended `addiu`-built mask invisible to every
prior `lui+ori` mask search -- a real, generalizable gap in that search
shape, not just these two bits) and located but did not unravel a
cross-actor `obj+0xe8` reader inside the general per-frame collision
resolver, flagged as "plausibly tied to" the project's slaved-actor
mechanic. Round 7 closed that lead definitively: the reader is the slaved-
actor attach sequence's own "first frame becoming slaved" impulse block
(a block a *different* doc section had already partially transcribed and
flagged incomplete) -- it gives the object being stood on a one-off
buoyancy-style vertical kick if that object is itself sitting in a type-5/
type-8 volume, i.e. landing on a floating platform bobs it. Tracing that
block also closed `obj+0xe8` bit 12 (a script-settable "cannot be ridden"
flag, SETPROP property 53, found via a single-bit-scoped bias-tolerant
census with a positive control) and found a second attach-rejection gate
(the currently-engaged actor can't become an anchor). Both rejection paths
converge on the same detach as "no candidate found at all."
`tools/valkyrieprofile/verify-e8-bits6-7-collision-volumes.ts` (round 6);
`verify-slaved-actor-anchor-buoyancy-e8-bit12.ts` (round 7, 60 words + 2
whole-overlay censuses, both discs); `scene-script-vm.md` §§21-22. Round 16
closed the `*(0x800895d0)` per-frame dedup global's full bit map via a
producer/consumer census requiring store-back (not just a masked test) as
proof of a real SET/CLEAR, resolving the round-6 bit-3-vs-bit-7 asymmetry as
a genuine cross-mechanism mutual exclusion (bit 3 is a wholly separate
signature, exclusively produced by type-4/ladder engagement, not a stray
reference to type-8's own bit 7) -- see
`mirrored-dedup-gate-tests-sibling-bit-not-own.md`.
`tools/valkyrieprofile/verify-e895d0-global-bits-round16.ts` (56/56
accesses, 0 orphans, both discs); `scene-script-vm.md` §31. Two technique
notes worth keeping here: round 18 (`game-re`) hit two generalizable bugs
building a
combined-mask/sign-bit-aware census, `probe-e4e8-round18-census.ts` --
a stale cached `lui` constant surviving an intervening real data load
(fixed via a generic per-instruction constRegs invalidation pass, now the
third instance in `dataflow-chase-must-track-destination-not-mere-
reference.md`) and a systemic blind spot where the whole-overlay bias
tracker treats any earlier `jal`/`jr` as invalidating the caller-saved
`$a1` parameter `SETPROP` handlers address the actor through directly
(`caller-saved-invalidation-misses-parameter-reused-across-call.md`, new
this round) -- and round 19 (`re-oracle`) closed `obj+0xe8` bit 17 -- five
rounds of field-centric censuses had missed its consumer -- with a
constant-first (mask-centric) census,
`tools/valkyrieprofile/probe-e8-bit17-mask-census.ts` /
`verify-e8-bit17-round19.ts`; `scene-script-vm.md` SS 33 and SS 33.12,
`field-centric-bit-census-blind-to-sibling-reuse-and-split-mask.md`.
**Rounds 20-26 (2026-09-26) closed the remaining `obj+0xe4`/`obj+0xe8` bit
space in full, including the row's own longest-running item (a 54-site
`obj+0xe4` bit-3 reader-site census, open since round 15, fully resolved
round 25 via a new iterative backward/forward `jr $ra` boundary-resolution
technique -- see `spawner-install-literal-outranks-backscan-prologue.md`'s
own "nearest preceding `jr $ra`" variant, sourced from here) and round 26's
mop-up of every remaining named function (a per-object command-queue drain
loop, a container-task cancel routine, a script-interpreter-expression-
stack consumer misdescribed as "a small FIFO queue" in round 25's own
prose, a status-code's full consumer set, and a container-opening debris-
particle task's own installer, found nested inside an already-documented
sibling task's body). **`vp1psx-scene-script-opcodes` is now fully closed
and its TODO row deleted** -- `scene-script-vm.md` §§1-40 is the complete
paper trail, no further per-round updates expected. Sourced
`value-consumer-trace-must-continue-past-first-branch.md` (new) and a
transcription-error variant added to
`lui-addiu-negative-low-half-borrows-from-high-half.md`.

**Round 122 (2026-09-26): `data/valkyrieprofile/` holds a SECOND,
previously-unopened official artbook, and it closed the last tied
character-portrait identification in the 42-image sprite-head-crop bank.**
Prompted by an audit of every `docs/valkyrieprofile/TODO.md` row citing a
manual check for the new (that session's own) `image-only-pdf-grep-
negative-is-vacuous.md` pattern. Widening that audit's search radius to "is
there anything else scanned in this data directory" (rather than just
re-checking the one manual PDF already known) found
`Valkyrie_Profile_Material_Collection_World_Guidance.pdf` -- a 151-page,
268 MB official JP artbook ("Valkyrie Profile Material Collection: World
Guidance"), also image-only-scanned, never referenced anywhere in this
project's ~120 prior rounds despite several of them (§§12.5c-12.5k)
exhaustively searching for exactly the kind of external character-portrait
source it turns out to contain. Its file size exceeds the `Read` tool's
100 MB direct-PDF-extraction ceiling outright (a hard error, not degraded
output); `pdftoppm -f <page> -l <page> -r <dpi> -png` rasterizing pages to
PNG was the workaround -- a cheap `-r 40` whole-book skim (151 pages in
~12s) to locate the relevant section, then a `-r 300` targeted re-render of
the 2 pages that mattered. Its "God & Goddess" deity-portrait section
(explicitly captioned "in-game depiction" vs. "real-world mythology" side
by side -- developer-sanctioned canonical art, not fan reinterpretation)
named `4818` as Eir and `4823` as Hermod via exact, feature-for-feature
painted-portrait matches (identical hood/gem/hair for Eir; identical
goggle/hair/shoulder-roundel for Hermod) against the already-extracted PSX
sprite crops -- settling both of §12.5j/§12.5k's own stated "no third
source exists... zero illustration/dialogue-portrait/battle-sprite entries
anywhere in this corpus" ties at once, since neither prior search had
considered a source outside the game disc corpus itself. Closes the whole
42-image sprite-head-crop bank (0 slots remain unidentified). Sourced
`data-dir-may-hold-a-second-unopened-reference-pdf.md` (new). Full writeup:
`docs/valkyrieprofile/psx/data-structure.md` §12.5l;
`tools/valkyrieprofile/verify-sprite-head-crop-eir-hermod-artbook.ts`
(11/11 checks, both discs).

**Round 123 (2026-09-26): re-mining the SAME World Guidance artbook for a
different open item's category (background/location art, not character
portraits) found a section nobody had read yet, and narrowed but did not
close the remaining `vp1psx-worldmap-menu-portrait-names` background-gallery
residual.** A full 151-page skim (not just the deity-portrait section
§12.5l already used) found one page dedicated to real in-game background
CG ("CG美術館"/CG Art Museum, 5 named scenes) distinct from both the
character-bio section and a "Story" section illustrating real-world Norse
mythology with actual stock photography/paintings (captioned 現実 vs. ゲーム中
side by side -- confirmed NOT game assets despite superficial page-layout
similarity to the CG gallery, see new
`artbook-mixes-real-world-photos-with-in-game-cg.md`). Matched slot `4853`
to 軍事訓練所 (Military Training Facility, a vaulted ribbed-arch corridor --
structural/architectural match, not pixel-exact) and independently
corroborated the already-confirmed `4854`/`4855` church match via the same
page's 教会 scene. The retail manual was also re-skimmed in full (19 pages)
and confirmed to hold zero standalone background art. The other 6 unmatched
slots (`4849, 4850, 4851, 4852, 4858, 4859`) are now a hardened,
artbook-and-manual-checked negative -- not escalated to `re-oracle`, since
the blocker is a checked absence of any further identifying source in this
project's `data/` tree, not a bounded decode question. A verify script
(`verify-bg-gallery-artbook-round121.ts`) re-confirmed the bucket and
per-slot facts from raw disc bytes on both discs and caught a real
overclaim in the round's own first draft: the doc text called the 7
unresolved images' two-panel structure a "near-duplicate" upper/lower half,
but 2/7 slots' actual pixel-difference fraction (0.63-0.68) refuted that
framing outright -- the correct read (matching §12.5b's original wording)
is "related but not identical, both halves independently non-degenerate,"
which is what got committed. Sourced
`artbook-mixes-real-world-photos-with-in-game-cg.md` (new) and sharpened
`data-dir-may-hold-a-second-unopened-reference-pdf.md`. Full writeup:
`docs/valkyrieprofile/psx/data-structure.md` §12.5m;
`tools/valkyrieprofile/verify-bg-gallery-artbook-round121.ts` (all checks
passing, both discs).

**Round 124 (2026-09-26): the long-standing "ending-selection routine" lead
(open since round ~18, tracked across §§18.30/20.12/20.21/20.22/20.32) is
now closed.** An exhaustive re-sweep of every "still open"-family marker
across all 7 `docs/valkyrieprofile/psx/*.md` files (216+ raw hits) found
the sweep's earlier passes had already fixed two stale doc-internal
cross-references (`scene-script-vm.md`, `battle-logic.md` -- both closed by
a *later* section of the same file that was never linked back, another
`doc-self-cross-reference-before-fresh-disassembly.md` instance) and left
one substantive item: GODCAMP's ending-dispatch arming latch
(`work[0x2fad]`). Doc prose had described the latch's poller
(`FUN_8003FE74`) as "gated on" a byte "that a sibling function,
`FUN_8003FE4C`, sets" -- phrasing that reads as a call relationship but
isn't one; disassembling both confirmed they never call each other, and
`FUN_8003FE4C` (the setter) has **six** independent call sites, not the one
previously traced: five are the tail of GODCAMP's five per-state
step-sequencers (dispatched by an outer switch whose own body address the
doc had mislabeled as a function entry), and the sixth is the dialogue
text-control-code `0x4010`, now censused to exactly 8 real strings
(byte-identical both discs). New account-wide lesson sourced from here:
`gating-prose-may-hide-independent-shared-byte-access.md`. Full writeup:
`docs/valkyrieprofile/psx/data-structure.md` §20.38;
`tools/valkyrieprofile/verify-godcamp-ending-latch-arming.ts` (65/65 checks,
both discs).

**Round 167 (2026-09-26): the doc-self-cross-reference technique pivoted
from reactive (grep a flagged item's cited offset) to proactive (sweep two
sibling docs for drift with no flagged item at all), and it paid off
immediately.** After 3 straight rounds re-running the reactive form against
`data-structure.md`'s field table, this pass generalized it: extract every
`identifier+0xHEX`/`identifier[0xHEX]` token from `battle-logic.md` (the
narrative log) and `battle-engine-spec.md` (the byte-level reference spec)
-- both describe the same battle-actor struct -- keep tokens both docs
cite, and diff the surrounding prose side by side. Found 4 real stale
claims, 0 of which either doc's own text looked self-contradictory about
alone: three same-file (an earlier section's "writer not traced"/"not named
anywhere"/"not pinned down" claim silently superseded by a same-day-or-
next-day later section in the same file -- §60.6 vs §81.3's
`ENEMY_FORMATION_SETS` length; §66.2 vs §59.3's `actor+0xb8`/`+0x7a` naming;
§13.6 vs §26's `battleCtx+0x10d8` consumer) and one genuinely cross-file
and higher-stakes: `battle-engine-spec.md` §4.1's own prose still described
`record+0x6C-0x6E` as "limited-use charges... decrements it... if the
charge is exhausted," a reading `battle-logic.md` §62.8 and
`data-structure.md`'s own correction had already refuted by name -- and
`src/engine/ai.ts`'s shipped `commitScriptedAction` already implemented
the corrected "Great Magic element id, no charge" reading, meaning the
spec prose had drifted behind the very code it specifies. All 4 fixed with
`> Correction` blocks. The same sweep applied to `scene-script-vm.md` vs
`dungeon-field-mechanics.md` found a superficially stale `obj+0xe4`/`obj+
0xe8` summary row, but that file's own most recent section (a dense,
same-day 40-round "Round N: ... CLOSED" campaign on the identical struct)
had already run the same kind of self-audit and declared the item's whole
open-question list empty -- a real false-positive trap, not a miss.
Generalized as the account-wide lesson's seventeenth instance:
`doc-self-cross-reference-before-fresh-disassembly.md`. No `TODO.md` row
changes -- all four were stale prose inside already-resolved sections, not
open items. Full writeup: `docs/valkyrieprofile/psx/battle-logic.md` §60.6/
§66.2 (Correction)/§13.6 (Correction); `battle-engine-spec.md` §4.1
(Correction). Verified: tsc/eslint/vitest all at baseline (docs-only
change).

**Round 172 (2026-09-26): `vp1psx-worldmap-menu-portrait-names` -- the
background-gallery naming residual open ~10 rounds after exhausting every
room/artbook/manual visual-matching source -- is fully closed, via a new
field-joining technique plus a `re-oracle` escalation.** Two sections landed
the *previous* day for an unrelated reason (naming Odin's Sacred-Phase voice
lines: §18.30's GODCAMP text-control-code disassembly and §20.5.1's 23-entry
scenario table) had never been read against this older open row -- a fresh
instance of `doc-self-cross-reference-before-fresh-disassembly.md`, but
running in the *other* direction from its usual framing (a newly-solved
section never checked against an older open TODO row, not an old citation
gone stale). Joining the scenario table's own `+0x0E` outcome-CG-id column
against the *same record's* `+0x04` location-name string (a technique not
previously named in this corpus: an already-decoded sibling FIELD in the
same record explaining what a separate enum field means, distinct from "two
independently-built tables agreeing on a number") found the CG bank buckets
23 missions by **terrain category**, not per-mission art: 4849 cave, 4850
open/plains, 4851 mountain-forest, 4852 water, 4853 fort -- independently
corroborated by an older, code-blind visual crop description reaching the
same 5-way split from pixel content alone (`tools/valkyrieprofile/
verify-scenario-cg-terrain-join.ts`, 25 checks, both discs). A `re-oracle`
escalation then closed the remaining id, 4859: it fully disassembled
GODCAMP's outer 5-way "finalization state" dispatch (`work[0x2fa4]`, jump
table `0x800455e8`, only partially connected before -- 4/5 case-0 BGM/picture
pairs were already known individually but never tied to the dispatch's own
states) and found state 3 (chapter 8) pairs 4859 with BGM 2287 "A clash of
personalities" and caption string 195, Thor's pre-Ragnarok war-council
mobilization speech to the assembled Aesir. A same-pass addendum then
*quantified* which picture 4859 actually is, rather than leaving it
"non-specific": splitting all 13 gallery images into their already-confirmed
two-panel halves (§12.5m) and Pearson-correlating luminance (tint-invariant)
across every cross-image panel pair, with a row-demeaned null control that
kills the shared sky/ground gradient every landscape has, found 4859's lower
panel matches 4850's upper panel at r=0.947 raw / 0.479 row-demeaned
(z=3.9, 2nd of 936 pairs) -- 4859 is 4850's own daytime open-field CG
(4850 is precisely the terrain bucket the scenario table files "Jotunheim
Ice Field" under) re-rendered at dusk with its panels swapped, matching
Thor's own "Leave the Ice Field enemies to us" opening line. The same census
found 4858 (already refined this round from "generic pool member" to
exactly 2 named vignette backdrops) shares its upper-panel source art with
4857's lower panel at r=0.503 row-demeaned (highest in the whole matrix,
z=4.1) -- a hazier re-panelling of the already-matched "plain of Valhalla"
scene. Independently re-run against both discs before committing each time
(114/114 dispatch checks, then the panel-correlation numbers reproduced
byte-identical). `TODO.md` row deleted outright (not just marked resolved).
Also closed this round: a stale `TODO.md` row
(`vp1psx-tile-sprite-unk10`) that a 2026-09-02 in-place `> Correction` block
had already resolved without the row ever being touched -- a clean instance
of the existing doc-self-cross-reference lesson's "TODO row stale relative
to a doc correction" shape, deleted outright. Full writeup:
`docs/valkyrieprofile/psx/data-structure.md` §§12.5n/12.5o (incl. the
panel-correlation addendum), §12.6, §18.30;
`tools/valkyrieprofile/verify-scenario-cg-terrain-join.ts`,
`tools/valkyrieprofile/verify-godcamp-finalization-backdrops.ts`,
`tools/valkyrieprofile/probe-bg-gallery-panel-correlation.ts`.

**Round 185 (2026-09-26): the scene-script VM's two highest-frequency
remaining `hypothesis` opcodes both closed, one via a plain re-check that
refuted a prior round's own claim, the other via a cross-doc offset join.**
Opcode 142 `SFX_CTL` (1,341 uses): round 27 had flagged resident
`0x8001a7e0` as structurally puzzling ("no prologue, reads an unset `$s7`");
a fresh, independent disassembly found this simply wrong -- a complete,
correctly-bounded 9-instruction leaf function with zero `$s7` references,
arming a duration-derived linear fade-rate timer on the already-confirmed
sound-driver-context global (`period = 0x7800/durationFrames`, corpus-wide
call census: exactly 4 clean frame-count values, 30/60/120/240 @ 60Hz,
refuting a note/pitch reading). Opcode 178 `WINREC_MODE` (1,149 uses,
mechanism already confirmed, purpose open): joined its mode-1 clearing
target (`ctx+0x39c..0x39f`) against `battle-logic.md`'s own already-
disassembled `buildPartyRoster`, which reads the identical 4 bytes (via
the independently-established `ctx`/`P` aliasing) as the party-seat(0-3)
-> characterId array -- and the SAME register that selects the opcode's
own companion-array slot is also the mode-1 comparison value, pinning
`operand1` as a character id. WINREC_MODE is VP1's party-membership-change
primitive (mode 0 arms/mode 1 disarms-and-evicts/mode 2 queries). Both
independently byte-verified on both discs
(`tools/valkyrieprofile/verify-sfxctl-fade-timer.ts`,
`verify-winrec-partyseat-tie.ts`); table now 226 confirmed / 11 hypothesis.
Sourced a 13th instance of `verify-escalation-artifacts-not-just-claims.md`
(a prior round's own disassembly claim, not just an escalation's, can be a
plain misread) and a 3rd instance of `confirmed-index-shared-by-second-
parallel-table.md` (the "second table" a confirmed index also touches can
already be fully decoded in an unrelated doc, joined only by a shared
small numeric offset once an aliasing fact applies).

**Round 186 (2026-09-26): 4 more scene-script VM hypothesis opcodes closed
by "find the consumer, not the producer" (round 185's technique reapplied
3x) -- a scripted camera-leash/shake subsystem found end-to-end.** Opcodes
131/132 `EFFECT_BOUNDS_A`/`B` (248/0 corpus uses; mechanism known since
round 182, purpose unnamed): found the previously-undocumented per-frame
consumer `0x8004740c` (field overlay) of the shared callee's scratch
output -- it polls the camera position against a stashed snapshot to
clear the WAIT flag opcode 153 tests, then ramps a half-extent and CLAMPS
the room camera's own live Y position into a scripted window, intersected
with opcode 208 `SET_SCROLL_REGION`'s rectangle; settles the mechanism as
a camera constraint/leash, not a particle/visibility-cone effect (132
promoted alongside 131 on 0 corpus uses = corroborated-unused content, the
round-178-opcode-7 pattern). Opcode 150 `TOGGLE_TASK_5AFD0` (33 uses):
disassembled the task (`0x8005afd0`) round 27 had explicitly flagged
out-of-scope, finding a sine oscillator sharing 131/132's own trig helper
(`0x80079324`); the SAME `0x8004740c` consumer has a third tail adding the
oscillator's output onto the camera's live Y -- VP1's camera-shake
trigger. Opcode 225 `SYNC_4_CHANNELS` (19 uses): decoded the shared
resident `0x8001aae8` (also called by opcode 227) as a 3-word leaf
clearing a per-party-seat voice/dialogue cache-invalidation byte inside
the sound-driver-context global. 228/226/227/234 substantially advanced
via the same finds. Table now 230 confirmed / 7 hypothesis (was 226/11
after round 185); remaining: 141, 167 (0 corpus uses, no corroborating
sibling unlike 132 -- deliberately left hypothesis rather than force-
closed), 205, 226, 227, 228, 234. All findings byte-exact both discs,
`tools/valkyrieprofile/verify-camera-leash-and-shake.ts` (102/102 checks).
Technique note: the winning searches were register-provenance-gated
(track which register's last load came from the target global, only flag
ops on THAT register) rather than literal-address or bare-immediate
scans -- cut ~150 coincidental `andi *,*,0x200` hits down to the 1-2 real
bit-tests. A real endianness bug was caught mid-round: a from-scratch
probe assembled 32-bit MIPS words big-endian instead of little-endian,
producing false 0-hit negatives until cross-checked against the project's
own already-correct disassembler helper -- fixed before any wrong
conclusion shipped.

**Round 187 (2026-09-26): 3 more closed -- both remain-141/205 plus a
bonus, by linking two ALREADY-solved subsystems together rather than
tracing anything new.** Opcode 141 `BGM_RETRIGGER_OR_TASK` (34 uses):
both resident calls turned out to already have named siblings in
`data-structure.md`'s own BGM-driver section -- `0x8001a5f8` is the
confirmed song-select function's (`0x8001a67c`) own "different song"
branch (voice-kill + reverb-disable + full reinit) minus the identity
check, closing `*(0x8007f104)`'s long-open role as a side effect (the
staged BGM sequence-data buffer, since it's stored straight into the
confirmed `ctx+0x30` seq-pointer field); `0x80059f88` re-kicks opcode
217 AMBIENT's own resident (`0x8001a91c`) for the outgoing track's
ambient/ducking entry. Opcode 205 `LAYOUT_TRIPLE_205` (48 uses, "purpose
not identified" since round 27): its own internal helper (`0x8007cdf4`)
turned out to `ctc2` 5 words into GTE control registers 16-20 -- the
PSX GTE's own hardware-documented **Light Color Matrix** -- so the
handler assembles one RGB row of a scripted lighting tint per call (see
`game-re-tooling/psx.md`'s new GTE-control-register section, sourced
here). Bonus: opcode 228's own further call target `0x8006efb0` (round
186 left it partial) is a 3-category per-companion item-slot table with
an auto-fallback active-slot pointer. Table now 232 confirmed / 4
hypothesis (was 230/7); remaining: 226, 227 (own record-field roles),
234 (companion-record identity), 167 (unchanged). A quick shape-based
scan for 226/227/234's remaining fields (`record+0xAC`/`record+0x2a`, no
base-register-provenance filter) came back too noisy (123/28 hits,
unrelated structs at the same offset) -- recorded as not-yet-advanced,
not refuted, per `negative-from-addressing-root-not-shapes.md`. Verified
byte-exact both discs, `verify-bgm-retrigger-and-gte-light-row.ts` +
`verify-equip-slot-category-array.ts`.
**Round 188 (2026-09-26): 226/227/234 CLOSED via a base-register-provenance
census, completing the round-183-188 `SCENE_OPCODES` arc (236/238
confirmed).** Fixed round 187's noisy scan with a proper root-based census:
find every literal `lui/lw` load of the companion-array base `*(0x8007f1e4)`
overlay-wide, forward-taint derived registers through `addu`/`addiu` chains
(stop at `jr $ra`, invalidate caller-saved regs across `jal`). Result,
byte-identical both discs: exactly 12 roots exist in the whole ~370KB
overlay; only opcodes 227/234 ever touch `record+0xAC`/`+0xB0`/`+0xD6` -- a
clean, complete negative for "no other consumer exists." Opcode 227's own
"+0x2a"/"+4"/"+0" fields (relative to a `base+0xAC` pointer) resolve to
those SAME absolute offsets, and 227 performs 234's own commit-and-clear
action unconditionally for all 25 records -- closing "what do these fields
mean" via arithmetic alone, no external consumer needed. A 12th root
outside the opcode dispatch table entirely (`0x8005ea08`, already named
but only shallowly described as `TASK` id 49 `NewobjCompanionPoolScanner`
in `data-structure.md` § 9.6.51) was fully disassembled as a side effect of
scanning ALL roots rather than just the ones near known handlers, giving
the companion array's `+0xD9` field its first real gameplay identity: a
per-character party-availability flag, auto-armed for 21-24 of the 25
playable-roster slots (4 always-excluded indices, 2 conditionally-gated
ones). Only opcode 167 `CAMERA_SCAN` remains hypothesis (0 corpus
occurrences, no corroborating sibling, deliberately left per round 186's
judgment). `record+0xB0`'s own writer stays an honest, un-blocking residual
(0 writes found via this addressing root anywhere in the overlay).
Verified byte-exact both discs, `verify-companion-record-commit-and-roster-
arm.ts` (32/32) + `probe-companion-record-provenance-census.ts` (the
reusable census itself, reproducible from raw disc bytes). This is the
6th+ confirmed Valkyrie Profile instance of the base-register-provenance-
census fix already documented in `struct-field-scan-blind-to-biased-base-
pointer.md`/`indexed-operand-needs-base-provenance.md`/`negative-from-
addressing-root-not-shapes.md` -- no new pitfall filed, just another clean
worked application. **`record+0xB0`'s residual CLOSED (round 189,
2026-09-26, `game-re`):** confirmed dead, not merely unwritten -- `NEWOBJ`'s
own allocation site zero-fills the whole 236-byte record via the confirmed
resident `memset` (fill byte 0, length exactly the record stride)
immediately after allocating it, and the same provenance census widened
from this one overlay to a 73-file corpus-wide sweep (every menu-family
overlay including the equip/status screens the "different subsystem"
half of the hypothesis named) finds the companion-array base referenced in
exactly one more file total (TOC 2293, "field overlay's paired module,"
disassembled and confirmed non-writing). Sourced two lesson-file sharpenings
from this round: `negative-from-addressing-root-not-shapes.md` (a root
census must be corpus-wide, not single-file) and `static-image-zero-dump-
refutes-authored-template-hypothesis.md` (disassemble the allocator's own
`memset` call as a stronger zero-default proof than a snapshot dump), plus
a new file, `local-decode-cache-may-be-stale-reverify-fresh.md` (this
project's own disc1 cache for TOC 2293 was a stale/wrong-length 22,528 B
artifact; the real content, re-derived fresh, is 2,944 B on both discs).
Side finding, not yet closed: TOC 2293 also holds the real BUILD routine
for the already-known 612-entry item table `*(0x8007f204)` (previously
only a resident pointer) -- `item-skill-system.md` § 10.

**Round 190 (2026-09-26): the round-189 side finding CLOSED --
`item-skill-system.md`'s 612-entry item table `*(0x8007f204)` now has its
own build routine traced, correcting a real biased-base-pointer misread
along the way.** `item-skill-system.md`/`TODO.md`. **Round 191 (2026-09-26):
generalized the round-189/190 shape ("documented consumer, undocumented
producer") into a systematic sweep of the whole `docs/valkyrieprofile/psx/
*.md` corpus for "no traced writer"/"writer unknown"-style rows** --
`StatusResistance.magicReflect`/`freezeImmune` (`battle-logic.md` § 48.4-
48.7's field table) matched the pattern. `magicReflect`'s "no writer
traced" claim turned out to be stale, self-contradicted by the SAME
document's own § 51.2 (`fcn.8005b878`, item 35 "Magic Charm") -- a fresh
instance of `doc-self-cross-reference-before-fresh-disassembly.md`.
`freezeImmune`'s writer (`fcn.8005b90c`, item 343 "Eternal Lamp", checked
against the party's shared 612-slot inventory array rather than any unit's
own equipment) was genuinely new, as was a shared wrapper (`fcn.8005b9a8`)
tying all three `+0x6a0`/`+0x6a3` sub-writers together and its exactly 2
corpus-wide callers. Verified 67/67 both discs,
`tools/valkyrieprofile/verify-status-resist-writers.ts`. Mid-session
self-correction: `+0x6a3`'s own writer (`fcn.8005b7f4`) was initially
written up as newly discovered, until running the FULL test suite (not a
targeted doc grep) surfaced pre-existing passing tests in
`support-buff-consumers.test.ts` proving `battle-logic.md § 64.9.3`
already fully documented it byte-for-byte -- see
`doc-self-cross-reference-before-fresh-disassembly.md`'s newest instance
for the sharpened fix (run the test suite before, not just after, writing
up a fresh finding as novel). The "documented consumer, undocumented
producer" doc-corpus sweep is now a proven repeatable technique on this
project across two rounds (189-190: the item table + the BGM sequence
buffer; 191: `freezeImmune` + the wrapper) -- worth re-running whenever
`TODO.md`'s tracked rows run dry, per the same file's eleventh instance.
`battle-logic.md` § 103; TODO.md unchanged (no row existed for this item).

**Round 198 (2026-09-27): a rigor spot-audit of the campaign's own earliest
resolution (`vp1psx-battle-damage-formula`, closed 2026-09-04 with no
dedicated verification script) re-disassembled the physical damage
formula (`fcn.8003ae48`) fresh from raw disc bytes and found it was wrong
in 5 ways** a prior pass's disassembly had missed or misattributed: an
undocumented "Weak Point" DEF-halving helper; a graze mechanism that an
earlier "Correction" had misattributed to the wrong sibling function
(the magic formula's own separate roll); an undocumented command-code-
keyed damage multiplier; a wrong classifier divisor (documented `/4`,
real `/8` for two specific values plus an always-applied `/2` the doc
missed via a MIPS branch-delay-slot trap); and a floor boundary
(`raw<0` vs. documented `raw<1`). All verified byte-exact both discs, 45
checks x 2, 0 failures. This is the project's clearest demonstration yet
that "resolved, no dedicated verification script" rows from early in a
long campaign are a real liability class worth periodically re-auditing,
not just a one-off.

**Round 199 (2026-09-27): closed the `src/engine/damage.ts` implementation
gap round 198 opened** (the round explicitly deferred wiring its findings
into the maintained TypeScript engine, correctly recognizing that a
same-round rewrite-plus-verify would be rushed). `baseDamage()` gained an
`rng` parameter and now implements all 5 corrected mechanisms internally;
every downstream test the signature change touched was updated using
values computed by running the corrected implementation, not hand-derived
arithmetic. Sourced `formula-fix-nets-identical-or-scaled-result-for-
default-parameter-case.md` (new): running the corrected formula against
the existing fixtures surfaced a real, easily-misread emergent property --
the previously-undocumented command-code multiplier's DEFAULT value (x2)
exactly cancels the newly-added unconditional `/2` divisor for the
majority "classifier == 0" case, so the corrected formula's output is
either byte-identical to or exactly double the old, wrong formula's
output for every DEFAULT-parameter fixture, and only diverges for
non-default command codes / the Weak Point check / the second graze roll.
A same-round check against only default-case fixtures could easily have
been misread as "the fix changed nothing" or "the fix just doubled
everything, that can't be right" rather than correctly verified branch by
branch. `battle-logic.md` § 9.3 / `battle-engine-spec.md` § 5.1;
`TODO.md`'s `vp1psx-battle-damage-formula-engine-gap` closed, a narrower
`vp1psx-battle-damage-formula-def-penalty-writer` opened for the new
`+0x5b9` field's still-untraced writer.

**Round 200 (2026-09-27): closed the `defender+0x5b9` writer round 199 left
open, and ran a genuine second rigor spot-audit.** The writer trace
started from the already-documented SIBLING field's writer as a
hypothesis (`fcn.8005b4e4`, the party-only stat-population function that
already writes `attacker+0x5b8`/`+0x5ba` from the equipped weapon's
`itemTable32+0x08`/`+0x0a` at equip time) and disassembled the whole
function fresh: `+0x5b9` turned out to be written from the SAME
`itemTable32+0x08` byte, but sourced from the character's *armour* slot 0
("head", one of the already-documented 6-slot DEF/HIT/AVD-summing array)
rather than the weapon -- i.e. one underlying item stat is dual-purpose by
equip slot: attack-penalty range as a weapon, defence-penalty range as
armour. A naive "the byte between the two already-known fields must feed
the new one" positional guess would have been wrong twice over: the real
byte between them (`itemTable32+0x09`, `hitBonus`) actually feeds a
FOURTH, previously undocumented, non-adjacent field (`actor+0x5bc`, a
wider u16) from the SAME weapon-equip block. Verified byte-exact both
discs (0 diffs across the whole 776-byte function); a corpus-wide `0x5b9`
displacement census found exactly 3 references in the whole overlay (the
known consumer, the zero-init, and this write) and zero in the enemy-
roster-construction overlay, matching the sibling fields' already-
documented enemy-side gap. Wired into `src/battle/encounter.ts` the same
way the weapon-derived fields already are (real effect on the shipped
Stage 3 roster: `0` for all 4 default party members, since their starting
head-slot items happen to carry `penaltyRange==0` -- correct, not a bug,
per a direct items.json check). Closes
`vp1psx-battle-damage-formula-def-penalty-writer`.

**The genuine second rigor spot-audit** (round 199 had only shallow-
checked two already-heavily-audited candidates and explicitly deferred a
real attempt) picked `vp1psx-battle-cp-two-tables` (resolved 2026-09-03,
no dedicated verify script) and re-disassembled every cited instruction
fresh from both discs via a from-scratch SLZ + group-directory extraction
(no cached `build/cache` artifact reused). Unlike round 198's damage-
formula audit, this one is a clean, useful NEGATIVE: every structural
claim (the flat Learn/Level commit path's stride-11 arithmetic; the
per-slot install/adjust routine's full raise/lower-mirror body, including
a doc pseudocode simplification -- "`(level-1)*2`" -- that the raw bytes
implement as "index by `level*2`, then read 2 bytes back", arithmetically
identical but worth confirming rather than assuming; both cost tables;
the direction table; the confirmed caller) held up byte-exact on both
discs with zero substantive changes needed. The one thing it DID catch:
a small citation transcription error -- the caller's UI-cursor selector
address was documented as `0x8005B6E8`, but re-deriving it from the raw
`lui`/`addiu` pair gives `0x8004B6E8` (one hex digit off in the upper
half, plausibly because the surrounding code is saturated with `0x8005`
lui immediates for this overlay's own base). Confirms the two-rounds-in
pattern this project is now building: periodic rigor spot-audits of
early, pre-dedicated-verify-script closures are worth running
repeatedly even after a first pass finds nothing big -- a clean result
with one small fix is itself useful signal, not a wasted round. Both
scripts (`tools/valkyrieprofile/verify-def-penalty-range-writer.ts`,
`tools/valkyrieprofile/verify-cp-tables-round200-audit.ts`) are the
project's reference examples for "extract fresh from raw disc bytes, cite
nothing from a cached artifact or prior doc prose without a literal
re-derivation."

**Round 201 (2026-09-27): closed the `actor+0x5bc` consumer round 200 left
open, incidentally surfacing a small previously-undocumented reusable
mechanism, and ran a THIRD rigor spot-audit that came back clean.** A
full-slot-1490 literal-displacement census for `0x5bc` (word-boundary
matched, so it doesn't false-positive on a wider literal like `0x5bc8`)
found exactly one real consumer: `fcn.8003a5f0`, a small helper reading
`halfword[unit+0x5bc]` (the weapon's raw `hitBonus` byte, round 200) as a
d100 percent-chance threshold against the already-confirmed
`fcn.800104d4` bounded-random helper, with two shortcuts returning
unconditional success (the unit IS the battle-context's currently-acting
actor; or the other unit already carries the confirmed "immediate miss"
hit-outcome code). This helper has exactly 2 callers, both inside a
small reusable per-candidate eligibility idiom (calling it right after
the already-documented main hit-gate `fcn.8003a39c`, same argument
roles, same `s8==1` sentinel independently re-set in each caller): the
already-documented `meleeCollisionStep` (`0x80039c14`,
`battle-engine-spec.md` §37.4/§11.6.3 -- confirms its internal
eligibility chain was never traced before this pass, only its 3-way
return code) and a second, previously-unnamed AOE routine whose terminal
call chains into the already-known physical-damage-formula entry
(`fcn.8003ae40`) with a fractional multiplier -- a splash/secondary-target
reduced-damage mechanic, consistent with "hitBonus" gating whether a
nearby target also takes a (weaker) hit. Not wired into the engine
(`meleeCollisionStep` is a deliberate caller-supplied policy stub since
this engine models no positions; the second routine is untraced further
and unreferenced in `src/engine/`) -- a documentation-only closure.
Verified byte-exact both discs, 39 checks × 2 discs, 0 failures
(`tools/valkyrieprofile/verify-actor-05bc-consumer-search.ts`). Closes
`vp1psx-battle-actor-0x5bc-field`.

**The third rigor spot-audit** picked `vp1psx-skill-spell-cost-and-
selection`'s §30.2 CP-category-array writer (resolved 2026-09-04/05, no
dedicated verify script) and re-derived every claim fresh: the
`regionType`-18 menu-code region turns out to be SLZ-compressed *at rest*
inside the group directory (the region's own `regionSize` field is the
on-disc compressed length, not the already-cited 24,368 B decompressed
module size the doc's own table header already correctly labelled --
worth flagging for whoever re-derives this, since a naive
`readVbin`+`parseGroupDirectory` alone stops at the compressed bytes and
needs one more `decodeSlzBlock` hop). Unlike round 200's audit, this one
found **zero discrepancies**: every global the doc's pseudocode cites,
the write instruction, the ×236 record-stride ladder, the array-B gate,
and the duplicate-assignment-check loop all re-disassembled identically
on both discs. A clean re-confirmation is itself a useful, distinct
outcome class from round 198's "real gaps found" and round 200's "one
small citation fix" -- three rounds in, the spot-audit vein has now
produced all three possible outcomes (gaps, a small fix, a clean pass),
which is itself evidence the technique isn't just fishing for bugs that
happen to always be there. `tools/valkyrieprofile/verify-cp-category-
array-writer-round201-audit.ts` (19 checks × 2 discs, 0 failures) is the
reference example for resolving a MIPS `lui`+load pair into an absolute
address programmatically rather than string-matching a disassembler's
raw per-instruction operand text (see
`disasm-text-never-folds-lui-load-pair-into-resolved-address.md`).

**Round 202 (2026-09-27): named+closed round 201's own "second, previously-
unnamed AOE routine," and a FOURTH rigor spot-audit came back clean
again.** `fcn.800720a8` (round 201's terminal splash-damage call) is now
fully traced end to end: a pooled-object spawner (`0x80072ae4`) installs
a per-tick native handler (`0x800726f0`, gated on a literal
descriptor-kind tag + a new `actor+0x61c` flag) that calls a real-geometry
sweep function (`0x80072274`, reusing the already-confirmed
world-to-screen GTE projector and screen-space AABB hit-test) and, on a
hit, `fcn.800720a8` itself — which forces `weaponType=0` into the general
physical-damage formula, applies an exact hardcoded **30%** fractional
multiplier via the identical magic-multiply-by-`0x51EB851F`/`÷100` idiom
already confirmed for the EXP difficulty scaler, is a second confirmed
consumer of the `battleCtx+0x644` nullify flag, and feeds the confirmed
PWS-counter and combo-gauge accumulator (proving it's live, exercised
logic, not dead code). Answers both open questions from round 201: the
trigger is the native per-frame `tickObjects()` dispatch (no static
skill/opcode binding at all), and the multiplier is a fixed constant, not
table-driven. Deliberately **not** wired into `src/engine/aoe.ts` — the
whole trigger/dispatch chain lives inside the same excluded native-
interpreter subsystem `MeleeCollisionPolicy` already stubs out, so
extending the engine core or the excluded interpreter would both be out
of scope. `tools/valkyrieprofile/verify-aoe-splash-damage-fcn800720a8.ts`
(33+ checks × 2 discs, 0 failures) — its first draft used positional
array-indexing into a decoded word window and miscounted delay slots,
producing ~13 spurious FAILs against otherwise-correct bytes; fixed by
switching every check to an exact-address `wordAt()` lookup (see
`mips-delay-slot-instruction-always-executes.md`'s new fifth
manifestation).

**The fourth rigor spot-audit** picked `vp1psx-battle-enemy-stat-record-
fields` (resolved 2026-09-17, verification was only a synthetic-fixture
unit test — see `test-fixture-encodes-same-wrong-model-as-implementation.md`).
Re-derived the copy-site and difficulty-multiplier disassembly fresh on
both discs, rebuilt the Disc 2 record collection from scratch (996/996,
byte-identical to Disc 1 — the doc's own "byte-identical" aside had never
actually been independently re-verified before), recounted every reserved-
zero run and boolean-flag domain, and cross-checked STR/RDM/RST/INT/EXP
against a **genuinely independently re-fetched** external oracle rather
than the docs' own transcribed numbers — GameFAQs and the VP Fandom wiki
were both Cloudflare-blocked outright, worked around by `curl`-ing
rpgdl.com's raw `.txt` FAQ mirror with a browser User-Agent (its own
`mod_security` blocks a bare UA-less request) plus several deliberately
non-leading `WebSearch` queries (omitting the target numbers, so the
search summarizer can't echo them back as false corroboration). Result:
clean re-confirmation, 0 discrepancies —
`tools/valkyrieprofile/verify-enemy-stat-record-rigor-audit.ts` (both
discs, 0 failures). Four rounds into this vein, the split is now 1 real-
gaps round (198), 1 small-fix round (200), and 2 clean-pass rounds
(201, 202) — still consistent with "worth running repeatedly," not
"fishing for bugs that always turn up." This round's own verify-script
authoring also hit a real, separate bug worth flagging for future
sessions: a `check(label, word === (a<<26)|(b<<21)|c, ...)`-shaped
expected-value comparison silently parsed as `(word === (a<<26)) |
(b<<21) | c` (`===` binds tighter than `|`), producing a truthy NUMBER
that JS coerces to a false-positive PASS regardless of whether the real
comparison held — caught only because `npx tsc --noEmit` flagged the
resulting type mismatch (TS2362/TS2345); see
`check-expression-bitwise-or-precedence-masks-comparison.md`.

**Round 203 (2026-09-27): a FIFTH rigor spot-audit widened past `TODO.md`
entirely, plus a first characterization of round 202's own two leftover
residuals.** Screening every `resolved` `TODO.md` row found nothing left
un-audited (rounds 198-202 already covered the four real candidates) —
so the pool was widened to any confirmed spec claim with no `TODO.md` row
at all, landing on the EXP/leveling system (`fcn.80099800`, TOC slot 1989,
closed 2026-08-22 via `re-codebreaker`, never independently re-checked
since; its only test, `exp.test.ts`, runs against a hand-typed fixture
copied from the same doc prose). Re-derived `EXP_TO_NEXT`/`GROWTH`/
`CLASS_OF_CHARACTER` from fresh Disc 1 + Disc 2 bytes, and — the one table
the project's own code flags as unverifiable by structure,
`classGrowthDeltas` ("hand-transcribed from the disassembly rather than
byte-parsed") — independently re-derived it by disassembling all 5
class-handler bodies fresh; all match. Also closed a real citation gap:
`build-assets.ts`'s `readDisc1TocSlot()` cited § 23.1 for TOC 1989/1490's
Disc-2 byte-identity, but § 23.1 is actually about the slot's load base, a
different claim entirely (`doc-self-cross-reference-before-fresh-
disassembly.md`'s 26th instance) — now backed by a real fresh whole-
overlay byte-diff on both discs. A bonus find: the level-up routine's own
`+0xB0` (max HP) write is a dead store, unconditionally overwritten by
`fcn.8005e5d8`'s own absolute recompute one call later (confirmed via a
fresh disassembly of that clamp block, whose `+0xB0` store sits in a
branch delay slot that always executes) — `src/engine/exp.ts`'s omission
of a separately-persisted `maxHp` field is a confirmed-correct
simplification, not a gap. Clean re-confirmation, 0 discrepancies,
`tools/valkyrieprofile/verify-exp-leveling-rigor-audit.ts` (both discs).
Five rounds in, the split stays 1 real-gaps round (198), 1 small-fix round
(200), 3 clean-pass rounds (201/202/203).

**Secondary task**: § 104.4's two residuals (`fcn.8003ca7c`, `actor+0x61c`)
got their first real characterization attempt. `fcn.8003ca7c` turned out
to have **3 callers, not the 1 round 202's framing implied** — a whole-
overlay `jal`-target census (cheap, ordinary due diligence, not a
post-hoc fix) found it's a shared, general-purpose post-damage hit-
reaction/stagger accumulator (increments a per-actor hit counter, records
and caps a running delta against the actor's own max-HP mirror field,
returns a constant animation-trigger id) any damage site can call, not
something AOE-specific. `actor+0x61c` was traced to exactly 2 static
writers in slot 1490, both inside one function that shares its `kind==4`
pooled-object discriminator and its GTE-projector call with the AOE
per-tick handler it gates — found via a plain corpus-wide "any `sb`/`sh`/
`sw` at displacement `0x61c`" scan, then reading the surrounding context:
the clear fires only for command codes 8/13 (already-documented
"projectile"/"heal-on-arrival" action types with their own known sibling
per-tick site), and the set follows an elemental-match/mismatch variant
selector. Reading: a per-caster "projectile/AOE effect in flight" latch.
Both substantially narrowed, neither fully closed (the state machine
`actor+0x61a` dispatches on, and `battleCtx+0x1129`'s own consumer,
stayed open) — no `src/engine/` change, same interpreter-scoping
exclusion as § 104. `tools/valkyrieprofile/verify-fcn8003ca7c-and-
actor61c.ts` (both discs, 0 failures).

**Round 204 (2026-09-27): resolved the round-202/203 AOE-chain caller
discrepancy, ran a SIXTH rigor spot-audit (clean), and got the first real
characterization of `battleCtx+0x1129`'s consumer.** The AOE/splash-damage
applicator chain `fcn.800720a8` (named in round 202) had one caller cited
inconsistently between rounds 202 and 203's own prose — re-disassembled
fresh from both discs and settled definitively. The sixth rigor spot-audit
picked `battle-logic.md` § 31.1's PWS chain-bonus mechanism (closed
2026-09-03 via prose-cited disassembly with no committed verify script —
this campaign's own selection bar). Re-derived, byte-exact on both discs:
`fcn.8003adb8`'s damage modifier (chainIdx==0 short-circuit, -25% for
chainIdx<3, then a `(100+bonus)/100` scale via the standard
`0x51EB851F` magic-multiply); the three independent saturating-counter
(cap 99) increment sites for `battleCtx+0x1131`, all sharing an
**additional, earlier gate** (`byte[unit+0x129]==2` skips the whole
block) the § 31.1 prose never mentioned; and the `0x8007d2a8` 16-halfword
table's real consumer (a separate PWS combo-gauge DISPLAY-value formula,
confirmed structurally distinct from the damage formula despite sharing
the "magic-multiply /100" idiom with a *different* constant). Clean
re-confirmation plus one genuine bonus finding (the undocumented
`unit+0x129==2` pre-gate) — sixth straight rigor audit, split now 1
real-gaps round (198), 1 small-fix round (200), 4 clean-pass rounds
(201/202/203/204). **Tertiary task**: a first characterization of
`battleCtx+0x1129`, whose only known writer (`fcn.8003ca7c`) had no traced
consumer. A whole-overlay displacement census found 3 more accessors, all
inside one contiguous function body: a per-tick counter (cap 255),
incremented while `battleCtx+0x10d0` is nonzero, cleared when it's zero,
gating a `0x51EB851F`-magic-multiply ramp formula (computed from
`counter-1`) whenever `counter<7` **and** the sibling `+0x1131` PWS-bonus
byte is nonzero. Left open (round 205 closed both): the ramp formula's own
downstream consumer, and `+0x10d0`'s exact meaning.
`tools/valkyrieprofile/verify-battlectx-1129-consumer.ts` (both discs).

**Round 205 (2026-09-27): diversified the rigor-audit vein outside
`battle-logic.md`/`battle-engine-spec.md` for the first time in 7 rounds,
and closed round 204's `battleCtx+0x1129` residual.** The primary task
deliberately picked a claim from `data-structure.md` instead — screening
for verify-script citation density and earliest date-stamps across the
non-battle docs (`dungeon-field-mechanics.md`, `item-skill-system.md`,
`data-structure.md`, `save-system.md`, `scene-script-vm.md`) found § 16.1
("the illustration run is `illustrationSlot = 2186 + characterId`",
2026-08-18, `re-codebreaker`) had never had a dedicated verify script —
only a manual, quantified-but-eyeballed weapon/class visual cross-check,
and its only later exercise was two downstream consumers that assert the
constant rather than re-deriving the join. Re-derived fresh on both discs
via a new `verify-illustration-slot-join-round205-audit.ts`: TOC slot
2186's 26-region group directory (ids exactly `{1..25,100}` — reading a
region's leading `u16` *before* SLZ-decoding it gives a uniform decoy
value on every entry, a cheap, self-revealing tell that it needs decoding
first); `codeoverlay_slot2174.bin`'s two literal `0x88a` (=2186) resource-
load references, freshly disassembled to the confirmed `openRes`/
`resolve` primitives; all 25 TOC slots 2187-2211 parsing/compositing as
clean § 12.6 tile sprites; and — the load-bearing external check itself,
never previously re-derived, only hardcoded into `build-assets.ts`'s
`VP_ROSTER_CHARACTER_NAMES` array — the class-string (4100-4124) and name
(4000-4024) banks decoded fresh from TOC slot 2179's own font/text pair,
matching the doc's published tables character-for-character. Also
re-rendered all 25 illustrations from scratch (bypassing every cached
pipeline PNG) and viewed a spread with fresh eyes, independently
reproducing every distinctive weapon/class visual match already claimed
(Llewelyn's bow, Jun's katana, Lezard's spectacles, Jelanda's gown,
Valkyrie's helm, Brahms's undead pallor, Janus's neutral no-weapon bust).
Clean re-confirmation, no engine change. **Secondary task**: closed both
items round 204 left open for `battleCtx+0x1129`. `+0x10d0` turned out to
be **already named** elsewhere in the very same doc (`beginAttackSequence`'s
"current active target" field, re-derived fresh via a whole-slot
`sw`-displacement census rather than trusted from the old citation) — a
`doc-self-cross-reference-before-fresh-disassembly` instance round 204
itself left unclosed. The ramp value's consumer is a floating PWS-bonus
number popup: it decays linearly (`220-(tick-1)*20`, magic-multiplied,
~2253->1024 over 7 ticks) then flattens at `0x400`, feeding as the 4th
argument of two `0x80061458` draw calls in exactly the
`0x800371bc`+`0x80061458` shape this doc already documents as the game's
digit/number-popup mechanism — plausibly a Q10 fixed-point pop-in/settle
scale factor. New `verify-battlectx-1129-consumer-round205.ts`, 0
failures both discs. Presentation-only; no engine change.

**Round 209 (2026-09-27): 12th rigor spot-audit, second landing on
`data-structure.md` after round 205, this time on § 4 — the "SLZ"
compression container, the earliest never-re-derived claim in the whole
doc.** `verify-slz-corpus-decode-round209.ts` re-ran the production
`scanSlzBlocks` magic scanner fresh (reproducing the doc's own "13,772 /
13,139" headline block counts independently) and decoded **every** block
on both discs (26,911 total) rather than the original doc's small
hand-picked samples (75/60/15/10/8) — using local *instrumented* ports of
the LZSS decoders that deliberately read look-ahead bytes past the
header's declared `compressedSize` and report the exact consumed-byte
count and *why* the loop stopped (sentinel/buffer-exhausted/output-full),
rather than reusing the committed `decodeSlzBlock`, whose input buffer is
pre-sliced to exactly `compressedSize` and so cannot distinguish "stopped
in the right place" from "ran out of room" — see
`rle-decode-succeeds-on-garbage.md`'s new "instrumented look-ahead decode"
addendum, sourced from this round. Two results: (1) the decode-length/
consumed-byte invariants hold with **zero deviations across the full
corpus**, including — for the first time ever — subtype-2 blocks
(16,776 of them; § 4.2's original text only ever sampled subtype 1 for
the consumed-byte check). (2) A real formula bug: § 4.2's `chainStride ==
16 + compressedSize`, "confirmed exact in every case" on its original
10-sample check, actually holds for only **24% (636/2,649)** of the real
chained blocks on both discs — it passed 10/10 purely because none of
those 10 samples happened to need padding. The real, zero-exception rule:
every SLZ header on either disc (chained or not, all 26,911) starts at a
4-byte-aligned absolute offset, and `chainStride` rounds `16 +
compressedSize` **up** to the next 4-byte boundary. No production code was
affected (every real consumer already reads `chainStride` from the header
rather than recomputing it) — purely a wrong prose claim, now corrected in
place. See `formula-check-small-sample-misses-conditional-rounding-term.md`,
sourced from this round. Commit `4774e04`.

**Round 215 (2026-09-27): a second, independent item-destruction mechanism
found, and round 214's `procRange` census corrected from 154/612 to
300/612; 16th rigor spot-audit.** Primary task: pushed `itemTable32+0x0B`
("procRange", round 214) further. A fresh whole-overlay census of
`actor+0x6a7` across the battle overlay (both discs) confirmed bit 0's
consumer is exactly the already-documented one-shot proc-chance formula
(no other reader/writer exists anywhere in the overlay) and found a
genuinely new bit-1 consumer: `fcn.8005b170`, a per-party-member
phase-start "chance of breaking" check for **ordinary weapons** (item ids
422-459), gated on a battle-context flag bit, reading a `{itemId,percent}`
table that matches shipped item-description text 18/20 (2 real,
precedented data-vs-text mismatches). This is a second, independently
working item-destruction primitive alongside the already-documented (and
non-functional for its stated scepter target) `destroyEquippedItem` —
correcting an "exactly one such primitive" framing that had stood since
round 214's own sibling doc. Separately, round 214's `procRange` census
(154/612, believed weapon-only) undercounted: the real figure is 300/612,
confirmed general item-quality stat (not weapon-specific) via decisive
tier-scaling evidence in named non-weapon helm families. Secondary task:
16th rigor spot-audit, this time on `dungeon-field-mechanics.md` § 5 (jump
mechanics) — this doc's earliest (2026-09-17) pass, never previously
re-derived from raw bytes. Clean re-confirmation on both discs, with one
scoping nuance: a broader census than the doc's own claim finds 5 hits
where the doc claims 3, but the 2 extras are unrelated code/struct
collisions once the doc's own actual (narrower) predicate is applied
precisely — a real instance of a census needing to match the claim's
literal scope, not a doc error. Both scripts `ALL CHECKS PASSED` both
discs; full triad unchanged from baseline. Commit `0b1de3e`.

**Round 216 (2026-09-27): 17th rigor spot-audit — `battle-logic.md` §83.2's
camera-instance-field census, a same-count-but-wrong-membership case.**
§83.2 (from round 182's own investigation) claimed a windowed scan found
"six real reads of `instance+0x6`/`+0x8`... every one of them falls inside
this one function's own body (`fcn.8009cd04`)... 16 total register uses."
A fresh, register-liveness-respecting census over the WHOLE 36,600-byte
cached region (not just the assumed-sufficient one function) reproduced
the SAME count (6 read-bearing sites) while getting the actual membership
wrong in two compensating ways: one of the doc's six cited sites
(`0x8009d76c`) is not a read at all — it's a STORE (the routine's own
ease-out write), silently counted into the "16 total register uses" along
with a second, entirely uncited write-only reload site (a "phase 2"
analog whose own reload instruction the doc's disassembly listing had
simply omitted); and a genuinely new, previously-uncensused READ of
`instance+0x6` exists OUTSIDE `fcn.8009cd04` entirely (`0x8009c19c`, in the
post-enemy-init one-time setup code), refuting the "every one of them
falls inside this function" completeness claim. The two errors (one false
inclusion, one false exclusion) happened to cancel in total count, which
is exactly why nobody had caught it — see the new "second instance"
section in `fixed-lookahead-window-census-count-is-a-window-size-
artifact.md`, sourced from this round: a re-scan reproducing a doc's exact
headline count is not itself confirmation; the matched-address SET must
be diffed. The new out-of-function read site is also a genuine small
finding: it's a second writer of `ctx+0x1142` (the field §82.2 calls
"already seeded once" and §83.3 reads back in a battle-intro spin-wait),
resolving a previously-missing link between the two sections rather than
contradicting either. No `src/` engine consumer exists for this whole
arena-camera-anchor mechanism (0 hits for `0x1142`/`0x1148`), so this is a
documentation-only correction. Verified:
`verify-camera-instance-field-census-round216.ts`, both discs, 0
deviations, plus a diagnostic fixed-window sweep (1/2/4/6/10/16/30/60
instructions → 0/4/7/8/9/9/11/12 sites) showing the naive count never
stabilizes on its own. Full triad unchanged from baseline (5 tsc errors,
110 eslint errors, 119 files/1891 tests). Commit `7d40267`.

**Round 220 (2026-09-27): verification-bar remediation continues (rounds
218-219's own compliance sweep was itself incomplete) — 21 scripts fixed
across two commits, plus one genuine new engine finding.** Primary task:
finish the 9 candidate scripts round 219 had flagged but not yet resolved.
7 were real violations (a `build/cache/...`-only read with no live disc
extraction, and/or missing disc2 coverage entirely); 1 more was borderline
(a cache-backed identity check with no live read) and got fixed anyway; 1
(`verify-character-intro-psp-oracle.ts`) is legitimately PSP-`.prx`-only by
design, out of scope. All 8 rewritten to read live via `vp-corpus.ts`
(`openDiscInfo`/`findEntry`/`readToc`/`readVbin`/`extractMainExecutable`)
and checked on both discs; `verify-slaved-actor-consumers.ts`'s 20-entry
hardcoded `IMAGES` table was replaced with a shared `liveImages(discId)`
builder now reused verbatim across several scripts. Fixing one of these
(`verify-platform-record-tail-fields.ts`) surfaced a real prior-round
artifact: the dynamic-platform record's `+0x2e` raw-kind byte, documented
in `dungeon-field-mechanics.md` §21.22.3 as having "zero readers anywhere,"
in fact has a second real reader once the corpus is complete —
`0x80048d34` (`lbu $a0,0x2e($s0)`), feeding a `÷10` magic-number divide and
2 downstream calls per platform-array record; doc corrected in place with
a `> Correction (round 220)` block, `dungeon-field-mechanics.md` §21.22.3,
and a new open TODO row (`vp1psx-platform-rawkind-second-reader`) to trace
those 2 callees. This whole finding is the account's clearest instance yet
of `struct-field-scan-blind-to-biased-base-pointer.md`'s pattern at scale:
the raw literal-displacement census went from 0 hits (incomplete, largely
single-disc corpus) to 334 raw hits once corpus completeness was fixed,
collapsing to 6 distinct base-register-provenance-rooted addresses under
symbolic bias tracking — 3 coincidental collisions against unrelated
same-offset structs, 2 already-documented, 1 genuinely new (see that
lesson's "Eighth confirmed instance"). Systemic bug found along the way,
and now the account's clearest confirmed case of a copy-paste-propagated
error: ~10 scripts across the project had `base: 0x80010000` (the raw
`t_addr` literal) applied directly to a header-included raw SLUS buffer,
off by exactly the 0x800-byte PS-X EXE header — correct is `t_addr -
0x800 = 0x8000f800` (see `game-re-tooling/psx.md`, updated this round to
flag the copy-paste propagation risk explicitly). Also found and fixed a
genuinely corrupted `build/cache` artifact (TOC slot 2293, disc1: cached
at 22,528 bytes against the SLZ block's own declared 2,944-byte
decompressed size on BOTH discs — stale trailing garbage from an adjacent
block that earlier, cache-only census scripts had been silently scanning
as if it were code) and a `startsWith('slot2292 (field overlay)')`
prefix-match bug in `verify-section3-consumers.ts` that silently
misclassified every disc2 hit (labeled `'... (field overlay, disc2)'` —
a comma, not the expected closing paren, sits at the tested position) into
an unbucketed "other" pile for an unknown number of prior rounds — see the
new `hardcoded-label-prefix-silently-stops-matching-on-suffix-insertion.md`
lesson, sourced from this round. Secondary task (21st rigor spot-audit):
re-ran round 219's own "does this verify script violate the live-disc-read
bar" grep sweep fresh rather than trusting its prior "11 candidates"
count, and found 13 MORE genuine violations the earlier sweep had missed
entirely (`verify-actor-default-field-init.ts`,
`verify-room-flipy-disassembly.ts`,
`verify-room-type4-payload-bytes123.ts`,
`verify-spawn-platform-stack-operand-order.ts`,
`verify-kind7-task-continuation.ts`,
`verify-object-kind-7-8-consumers.ts`,
`verify-object-kind8-fun8003bb4c-caller.ts`,
`verify-shoulder-button-remap.ts`,
`verify-save-unpack-additional-fields.ts`,
`verify-config-menu-table-unreferenced.ts`,
`verify-fb00-seat-indexed-read.ts`,
`verify-fb00-tail-words-corpus-scan.ts`,
`verify-slaved-actor-eligibility-residue.ts`) — all fixed the same way
(live disc read, both-discs coverage), each now carrying its own `>
Correction (round 220)` header. Widening the hit count for 3 of these
(which previously had zero disc2 coverage at all, not even a claimed
identity check) confirmed the extra hits are pure per-disc duplication (90
distinct addresses seen twice), not new content. See the round-220
addendum in `tracker-prose-is-not-evidence.md`'s eleventh variant: a
sweep's own reported hit count is a snapshot of what got checked that
session, not a ceiling on how many real instances exist — re-run the
identical query fresh every follow-up round rather than trusting a
remembered result. Full triad unchanged from baseline both commits (5 tsc
errors, 110 eslint errors, 119 files/1893 tests). Commits `a65106c` (8
scripts + `dungeon-field-mechanics.md` + `TODO.md`) and `62cfb5c` (13
scripts).

**Round 221 (2026-09-27): a genuinely independent 3rd verification-bar
sweep finds 3 more real violations; closes
`vp1psx-platform-rawkind-second-reader` with a correction to round 220's
own hedge; 22nd rigor spot-audit re-derives the campaign's oldest
unaudited load-bearing formula.** Primary task: rather than re-running
round 219/220's own grep shape, cross-referenced every
`tools/valkyrieprofile/*.ts` against "imports `./vp-corpus.ts` AND
contains both `'disc1'` and `'disc2'` string literals" — a genuinely
different query. Found 4 candidates, 3 real: `verify-battleoverlay-
regiontypes.ts` and `verify-slotsubindex-round66.ts` were both reading a
stale `build/cache/valkyrieprofile/codeoverlay_slot1490.bin` for their
main census with zero live reads (the latter also had a disc1-only
`fetchTextBank()` helper); `verify-save-preview-refresh-site.ts` DID
live-read via a local helper but every call site was hardcoded to disc1,
plus its cache-filename scheme had no disc suffix (a latent collision
risk, fixed alongside). All 3 rewritten to a `readOverlay(discId)` /
disc-qualified-cache-filename pattern and re-verified on both discs
(173/173, 152/152, 83/83 checks respectively). The 4th candidate
(`verify-character-intro-psp-oracle.ts`) is a correct exclusion — it
cross-references PSP's decrypted PRX modules as an oracle for an
already-resolved PSX claim, by design touching no PSX disc bytes.
Secondary task: closed `vp1psx-platform-rawkind-second-reader`
(`dungeon-field-mechanics.md` §21.22.3). The enclosing function is
`0x80048434`-`0x80048e38`, the field overlay's per-frame moving-platform
render pass — it resolves a platform record's raw `kind` byte against the
room's own ALREADY-CONFIRMED scroll/parallax-layer table (§9.6.13), not a
novel structure. Round 220's own hedge ("computes `rawKind/10`... feeds
the RESULT into two calls") was independently re-simulated in plain JS
per `hand-traced-byte-shuffle-needs-independent-resimulation.md` and found
imprecise: the divide-by-10 quotient is used ONLY to test divisibility,
never written back — the real search key is `rawKind` itself, unmodified,
except a narrow clamp to 30/`MAIN` when it's not a clean multiple of 10
AND falls in `[30,130)`, mirroring the constructor's own validity gate. A
corpus census then found a genuine bimodal split (every unmodified
value < 30 always matches a scroll-layer kind; every unmodified
multiple-of-10 value >= 40, including `kind=70` at ~87% of all real
spawns, never does) and traced the allocator to confirm the scroll buffer
is sized at exactly `count*60` bytes, zero slack — so an unmatched search
lands exactly at the array's own end, a genuine residual flagged as
out-of-scope for statics rather than guessed at. An exhaustive `jal`-word
scan across all 354 top-level SLZ blocks on both discs plus a literal
address-construction scan both confirm zero callers, matching a sibling
routine's already-documented unresolved-caller shape. Verified:
`verify-platform-rawkind-render-binding.ts`, 83/83 checks, both discs.
Tertiary task (22nd rigor spot-audit): rather than another compliance
sweep, a fork grepped `TODO.md` plus doc-tree "Round N" closure dates for
an old, thin-evidence target and surfaced `battle-logic.md` §13.7's
party-side equipment/level->stat recompute (`fcn.8005e5d8`, slot 1490) —
one of the campaign's OLDEST closures (2026-08-22, a `re-codebreaker`
escalation), load-bearing for essentially all combat math and quoted
verbatim elsewhere (`item-skill-system.md` §3), yet a targeted grep for
every address the formula cites found zero committed verify scripts ever
re-deriving it. Hand-traced the whole function fresh against real
disassembly, both discs: maxHP, ATK, DEF, and all four "further derived
stats" (`fieldC4`/`C6`/`C8`/`CA`) match the doc's pseudocode
instruction-for-instruction, including the item-table `-1`-indexed
negative-displacement convention and all four accessory-bonus branches
sharing one magic constant (`0x51EB851F`). One genuine correction: the
doc's own header cites the function's span as `0x8005e5d8`-`~0x8005ee00`
(tilde-hedged); the real end is `0x8005eccc` (`jr $ra`), ~15% shorter — a
different, unrelated function starts immediately after and wasn't
investigated further. A clean re-confirmation overall, not a bug hunt.
Verified: `verify-battle-stat-recompute-round221-audit.ts`, 95/95 checks,
both discs. Full triad unchanged from baseline both commits (5 tsc
errors, 110 eslint errors, 119 files/1893 tests). No new pitfall files
were needed this round — every technique used (independent
resimulation, live-both-discs verify scripts, disassembler-text
comparisons over hand-encoded hex, inherited-dirty-tree isolation via
targeted `git add`) was already covered by existing lesson files.
Commits `fa3d69b` (primary + secondary) and `07b969b` (tertiary).

Round 223 (24th rigor spot-audit) targeted `dungeon-field-mechanics.md`
§3's own very first-pass (2026-09-17) pad-record table, whose third field
had sat as "third mask (release/repeat, not traced)" for 22 rounds — a
concretely-named, never-executed next step per the "named-blocker-may-be-
an-untried-next-step" lens. Traced the producer to a fifth, previously-
unnamed resident pad-library function (alongside the already-documented
`0x80014484`/`0x8001449c`/`0x80013dd0` trio, `data-structure.md` §20.24):
a per-port saturating "consecutive polls held steady" counter compared
against a fixed threshold (confirmed initialised to 20), dispatching
between the SAME array the already-documented "edge/newly pressed"
reader returns (below threshold) and the raw per-poll pad word (at/above
threshold) — VP1's digital-pad key-repeat trigger. Found as a side
effect: `held`/`edge` are themselves per-poll OR-accumulators, reset once
per game frame by a sibling function called right after the sampler's
own read — never documented before, and the reason the repeat path must
fall back to the raw word (edge only pulses once per transition and
would otherwise never fire again). Two independent consumers (a field-
overlay menu-cursor direction dispatcher; the scene-script VM's pad-
state-export routine, which copies the third mask into the same struct
as held/edge) confirm it's live, consumed state. No `src/` port: this
project has no menu/list-navigation module yet to receive the finding, so
it stays doc-only pending that subsystem. Verified:
`verify-pad-repeat-mask-round223-audit.ts`, 176/176 checks, both discs,
every address independently re-disassembled from raw bytes (one real
self-caught transcription slip during drafting — an address block
reconstructed from memory of an earlier scrollback dump was off by a
few instructions; caught and fixed by re-running a fresh, narrow probe
before finalizing the checks, exactly the discipline `shared-load-base-
plus-scrollback-transcription-misattributes-address.md` prescribes).
Secondary task: spot-checked 5 previously-untouched verify scripts for
verification-bar compliance — 2 compliant (live, both-discs disc reads),
2 legitimately exempt (a pure-math bound-proof over an already-verified
formula; an artbook-PDF-based visual identification with no disc bytes
involved), and 1 real violation left deliberately unfixed
(`verify-character-intro-psp-oracle.ts` reads only a cached decrypted PSP
PRX directory with no live PSX check at all — fixing it is PSP-side
infrastructure work, explicitly out of scope this round). New
generalizable lesson: `undocumented-pad-field-adjacent-held-edge-is-
repeat-trigger.md` (sourced from here). Full triad: 5 tsc errors (all
pre-existing, from an unrelated concurrent session's in-progress
`psx-cd.ts`/`psx-str.ts` removal — verified none of this round's new code
touches those modules), 110 eslint problems (baseline, unrelated), 119
files/1894 tests passing. Commit `16a0022`.

## Corpora-index row text formerly inline in `game-re.md`

Moved verbatim from the always-loaded agent prompt during the 2026-10 restructure.

| `~/Development/valkyrie` | Valkyrie Profile (PSX), Valkyrie Profile 2: Silmeria (PS2), Valkyrie Profile: Lenneth (PSP remaster). VP1's formats are all solved; the account's longest-running gameplay-*logic* (not format) RE campaign now runs a periodic rigor-spot-audit series against its own prior closures (22 audits by round 221, spanning all 6 major docs) rather than only chasing new open items — the worked source for Method § 7's "Re-audit, periodically", and for round 210's sharper variant: a systematic doc-tree grep for small-hand-picked-sample "checked/confirmed/verified on N" claims (not just formulas, plain "N/N" coverage claims too) found a real, previously-unquantified 2.8%-of-parts field-sprite scaling gap a 4-slot sample had missed, see `formula-check-small-sample-misses-conditional-rounding-term.md`; round 213's own audit (a terrain-chunk header table) mostly re-confirmed cleanly but caught a real "4 on every chunk seen" constant that turned out to be 3-or-4, never independently re-checked before. That round is also this campaign's sharpest instance yet of "declared unanswerable without live capture" being wrong: a field-sprite render-mode's caller-side gating fields turned out to be literal script-settable properties (`ACTCMD_SETPROP`, `scene-script-vm.md` §12) the prior round never cross-checked against its own doc, closing the item from a pure corpus census with zero live capture — see `doc-self-cross-reference-before-fresh-disassembly.md`'s latest instance and `fixed-global-base-register-mistaken-for-per-call-parameter.md`. Round 214's own audit re-derived a `re-codebreaker`-sourced multi-instruction dataflow-census total (an item stat table's indexing idiom) and found the doc's "11 sites, 3 unrelated" figures were an artifact of an unstated fixed lookahead window, not a fact about the code — the real, liveness-based total is 9, and the "3 unrelated" hits were actually 1, misclassified as belonging to the wrong field entirely — see `fixed-lookahead-window-census-count-is-a-window-size-artifact.md`, sourced from here. The corrected hit revealed a genuine new mechanic as a side effect: `actor+0x69a`/`+0x69b` (previously documented as an enemy-stat-record-sourced field) has a second, disjoint PARTY-side writer sourced from the item stat table instead, the same "enemy record vs. equipped-item stat, same actor destination" pattern the project's damage-formula already established for a sibling field triple. Round 215 found a SECOND, independently working item-destruction mechanism (`fcn.8005b170`, an ordinary-weapon "chance of breaking" check reading a table matching shipped item text 18/20) that had been sharing a status bit with the already-known proc-chance consumer — correcting an "exactly one item-destruction primitive" framing — and corrected that round's own `procRange` census from 154/612 (weapon-only) to 300/612 (general item-quality stat, confirmed via non-weapon tier-scaling). Round 216 (17th rigor spot-audit) found a sharper variant of the round-214 lesson: a liveness-respecting re-scan of a camera-instance-field census reproduced the doc's exact headline count (6 sites) while its actual membership was wrong in two compensating ways (one mislabeled write counted as a read, one genuinely missed read outside the assumed function) — see `fixed-lookahead-window-census-count-is-a-window-size-artifact.md`'s "second instance". Round 217 (18th rigor spot-audit) re-derived a tile-composited sprite format's own "20,928/20,928, zero deviations" corpus-wide claim from scratch (a true blind SLZ-magic scan plus an independent second command-stream walker, both discs) — every claim held except the doc's own worked packing formula, whose literal (globally-counted) reading mismatched on every multi-texture-page resource, resolved by scoping the counter per `tpage` value instead (see `packing-formula-index-must-reset-on-mode-selector-change.md`, sourced from here) — and separately fixed a real defect this same audit series had left behind: round 216's own committed verify script still asserted its PRE-correction completeness claim, failing on every re-run despite the doc already being right (see `doc-self-cross-reference-before-fresh-disassembly.md`'s 28th instance, sourced from here). Round 218 (19th rigor spot-audit) found a quieter variant of the same family: a fixed-15-instruction-window `flags0f`-bit census's own committed script had already been correctly superseded ONE DAY LATER by an unbounded liveness-respecting rescan in a SIBLING doc file (data-structure.md § 13.3d, which duly carries its own `> Superseded` block), but the section the claim ORIGINATED in (battle-logic.md § 94.4) and its own script's header comment were never given the matching correction — and crucially the script's individual checks never failed (narrowly true of the 15-window scope all along), so nothing ever flagged the staleness; fixed by relabelling the checks' own descriptions to state their true window-bounded scope rather than implying completeness — see `fixed-lookahead-window-census-count-is-a-window-size-artifact.md`'s new addendum. Round 219 (20th rigor spot-audit, and the campaign's first round to audit verify-script COMPLIANCE rather than doc-claim correctness) fixed round 218's own new script (it read a single stale cached overlay file with zero live disc reads, despite citing live-reading siblings), then grepped every committed `verify-*.ts` for the same "cache read, no live-source import" shape and found 2 more genuine pre-existing violations spanning early-to-late rounds (one whose own comment falsely claimed a byte-identity re-check it never performed, cited verbatim by a second script as justification) -- all fixed the same way (live `vp-corpus.ts` extraction, both discs, explicit byte-identity check). Also closed a genuine Disc-1-only census gap in the campaign's oldest audited "resolved" row (`vp1psx-collision-primitive-types`, closed round ~9): its container/type-enumeration claim (nine types, clean chain walk) had never been checked against Disc 2 in either the doc or its regression test, though a LATER doc section had already cited the right Disc-2 number in passing; re-derived live and now `it.each`-parameterized over both discs. See `tracker-prose-is-not-evidence.md`'s eleventh variant, sourced from here. Round 220 (21st audit) re-ran that same compliance sweep fresh and found 13 MORE genuine violations round 219's own pass had missed, fixed a copy-paste-propagated `t_addr` off-by-0x800 base bug spanning ~10 scripts, and found one genuine new engine reader via a struct-field census that went from 0 to 334 raw hits once corpus completeness was restored (see `struct-field-scan-blind-to-biased-base-pointer.md`'s "Eighth confirmed instance"). Round 221 ran a genuinely independent 3rd verification-bar sweep (grepping for the import+both-discs-literal shape rather than round 219/220's own query) and found 3 more real violations, fixed live on both discs; also closed `vp1psx-platform-rawkind-second-reader`, correcting round 220's own hedge ("feeds the divided result") via an independent JS resimulation of the hand-traced divide-by-10 idiom, per `hand-traced-byte-shuffle-needs-independent-resimulation.md` — the real search key is the raw byte UNMODIFIED except a narrow clamp, not the quotient. Its 22nd rigor spot-audit, found via a `TODO.md`+doc-date grep rather than another compliance sweep, re-derived `battle-logic.md`'s core party stat-recompute formula — one of the campaign's OLDEST closures, load-bearing for all combat math, with zero prior committed verify script despite being quoted verbatim elsewhere — fully byte-exact on both discs, a clean re-confirmation with one minor function-boundary correction. Round 222 (23rd rigor spot-audit) re-derived the weapon/type-effectiveness multiplier (`fcn.8003abf4`, twice-corrected in prose, never independently re-checked) and found a genuine new mechanism this time, not just a clean re-confirmation: two structurally-parallel dispatch paths sharing the identical sentinel value (`override === 1`) diverge completely in what it means to each — one path returns a flat multiplier, the other indexes a previously undocumented static table by an entirely different operand (see `parallel-lfo-vcmds-may-clamp-asymmetrically.md`'s second confirmed instance) — plus a stale source-code doc comment that had drifted from a SECOND correction superseding the first, while the shipped consumer code had already implemented the fix correctly (comment-only staleness, not a logic bug). Round 223 (24th rigor spot-audit) ran down `dungeon-field-mechanics.md` §3's own 22-round-old "third mask, not traced" pad field to a full digital-pad key-repeat mechanism (a fifth previously-unnamed resident pad-library function dispatching between the confirmed edge array and the raw pad word by a saturating hold-duration counter vs. a fixed threshold), plus a new structural finding that held/edge are themselves per-poll OR-accumulators reset once per frame — see `undocumented-pad-field-adjacent-held-edge-is-repeat-trigger.md`, sourced from here. Round 224 (25th rigor spot-audit) re-derived a collision-primitive type dispatcher's own instruction-level citations byte-exact (both discs, zero prior verify script existed for any of it) and found a real gap in a SIBLING document's running "obj+0xe4 bit-3 writer" tally that had never cross-referenced this table's own already-published ladder-engage row, plus a brand-new sixth writer (a ledge-engage clear) — see `doc-self-cross-reference-before-fresh-disassembly.md`'s 29th instance. Its compliance spot-check also found a verification-bar violation round 221's own differently-shaped sweep query had structurally false-cleared (a file whose SECONDARY claim already used a live both-discs scan, masking a stale single-disc read still driving its PRIMARY claims) — see `tracker-prose-is-not-evidence.md`'s 12th variant. Round 225 (26th rigor spot-audit) found the mirror-image trap: a doc's own already-published NEGATIVE census ("9 live opcodes, 0 corpus occurrences") directly falsified an unhedged POSITIVE liveness claim in 3 other sections of a sibling doc about that exact opcode ("written from the field... by a dedicated scene-script opcode") — confirmed dead code via byte-exact handler-identity disasm plus an independent full-corpus occurrence re-tally, doc-only fix (no `src/` consumer needed) — see `doc-self-cross-reference-before-fresh-disassembly.md`'s 30th instance. Its compliance spot-check (5 scripts) found the 12th-variant shape 5 more times, including an `existsSync`-guarded silent-skip and a "both-discs" check comparing two differently-dated stale cache files to each other instead of to a live disc — see `tracker-prose-is-not-evidence.md`'s 12th-variant follow-up. **This row is now large enough (200+ rounds of history) to warrant a dedicated future harvest pass whose sole job is compressing rounds into a shorter summary while preserving lesson-file pointers — flagged, not done this pass, to avoid lossy edits under a harvest's own time budget.** | `game-re-corpora/valkyrie.md` |

## Lessons sourced from this corpus (full list)
`artbook-mixes-real-world-photos-with-in-game-cg.md`, `caller-saved-invalidation-misses-parameter-reused-across-call.md`, `call-site-address-misread-as-load-base.md`, `centroid-spread-blind-to-rigid-transform-candidates.md`, `check-expression-bitwise-or-precedence-masks-comparison.md`, `confirmed-index-shared-by-second-parallel-table.md`, `cross-platform-decode-oracles.md`, `data-dir-may-hold-a-second-unopened-reference-pdf.md`, `dataflow-census-root-must-cover-publish-sites-and-full-function-body.md`, `dataflow-chase-must-track-destination-not-mere-reference.md`, `decompose-quaternion-non-unit-needs-normalize.md`, `differential-oracle-blind-to-harness-injected-state.md`, `disasm-text-never-folds-lui-load-pair-into-resolved-address.md`, `doc-self-cross-reference-before-fresh-disassembly.md`, `encrypted-directory-defeats-structural-scan.md`, `enum-value-named-via-cross-subsystem-formula-reuse.md`, `field-centric-bit-census-blind-to-sibling-reuse-and-split-mask.md`, `file-offsets-vs-segment-relative.md`, `fixed-global-base-register-mistaken-for-per-call-parameter.md`, `fixed-lookahead-window-census-count-is-a-window-size-artifact.md`, `fixed-stride-scan-from-unaligned-anchor-misses-true-boundary.md`, `formula-check-small-sample-misses-conditional-rounding-term.md`, `formula-fix-nets-identical-or-scaled-result-for-default-parameter-case.md`, `fresh-reimplementation-reverify-manufactures-false-confirmation.md`, `gating-prose-may-hide-independent-shared-byte-access.md`, `generic-demuxer-misses-custom-pes-audio.md`, `genre-mechanic-asserted-by-tracker-needs-primitive-existence-check.md`, `hand-traced-byte-shuffle-needs-independent-resimulation.md`, `hardcoded-label-prefix-silently-stops-matching-on-suffix-insertion.md`, `image-only-pdf-grep-negative-is-vacuous.md`, `indexed-operand-needs-base-provenance.md`, `index-writer-may-be-a-loop-counter-not-a-selection.md`, `individually-failed-fixes-may-combine-cleanly.md`, `in-game-text-states-own-formula-constant.md`, `iso9660-tree-near-empty-check-raw-lba-toc.md`, `local-decode-cache-may-be-stale-reverify-fresh.md`, `lui-addiu-negative-low-half-borrows-from-high-half.md`, `main-chunk-role-masks-own-unopened-payload.md`, `mips-delay-slot-instruction-always-executes.md`, `mirrored-dedup-gate-tests-sibling-bit-not-own.md`, `narrow-opcode-form-census-false-negative.md`, `near-complete-word-decode-missing-one-char-is-hybrid-cipher-boundary.md`, `negative-from-addressing-root-not-shapes.md`, `nested-block-census-isprologue-gate-drops-non-function-aligned-chain-link.md`, `offline-compositor-full-canvas-not-viewport-crop.md`, `overlay-census-blind-to-region-embedded-code-modules.md`, `packing-formula-index-must-reset-on-mode-selector-change.md`, `parallel-lfo-vcmds-may-clamp-asymmetrically.md`, `per-resource-subset-alphabet-defeats-corpus-scan.md`, `point-projection-gte-usage-can-be-real-effect-geometry.md`, `port-preserves-bootstrap-resource-slot-numbers.md`, `proximity-pairing-fallback-fails-on-near-identical-siblings.md`, `r2-string-heuristic-hides-instruction.md`, `record-array-alternatives-vs-parts-footprint-test.md`, `reference-census-built-from-named-output-not-raw-pushes.md`, `refuted-premise-does-not-imply-refuted-conclusion.md`, `repeating-chunk-descriptor-mistaken-for-flat-header.md`, `reserved-slot-zero-shifts-extractor-index.md`, `resolved-edge-case-may-be-wrong-header-width-artifact.md`, `resource-id-in-strided-record-field-carried-by-callback-object.md`, `rgba-clut-vs-image-byte-identity.md`, `rle-decode-succeeds-on-garbage.md`, `romhacking-community-tools-first.md`, `runtime-valued-script-operand-is-usually-a-parameter.md`, `same-magic-different-format-by-referencing-context.md`, `scratch-slot-dual-role-verify-against-real-platform-struct.md`, `self-describing-length-field-mistaken-for-corpus-constant.md`, `self-relative-offset-ambiguity-resolved-by-corpus-vote.md`, `shared-load-base-plus-scrollback-transcription-misattributes-address.md`, `sibling-classifier-exclusion-via-already-solved-acceptance-test.md`, `source-rect-may-be-upload-key-into-packed-sibling-blob.md`, `spawner-install-literal-outranks-backscan-prologue.md`, `standard-codec-delegate-to-trusted-decoder-not-hand-reimplementation.md`, `static-image-zero-dump-refutes-authored-template-hypothesis.md`, `struct-field-scan-blind-to-biased-base-pointer.md`, `sub-overlay-base-is-parent-base-plus-size.md`, `subset-contiguity-needs-complement-check.md`, `test-fixture-encodes-same-wrong-model-as-implementation.md`, `traced-enum-label-corroborated-by-carrier-name-set.md`, `tracker-prose-is-not-evidence.md`, `undocumented-pad-field-adjacent-held-edge-is-repeat-trigger.md`, `unflagged-cluster-beats-flagged-subset.md`, `unit-magnitude-oracle-disambiguates-numeric-encoding.md`, `unreachable-return-explained-by-self-overwriting-overlay-swap.md`, `value-consumer-trace-must-continue-past-first-branch.md`, `verify-escalation-artifacts-not-just-claims.md`
