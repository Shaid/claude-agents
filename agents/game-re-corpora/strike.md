# strike — Desert/Jungle/Urban Strike (Amiga OCS/AGA + Genesis + SNES)

**Project root:** `~/Development/strike`

Two Amiga compressors across sub-eras (LR88/PowerPacker on AGA; RNC1 + nested RNC2 on OCS, `tools/shared/{lr88,rnc1}.ts`) and two Genesis codecs (Strike LZSS, plus a second RLE found by tracing the LZSS decompressor's own caller dispatch). Sourced `round-looking-longwords-are-centred-bitmap-rows.md`, `jump-table-noop-means-handled-elsewhere.md`, `shared-scratch-copper-list-palette-patch.md` (Jungle Strike AGA's `status`/`brief`/`menubgd`/`menubgd2` screens patch a shared scratch copper list at runtime instead of using one static list each — cracked by tracing each screen's own load call site to its patch-table source, not by scanning for copper-list shapes; `status` confirmed via quantified reference-screenshot match). See `docs/junglestrike/`, `docs/desertstrike/`

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
one form found only half the loader). See
`docs/urbanstrike/snes/data-structure.md` and `docs/urbanstrike/TODO.md`
for open items (general resource table not found — only 2 resources
decoded from one literal call site; tilemap/level format; SPC700 driver
itself untraced).
