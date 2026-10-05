# A tilemap-rendered "substitution cipher" may be a duplicate alphabet at a different tile-code page, not a runtime transform

**When it bites:** a confirmed, working byte-substitution "cipher" recovers
real text for tilemap/font-ROM-rendered content (every letter offset by a
constant, a sentinel byte repurposed as space, a handful of punctuation
values at the top of the range) and the mechanism has not yet been traced
to the actual drawing routine's disassembly — especially if 1+ punctuation
byte values in the table were assigned by symmetry with an already-confirmed
sibling byte rather than a directly observed real occurrence.

## What went wrong

Black Tiger's (arcade, `kolbold`) NPC dialogue text was documented and
shipped as a "+1 letter-shift substitution cipher" — verified correct via
real English sentence decodes, so the *byte-to-glyph mapping* was genuinely
right. But the framing ("cipher") implied a CPU-side arithmetic transform,
and it wasn't one: disassembling the real Z80 text-drawing loop
(`maincpu 0x6946-0x696a`) found a single unmodified `LD (HL),A` — the raw
source byte is copied straight into tilemap RAM with zero arithmetic. The
"+1" was entirely a ROM-authoring choice: the font ROM contains a SECOND,
duplicate alphabet at a different tile-code "page" (selected by extra bits
stolen from a per-line attribute byte — `tileCode = rawByte +
((attr & 0xe0) << 3)`, i.e. a page number from attribute bits, not from the
text bytes), laid out one tile-column later than the ordinary page-0
plain-ASCII alphabet the game's HUD/UI text draws at `tileCode == rawByte`
with no offset. From the decoded-text side alone, "every raw byte here maps
to a differently-valued real character" is indistinguishable between "a
runtime cipher" and "a raw copy into a ROM page that happens to store a
shifted alphabet" — only tracing the drawing code (or rendering the
candidate ROM page directly) tells them apart.

This distinction wasn't just semantic. Two punctuation-cluster byte values
had been assigned by **symmetry** with an already-confirmed sibling byte
(same relative position in the arithmetic table, mirrored across the
uppercase/lowercase ranges) rather than from a directly observed real
occurrence, and both were wrong: `0x5a` was assumed to be a space (by
symmetry with a confirmed lowercase-range space sentinel at the equivalent
offset) but the real font-ROM tile at its true page is a period — confirmed
across 10 independent real occurrences, all landing as grammatically
perfect sentence-ending periods, including one real 3-consecutive-byte
ellipsis. `0x7d` was assumed to be a period but the real tile is a dash.
Rendering the actual confirmed ROM tiles at the correct page (not
extrapolating the arithmetic pattern by symmetry) settled both immediately
and found one more real mapping (`0x5c` -> forward slash) a prior pass had
left unmapped with zero observed occurrences.

## The fix

1. Before calling a tilemap/font-rendered byte transform a "cipher," check
   whether the actual drawing code applies any transform at all. A plain
   unmodified byte-to-tilecode copy plus a ROM authored with 2+ alphabets
   at different pages/banks is a structurally different (and much cheaper
   to fully resolve) mechanism than a real runtime substitution.
2. Treat a punctuation/space byte assigned "by symmetry with an already-
   confirmed sibling byte" as exactly as unconfirmed as one inferred purely
   from arithmetic continuation — symmetry is a hypothesis, not evidence,
   even when it "must" be true by the pattern's own internal logic.
3. When the byte in question has zero real observed occurrences in the
   extracted text corpus (so waiting for a confirming sentence isn't
   possible), render the actual candidate ROM tile directly and read the
   glyph — this settles the value even for a byte the game's shipped text
   never actually uses.
