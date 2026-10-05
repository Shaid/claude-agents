# strike — Desert/Jungle/Urban Strike (Amiga OCS/AGA + Genesis + SNES)

**Project root:** `~/Development/strike`

Two Amiga compressors across sub-eras (LR88/PowerPacker on AGA; RNC1 + nested RNC2 on OCS, `tools/shared/{lr88,rnc1}.ts`) and two Genesis codecs (Strike LZSS, plus a second RLE found by tracing the LZSS decompressor's own caller dispatch). Sourced `round-looking-longwords-are-centred-bitmap-rows.md`, `jump-table-noop-means-handled-elsewhere.md`, `shared-scratch-copper-list-palette-patch.md` (Jungle Strike AGA's `status`/`brief`/`menubgd`/`menubgd2` screens patch a shared scratch copper list at runtime instead of using one static list each — cracked by tracing each screen's own load call site to its patch-table source, not by scanning for copper-list shapes; `status` confirmed via quantified reference-screenshot match). Jungle Strike AGA's `weapons` file (HUD weapon icons + world projectile sprite bank) is now also solved — a `LAB_0365` byte-consumption invariant that a prior session had compared against the file's *crunched* size (and filed as "mechanism confirmed, file identity unconfirmed" — sourced `crunched-size-mistaken-for-decrunched-size-invariant-mismatch.md`) turned out to match the *decrunched* size exactly once re-checked, unlocking a byte-exact geometry recovery and a decisive render (8 named icon/animation groups, 4 with legible bitmap-font labels reading "HYDRA"/"HELLFIRE"/"CHAIN"/"MINE" — real weapon names); `statmapN`'s HUD icon-glyph palette is also now confirmed (`STATUS_PALETTE_12BIT`, not the world-map palette borrowed by analogy — found by tracing the render routine's only caller up to the already-documented `status`-screen palette-install site, the same `shared-scratch-copper-list-palette-patch.md` mechanism one hop further). See `docs/junglestrike/`, `docs/desertstrike/`

## Desert Strike Amiga (`docs/desertstrike/amiga/`)

Custom trackloaded disk format (not a named-file archive) predating Jungle
Strike's LR88/PP20 build; uses RNC1 (Rob Northen Compression v1) for the
whole-disk directory table, with a second-generation **RNC2** found nested
inside several `hunk-wrapped` chunks' DATA hunks. Confirmed: a 96x72px,
6-bitplane row-interleaved **object atlas** sprite format (5 colour planes
+ 1 inverted-polarity mask plane, followed — not preceded — by a 32-entry
12-bit-RGB palette table; `tools/desertstrike/object-atlas.ts`) found as
clustered RNC1 sub-blobs inside `disk3-02/05/09/13`'s DATA hunks — 49
shipped sprite frames: buildings, vehicles, HUD label text, portraits.
Cracked by re-reading the *whole* 5,248-byte frame (not the 5,184 bytes
left after stripping an assumed leading header) — a confirmed hit for
`round-looking-longwords-are-centred-bitmap-rows.md`'s trailing-field
variant. Also confirmed: Desert Strike's 5 "named audio cue" chunks are
standard ProTracker `M.K.` modules, all 5 now shipped playable (2
self-contained, 3 pattern-only stubs spliced against the `DMCA` sample
bank with 100% name resolution and third-party verification via
`openmpt123`) — a confirmed hit for
`canonical-field-offsets-before-custom-header.md`. The `DMCA` chunks are a
confirmed sample-bank catalog over raw 8-bit PCM, extracted to 81 WAV
files at an inferred-not-confirmed standard PAL-Amiga sample rate (no rate
field exists in the format, and the loader binary was disassembled and
found not to set up Paula audio at all).

**`disk1-00` (the raw loader/engine, always-uncompressed entry 0)
disassembled**: contains a leaked `HUNK_DEBUG`-shaped source-text block
(~5.4 KB of literal 68k assembler embedded verbatim, surviving because the
custom trackloader's `DoIO` never strips hunk/debug structure from a raw
blob) that source-confirmed the whole-disk directory record's field
layout and named 2 UI graphics embedded directly in the loader (an
"INSERT DISK" icon and a disk-error comic, both confirmed via legible-text
render + byte-identity with 3 other on-disk copies) — see the
`HUNK_SYMBOL`-before-anything-else Method note for the general form of
this technique. Also gave hypothesis-level filenames (via a dead
`LOAD_MEDIA="FILE"` code path) for the still-undecoded `hunk-wrapped`
chunk corpus, and two informative negative results (no `DMCA`/Paula setup,
no `ANIM` `DLTA` delta-decode algorithm in this specific binary — that
code lives in one of the still-undecoded chunks instead).

**A `re-codebreaker` escalation overturned a prior "confirmed" decode and
solved two open items at once.** `disk3-00/04/07/11` had been documented
confirmed as a `u16 width, u16 height` + flat chunky-8bpp-pixel format;
this was wrong — the payload bytes are **tile indices**, not pixels,
indexing a 16x16px/5-bitplane/row-interleaved tileset that turned out to
be the corpus's *other* standing open item (`disk3-01/08/12`, previously
an unsolved "sparse dither texture" — the format's own unexplained
10-byte autocorrelation period was the scanline stride all along, see
`autocorrelation-period-is-the-scanline-stride.md`). Sourced/sharpened
`header-shape-ambiguous-pixel-encoding.md` with a third case: a
byte-count invariant that's satisfied identically by two different
payload semantics (pixel vs. tile-index), where the *wrong* interpretation
still passes the visual-oracle bar because tilemap indices are naturally
spatially smooth. This tile format is byte-for-byte identical to Jungle
Strike AGA's already-confirmed `worldNblks`/`worldNmap` — the same engine
lineage two games apart (Desert Strike uses u8 indices where Jungle Strike
widened to u16). `tools/shared/amiga-hunk.ts` is a general HUNK_HEADER
parser (masks `&0x3FFFFFFF` on both the header size-table AND the
in-stream type tag — Desert Strike's linker embeds MEMF_CHIP/MEMF_FAST
flags in-stream too, unlike Jungle Strike AGA's `objects*`/`sprites*`).

**Standing open item: no player-vehicle (Apache helicopter) sprite found
on this platform** — the object atlas contains only a small single-colour
helicopter *icon*, and `disk1-00` (now fully disassembled) neither
contains nor references one. See `docs/desertstrike/amiga/data-structure.md`
and `docs/desertstrike/TODO.md`.

**The per-mission-bank entity/template array is now fully enumerated and
bound to real sprite content.** Each mission bank (`disk3-02/05/09/13`) has
its own array of per-entity-type "templates" (61/62/66/59 across the 4
banks — a self-referential `HUNK_RELOC32` recipe scan over-counted this at
first, 66/66/71/64 raw, from real templates' own internal pointer fields
re-matching the same recipe a few bytes inside themselves; fixed by
sorting all raw hits by offset and greedily accepting only non-overlapping
ones, see `self-referential-recipe-ghost-match-nested-in-real-match.md`).
Every template's every sub-object descriptor is now generically bound to
real sprite content in the matching entity sprite pool (`disk3-03/06/10/14`)
via a table-slot -> `root[k]` -> recursively-resolved leaf-record walk
(`readSpriteRootList`/`resolveSpriteGroupLeaves` in
`tools/desertstrike/entity-sprites.ts`, `tools/desertstrike/
entity-templates.ts`), 100% resolution, zero exceptions across the whole
corpus. This also **corrected a stale prior claim**: `root[1]` had been
documented as "a small, unrelated fixed-point parameter table, NOT a
pointer list" — it is in fact a real 5-entry relocated sprite-record
pointer list (a coherent small rotating-helicopter icon), the prior
survey script having only ever printed the root table's own slot values
without dereferencing them.

**The real template<-spawn binding mechanism is found and live-confirmed —
the per-mission spatial spawn grid plays no part in it.** The task premise
going in (a spawn-grid leaf record must carry a type/index selecting which
template to spawn) was wrong at the root, not just unconfirmed at the
field level: exhaustive static refutation of every candidate leaf field
(leaf`+0` pointer never lands in a bank's template region; `field8`'s max
value exceeds every candidate array size in every mission) was followed by
an `amiga-disasm` live-emulation trace of the real mission-init spawner,
which never reads the spawn grid at all. The real mechanism is a
bank-header manifest table at `+0x50` (27/30 spawns, `{templatePointer,
spawnCount}` records consumed directly, no lookup) plus 3 fixed
bank-header slots (`+0x44`/`+0x48`/`+0x54` = the player) for the remaining
3/30 — cross-checked byte-exact live against the already-known player
template address. `hunk0+0x7ae` (previously suspected as the spawner) is a
*different* routine (screen-space culling of already-spawned content via
direct pointer-table reads). Sourced
`cached-runtime-image-stale-past-boot-checkpoint.md` along the way (a
cached boot-time Musashi RAM dump, regression-verified only up to an early
checkpoint, was found stale for this later-reached routine — a live
`DUMP_RANGE` capture diverged from it at 2,237/2,560 sampled bytes). The
spawn grid's own leaf fields (position confirmed, `+4`/`+6`/`+12`/`+14`/
`field8`/`+18`/`+20` still unexplained) are now a separate, narrower open
item (`dsam-spawn-grid-consumer`) decoupled from template selection. See
`docs/desertstrike/amiga/data-structure.md` "Twelfth session" and
`docs/desertstrike/TODO.md`.

Jungle Strike AGA's `objects1`-`9` (per-mission entity/spawn table) and
`sprites1`-`9` are **confirmed**, closing a group stuck at "hypothesis" for
2+ prior passes: both are generic AmigaDOS `LoadSeg()` HUNK wrappers around
opaque data (`tools/shared/hunk-wrapper.ts`), but decoding the
`HUNK_RELOC32` block between the payload and `HUNK_END` — never parsed by
prior passes — showed `objectsN` carries real relocated pointers (258-762
each) while `spritesN` carries none, settling "entity table vs. flat pixel
data" before any disassembly. A full parse of every `JSR`-to-loader call
site in `JS` (extending a partial per-mission constant scan into all 84
load calls, zero false matches against known crunched sizes) then confirmed
`objectsN`'s self-relative-offset header + primary entity/spawn directory
byte-for-byte, and found `spritesN` consumed through a static per-vehicle
geometry table in `JS`'s own code (`LAB_0DDF`) structurally paralleling the
already-solved `heli_sprite`. Sourced `hunk-wraps-non-code-data.md` (now
also covers the `HUNK_RELOC32` oracle + a value-based "field whose value
equals the header size" technique for re-anchoring a table whose byte
pattern doesn't generalize across files). See
`docs/junglestrike/amigaaga/data-structure.md` "objects1-9: per-mission
entity/spawn table" and `js-code-structure.md` Section 2.7/2.8,
`tools/junglestrike/objects.ts`.

## Genesis/Mega Drive tilemap + overlay-tile bank (`docs/strike-megadrive-tilemap.md`)

Shared cross-game container spec (Urban Strike + Jungle Strike, byte-for-byte
identical record shape and reader routines at different addresses) for the
"draw tile N with flip/palette/priority at grid (x,y)" nametable format —
found via a `re-codebreaker` escalation that located a dedicated VDP-blitter
function (`fcn.00008272` Urban Strike / `$03F4EE` Jungle Strike) separate
from the generic resource loader. 32-byte header, three payload codecs (raw
u16, word-level PackBits, bit-packed indices into an embedded LUT). A later
`re-codebreaker` escalation cracked the format's own 5-record `format =
0x1A` "unhandled" outlier: those aren't a tilemap variant at all, they're 5
of 271 records belonging to a wholly separate **overlay-tile bank**
resource (`tools/shared/megadrive-overlay-bank.ts`) that reuses the exact
same 32-byte header template with 3 fields reinterpreted (one
reserved-always-zero tilemap field becomes a live tileset-slot index; one
per-record tileset pointer becomes a dead, bank-wide-constant field) and is
consumed by 3 different dedicated blitters the tilemap reader never
reaches. Confirmed via 6 independently-disassembled reader implementations
(3 routines x 2 ROMs), zero-deviation payload-size arithmetic across the
whole bank (322 + 221 records), and a from-scratch independent render
against the one statically-resolvable tileset slot (0 out-of-range cells,
legible HUD text, a bilaterally-symmetric icon confirming the H/V-flip bit
assignment). Sourced `shared-header-template-cross-resource-false-positive.md`
(the bank's slot-0 records were silently passing the tilemap scanner as
false positives) and `shared-tool-session-clobbered-by-fork.md` (radare2
MCP session state, re-verifying the escalation). Most of the bank (270
records across 30+ runtime-composed tileset slots) remains unrendered —
see `docs/urbanstrike/TODO.md`/`docs/junglestrike/TODO.md`.

## Urban Strike SNES (`docs/urbanstrike/snes/`)

First SNES target in this project — genuinely from-scratch, unrelated
toolchain/codec to the Genesis/Amiga builds despite being the same game (EA
apparently used a different internal team/tooling for this port). 2 MB
headerless LoROM+FastROM cart, 65816 CPU. Confirmed: ROM header/vectors,
boot trace to an SPC700 driver-upload dead-end, and — the key find — a
6-op tag-byte compression codec (LZ backref with *absolute-offset* [not
distance-back] backreferences, 8/16-bit arithmetic ramps, 2-byte pair
repeat, byte RLE, literal copy; `tools/urbanstrike/snes-tagbyte-codec.ts`)
plus the standard SNES 4bpp bitplane-interleaved tile format and 15-bit BGR
CGRAM palette (`tools/shared/snes-ppu.ts`). Verified two ways per resource,
both byte-exact structural invariants sourced from the game's own boot
code: compressed-stream end lands exactly on the next known boundary
(decompressor entry point / next resource start, zero gap), and
decompressed length matches the game's own DMA transfer-size register
(`$4345`/DAS4L-H) write exactly — see the DMA-register-as-oracle technique
in `verification-techniques.md`. Render of the confirmed resource is
unambiguous: the EA splash-screen logo (spinning-globe roundels + cursive
wordmark). Found via a DMA-register byte-pattern census (`STA
$420B`/`$4342`/`$4345` etc.) that locates graphics-loading call sites
cheaply without full disassembly — the same technique should crack
`sorcery`'s still-open Wizardry 6 SNES graphics format (that project
already has DMA-loader call sites found but no source pointer traced to a
confirmed image). Sourced/sharpened `r2-snes-flag-width-blind.md` (added
the concrete fix: write a small flag-aware linear 65816 disassembler
rather than hand-verifying byte-by-byte) and
`narrow-opcode-form-census-false-negative.md` (SNES direct-page vs
absolute hardware-register addressing as a second example of the same "one
addressing-mode census misses real hits" trap — the CGRAM/palette DMA
setup used direct-page `$21`/`$22` while the VRAM tile DMA setup a few
functions earlier used absolute `$2116`/`$4342`, so a census restricted to
one form found only half the loader).

**A `re-codebreaker` escalation then found the game's *actual* main
graphics system**, after a prior pass's "no resource table" conclusion
turned out to be caused by disassembling bank `$A8` with the wrong entry
index-width flag (see `flag-aware-disasm-entry-state-not-global.md`). The
splash-screen tag-byte codec above is used *only* by the splash screen — a
resource-ID dispatch does exist, just scoped per-subsystem rather than one
global catalog: a 24-bit far pointer held in DP `$20`/`$22`, resolved
through a self-referential "handle" convention (a named pointer's target
holds a pointer to itself+4; the real object starts there), indexed by
per-subsystem 4-byte-entry arrays (`resourceId*4` → far pointer). Real
tile/graphics resources use a **second, independent** LZSS compressor
(`$9F:EBD4`, classic Okumura-style, 2048-byte ring, distinct from the
splash codec) and store pixels as **chunky (linear-nibble) 4bpp**, not
SNES-planar — the game's own upload routine (`$80:835D`) converts to
planar at DMA time, so applying the standard planar decode directly to ROM
bytes produces a coherent-*looking* but wrong render (a strong instance of
`header-shape-ambiguous-pixel-encoding.md`; the discriminator was the
15-16% out-of-palette pixel rate the wrong decode leaves behind, 0.0 for
the right one). A tilemap descriptor + 2 payload codecs (raw, word-level
RLE) sit on top. Fully verified byte-exact (67/67 LZSS tilesets, 98/98
tilemap headers, 97/98 tileset links resolving) and shipped: 67 tilesets
(12,564 tiles) + 97 composed screens, `tools/urbanstrike/snes-gfx.ts` /
`snes-tilemap.ts` / `snes-lzss.ts`. Render oracle: a wood-panelled pool
room with a legibly-lettered "EDGE COLA" vending machine, a flight helmet,
an aerial city view. See `docs/urbanstrike/snes/data-structure.md`. Open:
sprite/OBJ graphics, scrolling level/mission-map data, text, and tilemap
encoding type `0x1E` (an indirection, target not chased) — `docs/urbanstrike/TODO.md`.

**The Mega Drive overlay-tile bank's "30 runtime-composed tileset slots"
mystery (§7.6 of `docs/strike-megadrive-tilemap.md`) also cracked further**
this session: the mechanism repointing `$FF4690` per scene is a flat `u32`
far-pointer table (Urban Strike file `0x0499E2`) indexed by a live
level/scene-id RAM variable (`$FF13E4`) — `lsl.w #2,d0; move.l
(a0,d0.w),$FF4690`. Each level's array mixes the already-known Strike-LZSS
(`cmd=6`, one shared/common slot reused by every level) with a **new,
previously-unidentified fourth Genesis codec** (`cmd=18`, "a fourth codec,
nested nibble-keyed jump table" per the doc's own long-standing TODO) that
covers most level-specific slots. Cracked by hand-decoding a linear-
disassembler-defeating `JMP d16(PC,Dn.W)`-into-a-branch-array construct
directly from a hexdump (see `game-re-tooling/genesis.md`) — the codec
itself is not an LZ/back-reference scheme at all: 8 persistent 32-bit
registers, refreshed one Genesis tile (32 bytes) at a time via 2-bit
per-half nibble-encoded refresh modes {unchanged / upper16 fresh / lower16
fresh / full32 fresh}, verified 129/129 byte-exact against real ROM
resource-descriptor size fields, now `tools/shared/strike-tile-delta.ts`.
**Record-to-level association and VRAM base-tile order then both solved
in one pass**, `tools/shared/megadrive-level-tileset.ts`: grouping the
overlay bank's 322 records by `tilesetSlot` (29 distinct nonzero values)
and checking, per group, which candidate level's composed-array slot
makes the *union* of every tile index the whole group references land as
exactly `[0, tileCount)` — a perfect `(maxUsed+1)/tileCount == 1.00`
fit — hits 1.00 for a unique level in **29/29** groups, assuming
cumulative sequential VRAM-tile allocation (slot N's base = sum of tile
counts of slots 0..N-1). Grouping many small fragments by a shared key and
checking the *union's* fit is far more discriminating than checking any
one fragment alone (single-record fits were ambiguous, multiple candidate
levels passed; the 29-record group fits were unambiguous). Only the real
CRAM palette for `cmd=18` resources remains open (escalated to
`re-codebreaker` after 3 distinct failed approaches — a borrowed static
palette, the descriptor's own field which mirrors its payload pointer for
this whole resource family, and a sibling per-level object-handle chain
that resolved through the project's own confirmed tilemap reader to a
*legible text render* that turned out to be colouring the tilemap
header's own struct bytes as fake CRAM data — see
`legible-text-render-weak-palette-oracle.md`) — `docs/strike-megadrive-
tilemap.md` §7.9, `docs/urbanstrike/TODO.md`.

**Urban Strike SNES gained two more confirmed findings** this session,
both self-driven (not escalated), applying the entry-state lesson above:
a plain, uncompressed, null-terminated ASCII text table (883 real
UI/mission/menu/character-bio strings, found by tracing the confirmed
`$20`/`$22` far-pointer convention to a text consumer then scanning for
printable-ASCII runs filtered by "contains a space, OR >=2 lowercase
letters, OR is an all-caps label >=4 chars" — zero manual tuning needed
beyond that one rule, `tools/urbanstrike/snes-text.ts`), and confirmation
that real SNES OAM/OBJ hardware sprites are used (found via a DMA-
channel-*target-register* census — `LDX #$04; STX $43N1`, i.e. "which
channel points at `$2104`/OAMDATA" — rather than by resource shape; the
544-byte transfer size matches the SNES's fixed, well-known OAM table
size exactly, 128 sprites x 4 bytes + 32-byte high table, a strong
hardware-constant cross-check for confirming a DMA transfer's *purpose*
once its target register is known). The 3 bank-`$A8` entry points an
earlier escalation had flagged as "sprite leads" turned out to be *more*
tilemap/palette infrastructure, not sprite-specific code — a reminder that
an escalation's own "still open, try these leads" pointers aren't
guaranteed correct and need re-verifying, same spirit as
`verify-escalation-artifacts-not-just-claims.md`. Sprite tile-graphics
data and the shadow-OAM populate logic remain open.
