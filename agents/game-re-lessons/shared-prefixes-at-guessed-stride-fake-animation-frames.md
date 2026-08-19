# Shared byte prefixes at a guessed stride read as "animation frames" — coincidence until the reader's arithmetic confirms the stride

**When it bites:** about to document fixed-stride records as related content
(walk-cycle frames, variants of one graphic, "same figure, different legs")
because adjacent records share byte-identical prefixes — while the stride
itself is a guess (region size ÷ plausible count, a plausible sprite size)
with no reader-side address arithmetic behind it.

Contiguous graphic data cut at *any* stride shows correlated or identical
leading bytes wherever the art is locally similar — sky rows, blank margins,
repeated outline patterns. Byte-identical prefixes are therefore evidence
that the data is graphics, not evidence that your record boundaries are
real.

Confirmed on WIME CPC (`middilgard`): a post-map region was cut as
34 × 128-byte records; records 0/1 shared a 26-byte prefix and 2/3 an
11-byte prefix, which was written up as byte-verified walk-cycle structure
("upper body identical, only the legs animate") and the decode marked
confirmed in the format doc. The real record size was 32 bytes (168 8×8
tiles) — each 128-byte "sprite" straddled four unrelated tiles, and the
"walk cycle" evaporated. The byte observation was real and reproducible; the
interpretation was an artifact of the stride. Only the game's own indexing
arithmetic (`HL = base + index × 32` at `&24A7`) settled the record size.

Rule: a shared-prefix/shared-structure observation between records supports
a decode only *after* the stride is pinned by the reader (address
arithmetic, a count field the code consumes, or a stride that survives
`serpentine-row-order-mimics-mirrored-rows.md`-style coherence sweeps). Until
then, keep it labelled as an observation about the region, not about
records.

Siblings: `record-stride-guess-vs-recount-fields.md` (recover stride from
the reader's field count), `fixed-stride-record-count-unverified.md` (render
past row 0 before trusting `(size−header)/stride`).
