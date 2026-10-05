# sorcery — Wizardry 6: Bane of the Cosmic Forge (Sir-Tech; DOS/EGA, Amiga, SNES ports)

**Project root:** `~/Development/sorcery`

## DOS/EGA (`docs/wizardry6/dosega/`) — the original source platform

Confirmed to be the platform the Amiga port was built from (not just a
sibling port): the Amiga executable's embedded filename tables predicted
DOS's exact `.EGA`/`.CGA`/`.T16` platform-variant naming before the DOS
corpus was ever seen, and the Amiga's 16-colour EGA-family palette order
(previously assumed to be an Amiga-side re-permutation) renders *better*
than the standard EGA hardware DAC order on DOS's own `.ega` screens —
i.e. that palette order is the original game-authored one, not a port
artifact. Every same-sized `.hdr`/`.dbs` file between the two ports turned
out to be the exact same record layout with every multi-byte field simply
the other endianness (LE on DOS, BE on Amiga) — see
`endian-swap-needs-matching-field-width.md`, sourced from this session:
`misc.hdr` (Huffman tree, 98.9% node-identical — the small remainder is a
genuinely different but equivalent tree, not a bug), `master.hdr`/
`disk.hdr` (100% exact-value match), `scenario.hdr`, `pcfile.dbs`,
`scenario.dbs` (class-XP tables, item catalog, monster catalog — including
the `picFileIndex` `.pic`-file-selector field), `msg.hdr`/`msg.dbs` Huffman
text. `.EGA` full screens and `wfont`/`wport` files are byte-identical (or
99%+) to Amiga outright — pure bitmap data has no endianness to convert.
`mazedata.ega`'s directory record is 1 byte/record narrower than Amiga's
(offset field dropped entirely, reconstructed as a cumulative sum instead)
— sourced `implicit-cumulative-directory-offsets.md`. The one format that
isn't a simple port of the Amiga container: `.pic` sprites are wrapped in
an in-house block-oriented byte RLE (4096-byte blocks, no cross-block
tokens) around the *exact same* tile payload as Amiga — solved via a
`re-codebreaker` escalation after two failed raw-struct-read hypotheses,
verified byte-exact (712 cels, 3.4M pixels, zero deviation) against the
Amiga corpus as oracle; sourced `byte-scan-tag-byte-vs-wrong-stride.md`'s
"compressed-stream variant" addendum. New-to-this-project binary family:
MS-DOS 16-bit real-mode MZ executable (`wroot.exe`) + hand-rolled `.ovr`
overlay files — see `game-re-tooling/dos.md`. The CS/DS segment-resolution
gap hit while first tracing the overlay loader is **resolved**: `DS = CS +
0x0fd8` paragraphs, found by following the one MZ-relocation-patched
register forward to a later `mov ds, <reg>` in the small-model C startup
stub and verified against a legible string at the computed file offset —
this unblocked a full trace of the overlay-load state machine (a shared
`curState` global read by both the main exe's dispatcher and every loaded
overlay's own entry code, two dispatch levels deep) and corrected the
`.ovr` file header from an assumed 8 bytes to the real 14, with a
byte-exact `fileSize == 14 + sizeA + sizeB` invariant across all 11 files.
Also sourced `string-scan-crosses-structural-boundary.md` (a whole-file
string scan produced a phantom `"QMON00.PIC"` by gluing a trampoline
instruction's trailing operand byte to the start of an unrelated real
string). See `docs/wizardry6/dosega/data-structure.md` §6 and
`docs/wizardry6/TODO.md` for the up-to-date open-item list (remaining:
individual overlays' internal rendering/game-logic bodies beyond their
entry dispatch; a race-attribute table found inside `wpcmk.ovr`/
`wpcvw.ovr`'s shared data block, row semantics not fully closed).

**`.CGA`/`.T16` platform-variant graphics (solved, no escalation needed):**
every `.ega` full-screen/`mazedata`/`wfont`/`wport` asset ships `.cga`
(CGA, 2bpp) and `.t16` (Tandy 16-color, 4bpp) siblings. File-size
arithmetic alone (`.cga` = half of `.ega`, `.t16` = same size) only
constrains total bytes, not layout: unlike every planar/bitplane format
elsewhere in this whole corpus (Amiga and DOS `.ega` alike), all of
`.cga`/`.t16` turned out to be **packed-pixel (chunky)**, not planar — see
`header-shape-ambiguous-pixel-encoding.md`'s new 4th case. `.CGA` full
screens additionally needed real CGA hardware video-memory bank layout
(fixed 0x2000-byte even/odd-field banks, not a tight-packed guess) — see
`game-re-tooling/dos.md`'s new CGA/Tandy section — found by disassembling
`cga.drv`'s screen-blit routine. Both formats' palettes were confirmed via
`wroot.exe`'s own `INT 10h` BIOS video calls, not pixel guesswork: CGA via
`AH=0Bh` "select 4-color palette" (BH=01h BL=01h -> cyan/magenta/white
family), Tandy via `AH=10h AL=02h` "Set All Palette Registers" whose
embedded 17-byte register table reproduces the already-confirmed EGA
`PIC_PALETTE` permutation exactly — i.e. Tandy 16-color mode uses the
*same* palette table as EGA/Amiga. See `docs/wizardry6/dosega/
data-structure.md` §9 for the full writeup, `tools/shared/packed-pixel.ts`
for the reusable chunky-pixel decode primitives (the packed-pixel
counterpart to `tools/shared/amiga-planar.ts`).

## Amiga (`docs/wizardry6/amiga/`)

Genuinely from-scratch corpus — no prior art exists anywhere for this port. Plain AmigaOS hunk exe, SAS/C small-data (`A4 = DATA_start + 0x7FFE`). Solved: a Huffman bit-tree text decompressor whose 256-node table is a standalone 1024-byte file; `.EGA` full-screen images and `.PIC` cels (plane-major 4bpp, one shared 16-colour palette for the whole binary; `.PIC` cel tiles use a tile-presence bitmask and are tightly packed, but the 320x200 full-screen `.EGA` format pads *each* of its 4 bitplanes to a fixed 8192-byte slot rather than packing them tight at 8000 bytes — got this wrong for two passes, fixed by brute-force per-plane offset search against the DOS release's already-clean `.t16` sibling encoding as ground truth, see `planar-plane-padding-vs-tight-stride.md`); `mazedata.ega` dungeon-view art bank plus its full `DrawMazePiece` compose-list consumer/call-graph; the `master.hdr`/`disk.hdr` section-boundary system over `scenario.dbs` (XP/item/monster tables); `msg.dbs` paged message store; **the per-level dungeon maze geometry itself** — `scenario.dbs` section 2 (14 levels, 12 fixed 8x8-cell regions/level placed via an origin table, LSB-first 2-bit-packed wall planes read through the game's own `GetBitField` A4-primitive) plus its companion section-3 per-level entity table (structure only). Verified byte-exact against the DOS/EGA release's own `scenario.dbs` and against `newgame.dbs`'s initial-state template. Sourced `verify-escalation-artifacts-not-just-claims.md`, `compressed-stream-start-offset.md`, much of `header-shape-ambiguous-pixel-encoding.md`, `sibling-functions-outside-callgraph-scope.md`, and `domain-refuted-by-shape-not-values.md` (a session had *correctly* traced this exact `scenario.dbs` section's allocator/access-pattern/field-offsets and still misidentified its domain as character-creation UI data rather than maze levels — the escalation that found the real answer is the source of both new lessons). Techniques worth reusing: resolving PC-relative `LEA`/`PEA` targets against known filename-string addresses to find a loader cheaply, gap-histogramming name-like strings to recover a record stride, and — when a caller/callee trace from a confirmed dispatcher dead-ends — censusing the *parent* function's full sibling-call list (function-prologue scan across the containing address range) rather than re-trying the same dispatcher's own graph. **Tooling state (as of the coverage-gap fix session):** `docs/wizardry6/amiga/disasm/Bane.cnf` used to declare `CODE` for only ~1.5% of the 351,292-byte CODE hunk (a stale `-preproc` artifact, silently trusted across 2 sessions — see `committed-ira-asm-silent-coverage-gap.md`, sourced from this project); fixed by extending the `.cnf`'s `CODE` range to cover the whole hunk and regenerating, now at 99.47% declared-code coverage. `Bane.asm` is now a genuinely useful greppable search surface across nearly the whole binary — prefer grepping it before a fresh radare2/capstone pass. See `docs/wizardry6/amiga/` and its `investigations/`.

**Later session (all 5 then-open Amiga TODO items worked; 2 fully closed, 3 materially advanced):** the monster catalog's HP/stamina/alignment question — stuck across 10 documented disassembly-only negatives spanning multiple sessions — was finally cracked by a `re-codebreaker` escalation via a published fan bestiary claiming internal-data-table provenance (zimlab.com's Wizardry VI walkthrough), the first use of this oracle class in the corpus; sourced `published-walkthrough-numeric-oracle.md`. HP is `+0x78` (the field previously mislabelled "damage dice #1"), stamina is `+0x7c`, "number appearing" is `+0x74` (not attacks-per-round), gender is `+0xd6`; alignment is refuted as nonexistent (Wizardry 6 dropped the Good/Neutral/Evil system entirely — confirmed via a full 642-message sequential `msg.dbs` re-decode finding no alignment enumeration anywhere). Also fixed an off-by-one on the resistance array (`+0x95`, not `+0x94` — `+0x94` is a reserved slot-zero coinciding with a `PEA 148(A0)` pointer-base instruction; sourced an addendum to `reserved-slot-zero-shifts-extractor-index.md`) and resolved the full AC block (`+0xbe`-`+0xc5`, overall + 7 body-part slots). `item-catalog-remaining-fields` fully closed (3 consumer-less bytes confirmed genuinely unused, via a checklist of "is there any code module/overlay/buffer outside the CODE hunk that could read this" — this Amiga port has exactly one executable and no overlay files, unlike the DOS port). `scenario.dbs` sections 6/7/8 all now confirmed (section 6 = a scripted event/opcode table whose records are callable sub-scripts via self-recursion; section 7 corrected from "monster encounter table" to a weighted treasure/reward table that references the *item* catalog, not the monster catalog — only section 5 remains open). `pcfile.dbs`'s character-record field map materially advanced (~30 of 432 bytes now confirmed/rendered, up from 3) via per-consumer-function tracing rather than a universal regex census, after a prior session's scripted census attempt failed on addressing-shape variance. See `docs/wizardry6/amiga/data-structure.md` and `docs/wizardry6/TODO.md` for current status — `TODO.md` items narrowed this session: `monster-stat-block` (HP/alignment solved, some sub-record fields still open), `pcfile-character-fields` (still open, large spans remain), `scenario-sections-5-6-7-8` (narrowed to section 5 only), `maze-plane-semantics` (re-confirmed as correctly deferred to the walker's own M3 pass, no change).

## SNES / Super Famicom (`docs/wizardry6/snes/`)

Japan-only 1995 ASCII Corp release, 3 MB LoROM+FastROM cart, 65816 CPU —
unrelated toolchain to the Amiga port (no shared code/format), useful only
as a *game-content* oracle (class roster, monster list). No public
disassembly/romhacking project exists for this release. `tools/shared/
snes-ppu.ts` (4bpp/2bpp tile decode + BGR555 palette, ported from `strike`)
and `tools/shared/snes-lzss.ts` (this project's first LZSS codec, new this
session — general 2 KB-window LZSS, 22 confirmed call sites, may be worth
checking against other SNES-era games in this corpus family if a similarly
shaped codec turns up) are the shared decode primitives. Confirmed: ROM
header/vectors; RESET boot through a **cooperative round-robin task
scheduler** (10 fixed task slots, `TCS`+`RTS` resume / `TSC`+`RTS` yield
primitives — see `game-re-tooling/snes.md`'s new section — this closes
the long-standing "where does per-frame game logic run" question: NMI
resumes each task once/frame, there is no separate main loop); SPC700
upload handshake + driver source address (textbook `$BBAA`/`$CC` IPL
protocol); a 98-string class-tier title table matching the Amiga corpus's
14-class roster exactly; a 102-entry monster-name table decoded via
half-width katakana (see `game-re-tooling/snes.md`), found *because* the
ROM unexpectedly retains plain-English internal name strings paired with
their localized translations (the Rosetta-stone-oracle technique in
`verification-techniques.md`); a 36-entry monster/NPC face-portrait bank
plus its full CGRAM palette (per-pair groups from one shared colour
table); a 405-tile UI icon bank plus its own palette (a sibling entry
point into the *same* palette-copy routine, 4 bytes past the portrait
bank's own entry, confirmed by cross-checking the generic CGRAM-DMA
dispatch table's fields against the call sites' own register operands);
the full **opening/title sequence** — publisher logo and copyright screen
both verified by rendering to fully legible text/wordmark, plus a title
backdrop+lightning overlay (rendered, structurally coherent); and the
**256-glyph dialogue font** (2bpp, uncompressed, renders as a complete
digit/A-Z/hiragana/katakana/symbol set). All of the LZSS-compressed finds
(opening sequence, font's DMA path, and a 139-record spell/combat
special-effect animation bank — see below) came from one `re-codebreaker`
escalation; both `MVN`-based (uncompressed) and LZSS-based (compressed)
resource families now have proven cracking techniques on this ROM (see
`game-re-tooling/snes.md`'s "Finding a graphics loader without a DMA
register census" section for the `MVN` technique).

**Correction worth flagging for any future session touching this ROM**: a
region previously tracked across 2 sessions as a strong dungeon-corridor-
art/maze-geometry lead (a dense 2-byte `[tag][id]`-shaped record region,
cross-referenced by a long-addressing-instruction census) is **not** maze
data — a second `re-codebreaker` escalation traced its real consumer
(`DBR`-relative indexed addressing, invisible to the long-addressing
census that found it — see `indexed-table-base-below-valid-rom-window.md`,
new this session) and confirmed it's the **spell/combat special-effect
animation bank**: 139 records, ROM banks `$32`-`$3F`, LZSS graphics + a
frame-table (SNES BG tilemap cells for "mode A" records, flat uniform-fill
frames for "mode B"). The `[tag][id]` bytes were really the high/low bytes
of ordinary SNES tilemap words, not a category/id record scheme. **The
dungeon/maze-geometry art question is open again** — this was the
strongest lead for it and it's now something else entirely; no
replacement lead exists as of this session. Also sourced
`nearest-preceding-immediate-is-not-dataflow.md` (a DMA-size census
heuristic's false ~35KB "candidate title-screen transfers", refuted by
hand-disassembly) and an addendum to
`autocorrelation-period-is-the-scanline-stride.md` (the comb-striping
artifact that first flagged the mis-identified region as "not pixel
data" was correct — it just wasn't maze data either). A file-offset↔CPU-
address bank-rollover error (file offset `>= 0x8000` isn't bank `$00`)
was caught and fixed, inherited across 2 prior sessions — see
`game-re-tooling/snes.md`'s new bullet on this.

**Major sweep session (2026-08-16, re-oracle):** 7 of the then-16 TODO
rows closed, 8 narrowed, in one Fable session across both Amiga and SNES.
Highlights: the SNES first-person **view walk fully traced and shipped**
(`$80:C69F`: 26 frustum slots, visibility-propagation skip flags, art
dispatch through `$80:DE4E`, floor/ceiling `$80:DED8` tables — verified by
dual independent ports, Python vs. TS, word-identical over real poses),
which **confirmed the cross-platform wall-value semantics** (0=open,
1=open doorway, 2=solid wall, 3=closed door) both maze rows had carried as
a shared unknown; the Amiga **deferred-draw queue decoded** (12-byte
records, descending-depth consumer) along with `0x9b58`'s complete
per-code dispatch and both checkerboard parities, all implemented
(298,744-pose sweep, 0 exceptions); the flagP/flagQ per-level overlay
dispatches decoded (fog cells, open sky, pits, alt floors); monster
per-attack 16-byte sub-records solved field-for-field against the Zimlab
bestiary; the full SNES 8-bit text encoding solved (ASCII + JIS X 0201
half-width katakana + a custom hiragana page with trailing dakuten
combining); the SPC sound system's real directory found (151-module
far-pointer table at `$A0:8000` — the prior "driver blob at `0xF0919`"
premise was wrong, that's the 37-song module-set table); spell-animation
palette closed (mode-A tilemap words carry live per-cell BG sub-palette
fields; sourced `tilemap-word-assets-carry-own-palette-field.md`);
scenario.dbs section 5 solved (NPC name table spliced at `'^'`
placeholders). Also sourced the 68k brief-extension-word addendum to
`addressing-mode-operand-hides-implicit-index-offset.md` and the
decimal-vs-hex `A4`-displacement caveat in `game-re-tooling/amiga.md`.

**Still open** (see `docs/wizardry6/TODO.md` for the authoritative list):
the 16-bit script-token → kanji-glyph mapping (four linear-layout probes
refuted), per-region SNES art-variant/palette runtime gating, the Amiga
deferred queue's `.PIC` cel-token draws, pcfile field spans, a handful of
monster/maze residual bytes, and the two DOS/EGA rows.
See `docs/wizardry6/snes/data-structure.md`,
`docs/wizardry6/amiga/data-structure.md` and `docs/wizardry6/TODO.md`.
