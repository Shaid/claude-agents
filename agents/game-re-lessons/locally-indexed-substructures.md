# Sub-structure indices can be locally-scoped per-item OR one flat corpus-wide pool — don't assume either direction

**When it bites:** a multi-part format's element indices either (a) look
small enough that "one shared pool" seems necessary but resolving against
it produces garbage, OR (b) a per-item/per-id addressing scheme built from
a confirmed ID-naming convention leaves many real indices out of range,
silently falling back to a placeholder/error value for the rest.

This is one ambiguity with two opposite wrong guesses, both confirmed in
separate projects:

**Direction 1 (assumed shared, was actually local):** a multi-part
icon/mesh looked like it needed one big shared vertex table because every
chunk's edge indices were small. Actually each chunk carried its own tiny
vertex table immediately before its own edge list, with indices always
restarting at 0 per chunk.

**Direction 2 (assumed local, was actually shared/flat):** Champions of
Krynn (Amiga)'s WALLDEF-referenced 8x8 tile art. The tile-bank container's
own directory entries follow a confirmed `10*wallId+wallset` composite-id
naming scheme (mirroring a sibling GLIB engine's own confirmed per-wall
"scheme 2" addressing), which made a per-wall LOCAL tile bank (`[placeholder,
universal, thisWall'sSpecificTiles]`, ~70-116 tiles) the natural first
build. WALLDEF's own raw view-index bytes go up to 233, so this only put
60/115 real view slices in bounds — the rest silently fell back to a
placeholder tile via the renderer's own out-of-range fallback (an easy
failure to miss without explicitly counting skips vs. successful writes).
The real addressing was ONE flat, whole-file bank — `[placeholder,
universal-id-first, then every other directory entry's tiles concatenated
in directory order]` — the exact structure this same engine's OTHER
container format (GLIB) already uses for its own confirmed "scheme 1".
Switching fixed all 115/115 view slices with zero out-of-range indices and
produced coherent, non-degenerate art for the previously-blank slices.

**Fix, generalized:** when a directory/entry naming convention (composite
IDs, sequential per-item IDs) is confirmed correct for ORGANIZING a
container's entries, that says nothing yet about whether the RUNTIME index
space addressing those entries is per-item-local or one flat corpus-wide
concatenation — these are independent questions. Test both directions
cheaply: build the candidate bank, then explicitly count (not just
silently render) how many real indices land out of range. A high
out-of-range rate under a per-item-local bank is a strong, cheap signal to
try a flat whole-file concatenation next — especially if the SAME engine
family already has a confirmed flat-addressing convention elsewhere (a
different container format, a different title) to borrow the exact
structure from, rather than reinventing it.
