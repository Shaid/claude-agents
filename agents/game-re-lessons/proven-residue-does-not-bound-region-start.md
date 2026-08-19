# Proving part of a trailing region is authoring residue does not tell you where the residue *begins*

**When it bites:** you've found genuinely decisive evidence that some of an
unexplained trailing region is stale authoring-buffer junk — a duplicated
copy of the file's own earlier content, a fragment of a *different* file's
data, a string that belongs to another asset — and you're about to write the
whole region off as residue and stop.

The evidence is real; the scope you're giving it is not. A fixed-size record
that the game reads whole (`read(fh, buf, 2500)`) can hold a genuine,
never-mentioned-in-your-notes structure *and* a tail of stale bytes past it,
and the stale part you happened to find first can sit hundreds or thousands
of bytes into the region. A positive finding at offset X bounds nothing about
`[regionStart, X)`.

Confirmed on Phantasie I (Amiga, `nicodemus` project): `out*.dat` files are
a fixed 2,500 bytes, of which offsets 0-994 were fully decoded (terrain grid,
POI record table, text block). The remaining 1,505 bytes were written up as
"residue, not structure" on genuinely strong evidence — `out1.dat` carries a
**near-duplicate of its own 400-byte text block** (357 of 400 bytes identical
to the live copy) at offset 2143, at an offset aligned to nothing. That
finding was correct. The conclusion drawn from it was wrong: disassembling
the loader showed offsets **1000 onward hold a real per-section map display
list** — `u16 backgroundIcon`, then `{u16 count; u16 iconIndex; count × {u16
x, u16 y}}` groups, `0xFFFF`-terminated — that parses cleanly in **18 of 18**
files, with every `y` inside 0-199 across 4,627 points. The duplicated text
block sat *after* that list's terminator, in the genuinely dead tail. Roughly
a third of the file had been filed as junk.

The tell was available in the data before the disassembly and was misread:
parts of the region read as plausible 16-bit coordinate pairs, which got
dismissed because values ran past 320 and word alignment looked inconsistent
across the *whole* region — an artifact of measuring alignment over a span
that included the real residue.

**What to do instead.** Treat "some of this is stale" as locating the
residue's *end* of the file, then work the boundary from the other
direction:

- Look for a **terminator-shaped structure** near the region's start, not
  its end. A self-terminating grammar that consumes a plausible prefix and
  stops in-bounds *in every file of the corpus* is decisive, and it costs one
  parser to test.
- **Measure structural properties per sub-range, not over the whole region.**
  Alignment, value ranges and entropy computed across a real structure plus
  its stale tail will look inconsistent no matter how clean the structure is.
- If a loader reads a **fixed-size record**, the read length tells you
  nothing about how much is meaningful — but it does guarantee that any
  structure inside it is addressed by a constant offset, which is a cheap
  thing to grep the disassembly for (`adda.w #0x3E8` gave the display list's
  base here).

Sibling lessons, reached from different symptoms:
`unbounded-appended-data-boundary.md` (unidentified data with no declared
end — where does it *stop*), `bootstrap-catalog-boundary-not-content-boundary.md`
(a verified catalog bound that is the wrong *kind* of bound). This one is the
inverse of both: a correct positive finding over-extended backwards into a
negative claim about bytes it never covered.

**The same over-extension happens at file scope, not just region scope**, and
does more damage there: residue found in a dead sub-region gets used to
classify the *whole file* as save state / non-canonical, when the regions the
reader actually consumes are untouched. See the "written by the game is not
playthrough-specific" section of `save-file-not-asset.md` — same `out*.dat`
format family, same dead gap, one game over.
