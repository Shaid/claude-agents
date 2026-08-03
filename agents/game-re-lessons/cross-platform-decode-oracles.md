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

**Cheap structural proof a differently-grouped container is the same asset
catalog:** when a port reorganizes N files into M files (different filenames,
different counts, no obvious 1:1 mapping), diff the *resource-ID sets*
(not filenames) across the two ports' combined file lists. A 100% (or
near-100%) ID overlap is strong, cheap evidence the two releases share one
underlying catalog before any pixel-level decoding — confirmed for WIME's
DOS EGA release (3 files) vs DOS VGA (7 files): 110/110 `GAMI` IDs and 19/19
`LMRF` IDs matched exactly, settling the container-mapping question in one
script run instead of guessing from file sizes/counts.
