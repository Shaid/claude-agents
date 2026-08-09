# Cross-platform ports are decode oracles — for code too, not just data

**When it bites:** stuck cracking a data format, or stuck tracing a routine's
caller in disassembly with no symbols — or a known-content byte search
against a target platform's executable comes back with only noise-level
(4-6 byte) matches for a table you have strong reason to believe is shared
verbatim.

**Check the target executable for compression before concluding the search
failed or the data isn't there.** A byte-identical search using another
platform's confirmed table content as the oracle only works against the
*executable's real bytes* — if the target binary is itself compressed
(LZEXE, or any codec `game-re-tooling/compression.md` covers), the on-disk
bytes are a transform of the real content, not the content itself, and a
literal search will find nothing even when the tables really are shared
byte-for-byte after decompression. Confirmed on Vengeance of Excalibur's DOS
VGA `game.exe`/`vex.exe`: an initial search for the Amiga executable's
confirmed remap/terrain tables found nothing (LZEXE v0.91-compressed, `LZ91`
tag at file+0x1c); decompressing first (`tools/shared/lzexe.ts`, a TypeScript
port of `unlzexe.c` verified byte-exact against the reference C tool) and
re-running the identical search found all three tables byte-identical, zero
transformation needed. Cheap check before assuming the search methodology or
the cross-platform-sharing hypothesis is wrong: does the executable have a
compression-tool magic/signature anywhere, and does a generic decompressor
(`ancient`, `unlzexe`, or this project's own `tools/shared/lzexe.ts`) accept
it? Note the ceiling on this technique, though — it only rescues *flat data*;
VM bytecode/scripted-behavior tables can still be structurally impossible to
byte-match even after decompression, if the format embeds platform-specific
code addresses inline (see `vm-bytecode-embeds-platform-addresses.md`).

Same-game DOS/Windows data often has identical structure with different
endianness or no compression at all — Black Crypt's `bcdfs` (Amiga) vs
`maindung.gam` (DOS); WIME's DOS `GAMI` mirrors Amiga `IMAG`. Decode the easy
platform first, then map back.

Extends to **code**: if a reference disassembly exists for another
platform's build of the same game, byte-pattern-search the target binary for
that routine's own immediate operands (`MOVE.L #imm,Dn` constants are often
near-unique) to find the equivalent routine directly — this sidesteps a
stuck caller-tracing problem entirely. Cracked FE2's savegame cipher this way
after a linear-disassembly caller search had failed.

**Scaled-up version: map an entire subsystem in one pass with a sliding-
window anchor index, not one routine at a time.** When both platforms share
one compiled source (common for a small studio's in-house engine shipped on
two 68k platforms, e.g. Amiga+Atari ST) and you already have one platform's
binary fully confirmed, build an index of short (~8-byte) sliding windows
from the confirmed binary — filtered to reject low-complexity/repetitive
windows (fewer than ~4 distinct byte values; otherwise runs of zeros/0xFF
swamp the index with noise) — then scan the *other* binary for exact window
matches and cluster the resulting `(targetOffset - sourceOffset)` deltas per
source region. A dominant cluster at one delta reliably marks the
corresponding routine in the target binary, even when the two binaries
differ substantially in overall size/layout and different subsystems
cluster at *different* deltas within the same binary pair (shared math/
render code at one relocation offset, a later-linked subsystem at another).
This finds an entire family of routines — including ones you didn't already
have a specific operand to search for — in one indexing pass, considerably
cheaper than disassembling the second binary standalone. Confirmed on
Hunter (Amiga vs Atari ST, both loading at base `$800`): mapped 8+ confirmed
Amiga routines (a full 3D-object rendering subsystem: scan/setup/transform/
bbox/edge-build/polygon-fill/line-draw/matrix-build, plus the per-object
dispatcher) onto the Atari ST binary this way, several with full 16-byte
exact-byte-run confirmation, and it also surfaced a previously-unfound
header-field consumer routine that a same-binary-only search had missed
(see `negative-from-addressing-root-not-shapes.md` for that half of the
story). Caveat: this only finds *shared* code — platform-specific I/O
(disk loaders, sound drivers) won't have a match to anchor off, since it's
independently written per platform even when the game logic is shared.

**A sibling platform's structurally different but already-clean encoding of
the *same artwork* is a byte-exact pixel oracle, not just a shape check.**
When a game ships the same asset in two unrelated pixel encodings (e.g. an
Amiga/DOS `.EGA` planar bitplane file next to a DOS `.T16`/Tandy
packed-chunky file of the same scene), and one of the two is already
confirmed clean, don't just eyeball the suspect decode's shape against it —
decode the clean one to get a true pixel-index grid, then brute-force search
*each independent structural unit* (each bitplane, each field, each record)
of the suspect file for the byte offset that best reproduces the
corresponding truth values. Searching per-unit rather than only per
whole-buffer offset can reveal that a "single global offset" bug is
actually N per-unit offsets forming an arithmetic progression — exactly what
happened cracking Wizardry 6's `.EGA` full-screen stride bug (see
`planar-plane-padding-vs-tight-stride.md`): a per-bitplane search against
the `.t16` sibling's ground truth found 4 independent 100.000000%-match
offsets in one pass, which a single whole-image offset scan would only ever
have partially compensated for.

**A "does the reference need remapping through an unknown table" worry is
often answered for free by checking whether the target embeds the source
asset verbatim.** Before assuming a cross-platform offset-style reference
(a byte offset into a string block, a table index) needs a semantic remap
because the two platforms' internal asset layouts might differ, check
whether the target's own binary contains an exact copy of the source's
raw asset bytes at some fixed location — a couple of `bytes.find()` calls
against known content plus a relative-offset cross-check (does a second,
different string sit the same distance from the first as it does in the
source?) settles it. Confirmed on Black Crypt: DOS `crypt.exe` embeds the
Amiga `bcdft` item-name string block byte-for-byte at file offset
`0x37A28` — same strings, same relative offsets — so the on-disk name
reference word needed no remap at all beyond the ordinary endian swap
already applied to every other word field in its record. If no such
verbatim copy exists, *then* the remap-table concern is real and worth the
tracing effort.

**A byte-value frequency histogram matched against a sibling platform's
already-confirmed dominant values is a cheap identity oracle, not just a
dimension check.** Before guessing at a resource's dimensions or format by
brute-force (see `tile-grid-dimension-needs-render-not-just-bytecount.md`),
histogram its decoded bytes and compare the top few values' frequencies
against an already-solved sibling platform's equivalent resource — a close
match (not just "same top value" but similar *percentages*) is strong,
free evidence the two resources are the *same underlying content*,
repackaged with different dimensions/padding, before any pixel-level or
grid-shape work. Confirmed decoding War in Middle Earth's Apple IIGS
`PAMM` (a terrain-map resource in a battle-scene file with no obvious
connection to the world map): its decoded bytes were 40.3% the value
`0x21` and 22.0% `0x00`, matching Amiga's already-confirmed world-terrain
`MMAP` almost exactly (~41% plains, water second) — which correctly
predicted `PAMM` was the *same* world terrain grid (160 columns wide, same
byte-to-terrain-class encoding) before any dimension-guessing was needed,
and a direct cell-by-cell diff against the Amiga corpus's own rendered
map then confirmed it at 99.7%.

**A sibling *game* by the same developer can be a decode oracle too — not
just a sibling platform port of the same title.** The pattern in this file
mostly assumes "port A" and "port B" are the same game; it applies just as
well across two different titles from the same studio/era if their
container formats share even partial magic-string naming, since studios
routinely reuse an in-house codec across a franchise without changing its
tag. Confirmed on tri-Ace's Valkyrie Profile (PSX, 1999) and Valkyrie
Profile 2: Silmeria (PS2, 2006), both in the same project (`valkyrie`):
VP1's session reverse-engineered a `"SLZ"+subtypeByte`-tagged LZSS
container from `SLUS_011.56`'s disassembly; a *separate*, earlier VP2
session had independently found VP2's TOC wraps sub-records tagged
`"SL"+typeChar('Z'/'E')+versionByte` and had exhausted zlib, LZMA,
`ancient identify`, and a ~480-combination parametric LZSS brute force
against a real `type='E'` sample with zero success. Running VP1's
unmodified decoder against real VP2 bytes tagged `type='Z'` (the same
3-letter "SLZ" root, just wrapped in a differently-shaped 4-byte header)
succeeded byte-exactly on 4/4 samples — recovering a valid ELF module and
readable library-version strings — with **zero code changes**. The
sibling `type='E'` ("SLE") tag, despite sharing the outer header shape,
turned out to be a genuinely different, still-unsolved codec — so this
technique narrows the search, it doesn't guarantee every same-prefix tag
in the sibling game shares the codec; verify each tag family
independently rather than assuming the whole family transfers. Before
spending disassembly time on a blocked compression/container format,
check whether *any* sibling game in the same project — not just other
platform ports of the same title — has already solved something with
overlapping magic-string naming.

**Cheap structural proof a differently-grouped container is the same asset
catalog:** when a port reorganizes N files into M files (different filenames,
different counts, no obvious 1:1 mapping), diff the *resource-ID sets*
(not filenames) across the two ports' combined file lists. A 100% (or
near-100%) ID overlap is strong, cheap evidence the two releases share one
underlying catalog before any pixel-level decoding — confirmed for WIME's
DOS EGA release (3 files) vs DOS VGA (7 files): 110/110 `GAMI` IDs and 19/19
`LMRF` IDs matched exactly, settling the container-mapping question in one
script run instead of guessing from file sizes/counts.
