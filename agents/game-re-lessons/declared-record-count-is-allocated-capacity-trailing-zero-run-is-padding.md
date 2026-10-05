# A per-instance "count" field can be an allocated-capacity value, not a real-content length — a trailing run of fully-zero records is padding, and consuming it literally corrupts derived aggregates, not just individual pixels

**When it bites:** decoding a variable-length record array whose length
comes from an in-band `count`/`tileCount`/`numEntries` field, where a
small, structurally-clean render/decode still produces implausible mass
("100% black", "way too many entries", "content that doesn't fit its own
declared area") — especially when a downstream step also derives an
*aggregate* from the same array (a bounding box, a total, a centroid),
which the padding can corrupt even more visibly than the padding records
themselves.

## What happened

Parasite Eve (PSX, `~/Development/parasite`)'s tile-scatter background
compositor reads each camera trigger's own `tileCount` field and decodes
exactly that many 12-byte tile-placement/texture records. A pixel census
found 6 of 509 shipped room composites were **100% solid black** — not
just dark, completely blank-looking. Per-tile diagnostics showed the
mechanism precisely: for the affected triggers, a large trailing slice of
the tile array (up to 87.5% of the declared `tileCount`) consisted of
**fully zero 12-byte records** (`wordA===0 && wordB0===0 && wordB1===0` —
placement x/y, ordering index, texpage, CLUT id, and UV all zero at once,
not just one suspicious field). A corpus-wide census (306,620 tile
records, 2,078 active triggers) confirmed every such all-zero record sat
in an unbroken run ending at `tileCount - 1`, with zero exceptions —
i.e. `tileCount` is really an *allocated capacity*, and real content only
occupies a variable-length prefix of it.

Left unfiltered, this had **two compounding effects**, not one: every
placeholder record painted a real, opaque, pure-black 16x16 tile at
position `(x=0, y=0)` (since a zero record decodes to `clut=0`, which
always samples an un-uploaded, always-zero VRAM address) — but it also
fed `(0,0)` into the room's **bounding-box computation**, dragging
`minX`/`minY` down to 0 regardless of where the real content actually
was. The result was a canvas inflated far beyond the real content's
extent, mostly filled with fake painted black. Fixing only the pixel-level
symptom (e.g. skipping zero-record pixels during paint) without also
excluding them from the bbox calculation would have left the canvas
wrongly sized.

## The fix

Filter fully-zero records out of the array *before* any downstream
aggregate is computed from it, not just before painting:

```js
if (wordA === 0 && wordB0 === 0 && wordB1 === 0) continue; // trailing padding
```

Before shipping this as more than a hunch, run the exhaustive corpus-wide
check that makes it safe: confirm every zero record is part of an
unbroken *trailing* run (never followed by a non-zero record) across the
whole corpus, not just the file(s) that motivated the investigation. A
single counterexample would mean the field encodes something else (a
legitimate "blank" tile, a sentinel with real meaning) rather than unused
capacity.

## The generalizable lesson

When a declared count field's records include some that are entirely
degenerate (every sub-field zero, not just one), don't assume the count is
wrong or the format needs a different field — check whether it's an
allocated-capacity value with trailing padding, the same convention this
project's own model format already used for its `boneCount+1` placeholder
bone record (see `genuine-off-by-one-loop-matches-placeholder-record-convention.md`
for the mirror-image case, where the "+1" was real and had to be kept).
And when fixing it, audit every place the raw (unfiltered) array feeds a
*computed* value — a bounding box, a sum, a centroid, a min/max — not just
the places that render individual elements; padding that would be
harmless on its own (an inert, invisible extra tile) can still corrupt an
aggregate built from the whole array.
