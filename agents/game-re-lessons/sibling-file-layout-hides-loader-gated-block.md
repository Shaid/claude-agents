# A layout confirmed on one sibling file can hide a loader-gated block in the others

**When it bites:** a family of per-level/per-map files shares a layout like
"header, stream, block A, then B to EOF", confirmed on one or a few files by
a strong oracle (byte-match, clean tiling). Nothing in the files signals extra
content, so "B to EOF" is applied to every sibling.

The loader can read an extra block for **only some** files, gated by a table
in the *executable* (per-level flag/size words). No magic, length field or
header bit in the data shows it. The extra bytes are absorbed into the
"to EOF" region, and if that region is permissive (PCM audio, raw bytes,
padding) nothing looks wrong — an oracle that matches samples deeper in the
region still passes.

## Check / fix

1. Find the loader and list its read calls in order, with the size source
   for each: constant, header field, or an indexed table in the executable.
2. For **every** sibling, require `file length == sum of the reads`,
   byte-exact. Don't stop at the file the oracle confirmed.
3. Dump any per-file size/gate table the reads index. A gate that is
   non-zero for a subset of files means those files carry an extra block —
   locate it from the schedule, not by eyeballing the data.

Distinct from `discriminant-gated-field-convention-applied-unconditionally.md`
(gate is a field *in the file*) and
`block-chain-walk-stops-at-unknown-sibling-block-magic.md` (blocks carry
magics); here the data carries no marker at all.

## Canonical example

Black Crypt (Amiga) per-level files `bcdfb`-`bcdfn`. "1,932 B wall
decorations, then PCM sound bank to EOF" was confirmed byte-exact against the
DOS port's sound samples on the first file. The level loader actually reads
header -> RLE stream -> 1,932 B -> **if gate[level] != 0**: a 4,320 B panel
body + 112 B descriptors + gate[level] B of inset pixels -> sfx[level] B. The
gate was non-zero for 6 of 13 files, so those six "sound banks" began with
~4.5 KB of panel art. Schedule accounting closed 13/13 files byte-exact and
recovered six special-panel images the DOS port names but never shipped.

**History:** 1 instance (crawl / Black Crypt Amiga, 2026-11-13).
