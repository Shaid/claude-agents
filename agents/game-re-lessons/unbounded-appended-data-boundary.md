# Finding where headerless appended data stops, with no length field

**When it bites:** a blob of unidentified data follows a known, already-solved
structure in the same file (leftover space after a directory's last entry, data
past a compressed stream's terminator, bytes after a screen's expected pixel
count) and there is no length prefix, count field, or second terminator marking
where it ends.

Don't reach for a fixed guessed cutoff or eyeball a single render and call it
done. Real image/bitmap data has a small effective byte alphabet — borders and
fills repeat, so a fixed-size chunk (a tile, an icon, a sprite row) typically
uses well under half its possible byte values. Unrelated non-image data
(compiled data tables, mixed-content records, another compressed stream reread
without decompressing) spreads much closer to a uniform distribution over the
full byte range. This gives a cheap, purely structural boundary test: compute
unique-byte-count (or entropy, or distinct-palette-index count once a colour
decode is in hand) per fixed-size chunk, and require several **consecutive**
chunks to cross a threshold before calling it the boundary — one chunk alone
can trip the same test by chance (a genuinely busy/detailed icon can also have
a high unique-byte count), but a real transition into different data stays
past the threshold for the rest of the file, it doesn't flicker.

A diversity/entropy boundary test tells you *that* the data changes, not
*what* it changes into. Treat anything past a detected boundary as a *new
format to identify*, not a tail to keep decoding under the old hypothesis —
and don't assume a detected transition is a section/directory edge until
something independent (a code trace, a table entry, a count) confirms it. It
can just as easily be an ordinary content-type change at an ordinary frame
boundary inside an otherwise-uniform, already-solved format: Jungle Strike
AGA's `heli_sprite` (228 sprite frames, no directory) has a sharp,
reproducible byte-diversity transition at 91% through the file that is real,
but it's simply where the 216 helicopter-rotation frames end and the 12
explosion frames begin (different pixel statistics, same table-driven format,
no header or loader reference at that offset at all).

**Before trusting a "clean render" at some assumed chunk size, check whether
that chunk is actually one whole record — or just one *plane* of a
multi-plane sequential sprite.** If this project (or the engine family) has
*any* other confirmed sprite format using N sequential bitplanes per image
(a 1bpp mask + 6bpp colour convention is extremely common — see
`amiga-hardware-specifics.md`), a same-sized single-plane slice of a real
multi-plane image will *also* render as a clean-looking bitmap in isolation:
a lone colour bitplane of a limited-palette image is still a low-entropy
black/white pattern (repeated borders, blocky flat-colour regions). So "the
1-bit render looks clean" is not, by itself, evidence the chunk size is the
whole record — cross-check the assumed chunk size against `record_size /
N_planes_this_engine_uses_elsewhere` before finalizing, and if a full-colour
decode at `N_planes * chunk_size` *also* renders cleanly (through whatever
palette the rest of the project already confirmed), prefer that reading:
genuinely finished, coherent colour art is much stronger evidence than a
monochrome silhouette, and a project-wide sprite convention (same mask+colour
layering used everywhere else) is exactly the kind of prior the "prior-art
corpora" table exists to make you check first.

**Before decoding an unidentified appended blob as graphics at all, test the
audio hypothesis — it costs one plot.** Interpret the bytes as signed 8-bit
and plot min/max per column: real PCM shows unmistakable attack/decay
envelopes with near-silence between events. A cheap numeric version: median
`|byte[i+1] - byte[i]|` over a sliding window separates the two cleanly in
practice. Game data files routinely pack graphics *and* sound in one blob —
check whether the file header's own fields or the loader's own comments
already hint at a second content type before typing up a graphics-only
answer. And cross-platform ports are an oracle for *audio*, not just for
pixels: sound effects are usually shipped as the identical PCM with only a
sign convention differing (signed on Amiga, unsigned/0x80-centred on DOS), so
a plain `bytes.find(sample ^ 0x80)` over the other platform's archive is a
byte-exact identification with no decoding at all — try this first on any
unidentified blob when a port exists, it's far cheaper than any structural
analysis and it either confirms or refutes outright.

Two mechanical traps on the way there, both worth checking for explicitly:
1. **First check it isn't more of the same compressed stream** (re-run the
   RLE/PackBits decoder starting right at the boundary) before assuming a raw
   read — a mis-set boundary can *look* like garbage under one interpretation
   and be clean under the other. A decoder producing hundreds of near-zero-
   length pseudo-streams (single `0x00` bytes misparsed as empty streams) is
   itself a `rle-decode-succeeds-on-garbage` symptom, and the signal to try a
   raw, uncompressed read instead.
2. **Off-by-one in the "N consecutive chunks" scan is easy to introduce and
   easy to miss**: `range(n - K)` excludes the final valid window start
   (`i = n - K`), so a boundary landing in the last `K` chunks of the file
   silently falls through to "no boundary found" and the whole tail gets
   treated as valid content. Use `range(n - K + 1)`, and cross-check with a
   throwaway repro (`uniq = [10]*10 + [50]*5` should return `10`, not `15`)
   before trusting the heuristic's output counts.

**Worked example (Black Crypt, Amiga, `crawl` project) — three passes to the
real answer, each wrong in a different, instructive way.** `bcdfb`-`bcdfn`'s
9-19 KB of data after the monster-sprite RLE stream sat logged for multiple
sessions as "small 16x16-style icons, purpose not yet determined."

*Pass 1* read raw (uncompressed) 40-byte chunks immediately after the
stream's `0x00` terminator and decoded each as a standalone 16x20x1bpp planar
bitmap, producing clean, recognisable glyphs for the first several dozen
chunks per file before sharply degrading into full-byte-range noise —
reported as "692 icons across 13 files." This was the multi-plane trap above:
40 bytes is exactly `bpr` for a 16x20 sprite, and this project's other three
sprite formats all use 1bpp-mask + 6bpp-EHB-colour, 7 sequential planes.

*Pass 2* re-decoded at `7 * 40 = 280` bytes/icon (mask + 6 colour planes)
through the project's already-confirmed palette and got genuinely finished,
coherent colour art (wall-mounted control panels, dials, a gargoyle face) —
reported as "92 7-plane icons, 7 per file." This looked like the fix, and
still wasn't: the "692 icons" tell was hiding in pass 1's own boundary
counts (61, 49, 49, 49, 69, 49, 52, 52, 49, 56, 52, 53, 52 per file),
clustering tightly around small multiples of 7 (49 = 7×7 exactly in five
files) — worth checking *before* trusting a boundary count at face value.

*Pass 3*, a later session, found the 9-19 KB is not icons all the way to EOF
under *either* reading. Only the first **1932 bytes** are graphics; the
remaining 7-17 KB per file is a bank of raw signed 8-bit PCM sound effects —
proven byte-exact against the DOS release's `clipper.clp` type-4 entries via
the `XOR 0x80` sign-flip search above (one file's post-1932 region is 100%
tiled by three known DOS samples, no gap or overlap). Both pass 1 and pass 2
were decoding audio as bitplanes: the colour-diversity scan from this file's
main heuristic *did* find the real transition at roughly the right offset —
and then the far side got filed as "unidentified noise" and quietly left
inside the icon atlas anyway, instead of being investigated as its own
format the way this file's second section above now says to.

The real format: a fixed **1932 B = 3 x 644 B** header region, each 644 B
block holding *the same wall decoration at three view distances* (16x20 /
16x15 / 16x11, 7 sequential planes = mask + 6bpp EHB, tiling
`280 + 210 + 154 = 644` exactly), followed by the PCM bank. Note the
corollary for chunk-size heuristics generally: a uniform stride was never
going to find the graphics region either — the three per-distance records are
different sizes, and the giveaway was that the masks are nested rectangles
whose widths (16, ~12, ~8 px) shrink in step with the heights. When
per-record sizes vary, look for a *self-tiling* decomposition that consumes a
repeating block exactly, not a constant stride.
