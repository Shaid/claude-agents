# A header/size match doesn't prove the pixel encoding — or the right decompressor

**When it bites:** a candidate image header's declared width/height, run through a plausible-size formula, exactly matches the decompressed payload length — for more than one competing pixel-encoding hypothesis at once. Also fires one layer earlier: two competing *decompressors* (e.g. PackBits and LZSS) both produce output that exactly matches the declared/expected length for the same compressed input. Also fires across ports: a same-named sprite/image file on two different platform releases happens to be byte-for-byte the same *size*.

Different pixel encodings can produce the *same total byte count* for a
given width purely by arithmetic coincidence — e.g. Amiga-style interleaved
planar (`ceil(w/16)*2 * depth` bytes/row) and IIGS-style packed-nibble
(`ceil(ceil(w/2)/8)*8` bytes/row) happen to agree for narrow widths like 24-25
px at depth 4, both landing on 16 bytes/row. A `data.length === headerSize +
bytesPerRow*height` check that tries formats in sequence will silently
accept the *first* one whose formula happens to match, even if it's the
wrong encoding — a length match is necessary, not sufficient.

Found on WIME's DOS EGA release: two small (24x12, 25x13) resources used a
27-byte IIGS-shaped header (LE u16 width/height at the IIGS offsets) but
carried IIGS *packed-nibble* pixel data even though every other image on
that same platform uses Amiga-style *planar* data under a different (28-byte,
BE-offset) header — decoding both interpretations and rendering them showed
the packed-nibble reading as a coherent filled icon shape, the planar reading
as noise. The header's offset/endianness shape and the pixel encoding it
carries are two independent facts; matching one format family's header does
not license assuming its pixel encoding too. When a format autodetector
matches purely on total byte count, decode *all* structurally-plausible
candidates and check for shape coherence (or an independent oracle) before
trusting whichever one matched first.

The same trap shows up with zero header at all, and the *numerically
cleaner* candidate can be the wrong one: Wizardry 6 Amiga's 32768-byte
`.EGA` screens fit two competing dimension/depth guesses — 320x200 at 4
bitplanes (`40*200*4 = 32000`, leaving a 768-byte remainder that's still
unexplained) and 256x256 at 4 bitplanes (`32*256*4 = 32768`, an exact fit
with zero remainder — arithmetically the "nicer" answer). The exact-fit
256x256 candidate rendered as pure noise; the messier 320x200-with-leftover
candidate rendered legible engraved-stone title text reading "BANE OF
COSMIC FORGE" once the plane-interleaving order was also tried both ways
(plane-major legible, row-interleaved a much fuzzier partial match). Prefer
the byte-count formula that divides evenly all else being equal, but never
*let it substitute for* rendering — an uneven remainder is not disproof by
itself, and a perfect division is not proof by itself.

**Third confirmed case — same encoding shape, wrong semantic axis, and the
render itself can't tell you.** Desert Strike (Amiga)'s `disk3-00/04/07/11`
were documented "confirmed" as `u16 width, u16 height, then width*height
bytes of flat 8bpp chunky *pixels*" — the byte-exact zero-remainder
invariant (`length - 4 == w*h`) held for all 4 files, and rendering the
bytes as greyscale pixels produced a plausible-looking coherent top-down
terrain scene (coastline, road grid). Both were wrong: the `width*height`
bytes are **tile indices into a separate tileset** (one byte per 16x16
cell), not pixels — a tilemap, not a chunky image. The size formula can't
distinguish the two because the byte-count arithmetic is *identical*
either way (`w*h` bytes, full stop) — only the semantic meaning of each
byte differs. Worse, the wrong "pixel" interpretation still passed the
visual-oracle bar: a tilemap's index field is naturally spatially smooth
(neighbouring terrain reuses neighbouring tile numbers), so treating tile
IDs as greyscale intensities still renders a locally-coherent-looking
picture, for the same reason a real pixel image would. Rendering plausibly
is not sufficient evidence when the candidate wrong-encoding has its own
source of spatial smoothness — cross-check independently: does a "this is
a different pixel encoding than every other confirmed format in this
corpus" flag exist for the candidate (a real tell that should prompt
re-examination), and does the corpus contain an separately-unsolved,
similarly-sized blob that could plausibly be the tileset this file
indexes? If yes, decode *that* first and try composing the two before
trusting the flat-pixel render.

**Fourth confirmed case — planar (bitplane) vs. packed (chunky) pixels,
same byte count either way.** Wizardry 6 DOS/EGA's `.CGA`/`.T16`
full-screen and tile-bank files are exactly half (2bpp) or equal (4bpp)
the size of their already-confirmed-planar `.EGA` siblings — arithmetic
that a plane-major bitplane decode at the matching bit depth satisfies
exactly (`width/8*height*bpp` bytes, identical formula whichever way the
bits are arranged). Every other format in the whole corpus (Amiga and DOS
`.EGA` alike) was planar, so planar was the natural first hypothesis —
and it rendered as pure noise for every one of these files. The actual
encoding was packed/chunky (N bits/pixel packed directly into consecutive
bytes, not N separate bitplanes), which a `decodePackedPixelLinear`-style
decode confirmed immediately. The lesson generalizes past this one
example: total byte count is *exactly* the same whether a given bit depth
is stored as planar bitplanes or as packed chunky pixels (both are just
"N bits of index data per pixel," differently arranged) — a byte-count
match narrows the *bit depth*, never the *arrangement*, and a corpus
being uniformly planar elsewhere is a prior, not a proof, for a sibling
platform's own asset variants (DOS CGA/Tandy-family formats in particular
lean packed/chunky, unlike EGA/Amiga's bitplane convention — see
`game-re-tooling/dos.md`).

**Fifth confirmed case — same trap one layer earlier, picking the
decompressor itself.** Vengeance of Excalibur's `ANI32.RES` FRML #714 and
#900 are genuinely LZSS-compressed, but PackBits *also* decompresses their
compressed bytes to the exact declared output length — the only validity
check the decoder had — while silently producing a corrupted frame table
(frame count reads back correct by coincidence, but every frame's
x/y/width/height/`endOffset` is garbage). Both candidates "succeed" by the
length check; a fixed "prefer PackBits" tie-break for length-matching
candidates picked the wrong one for years. The actual tell was one level
downstream, in the very field the wrong decode corrupted: frame 0's implied
bitplane depth (`dataSize / (bytesPerRow*height)`) divides out to a clean
integer 1-8 under the correct codec and never does under the wrong one
(2.49 and a negative value for these two, vs. a clean 5 both times under
LZSS). A length match is exactly as weak a discriminator for *which
decompressor ran* as it is for *which pixel encoding a header implies* —
when two decompression candidates both hit the target length, decode both
and score a downstream structural invariant (a table's implied count,
a frame's implied depth, a directory's implied offset) before picking
one, never a fixed per-format preference.

**Sixth confirmed case — a cross-port file-size match doesn't prove the two
files share a pixel layout either.** Phantasie II (Atari ST)'s
`PARTY1.PAT`/`PARTY2.PAT` are byte-for-byte the same size (8,192 B) as
Phantasie I (Amiga)'s `party1.pat`/`party2.pat`, while P2's `MSTR1.PAT`/
`MSTR2.PAT` are ~13% *larger* than P1's `mstr1.pat`/`mstr2.pat`. It's
natural to read that split as evidence `PARTY*.PAT` kept P1's raw
contiguous-planar layout while only `MSTR*.PAT` switched to the ST
word-interleaved layout — a same-project doc recorded exactly that
reasoning as a hypothesis. Rendering `PARTY1.PAT` under both layouts
refuted it: P2's `PARTY*.PAT` also uses the ST-interleaved layout despite
matching P1's file size exactly (P2's `MSTR*.PAT` uses it too, confirmed
separately). The reason size can't discriminate here is the general rule
from the rest of this file: total bytes for a given width/height/bitplane
count (`width/8 * height * bitplanes`) is identical under contiguous-planar
and word-interleaved arrangements — only the *order* of bytes differs, and
order is invisible to a size comparison. A same-size match across ports is
exactly as weak a layout signal as a same-size match across candidate
headers within one file; only a pixel render (or an independent oracle)
settles it.

**Seventh confirmed case — a block-compressed texture's total byte count
ties across whole *families* of `(width, height, format)` triples, and a
total-variation render score resolves it cheaply at corpus scale.** NieR
(2010, PS3)'s `TX2D` GPU-texture records are headerless BC1/BC3 mip chains
with `rawSize` as the *only* self-describing field, recovered by inverting
`alignUp(mipChainBytes(w,h,bytesPerBlock),128) === rawSize`. Doubling one
dimension while halving bytes/block (BC1's 8 B/block at `2w x h` vs. BC3's
16 B/block at `w x h`) produces the *exact same* total — corpus-wide, 96.7%
of records (1,488/1,539) had 3-12 tied candidates, not a rare edge case.
Unlike the earlier cases in this file, there was no independent oracle and
no downstream count/depth field to cross-check — the fix was to *decode
every candidate's pixel data* and score it by **total variation** (mean
absolute colour delta between adjacent pixels): a real image reinterpreted
at the wrong dimensions scrambles unrelated rows together, which is
measurably noisier than the correct decode. Margins ranged from decisive
(>5x, best `TV≈2-11` vs. runner-up `TV≈60-120`, for detailed textures) down
to near-ties (`≤1.2x`) for flat/low-detail textures — but a near-tie doesn't
mean a wrong pick: spot-checking a `1.09x`-margin "close" case still
rendered a coherent, recognisable book-cover texture, because when content
is naturally flat every candidate scores similarly low and the specific
dimension barely matters for output plausibility. The general form: when a
byte-size formula genuinely ties across an *entire family* of candidates
(not just two), and no cheaper structural invariant exists to break the
tie, decode every candidate and let a smoothness/total-variation score on
the decoded content pick the winner — it's cheap enough to run corpus-wide
(one decode + one O(pixels) pass per candidate) and degrades gracefully
(a wrong pick on inherently flat content still looks plausible, since
there's nothing there to get wrong).
