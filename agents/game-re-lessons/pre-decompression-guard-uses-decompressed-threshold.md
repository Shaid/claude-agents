# A "too small" guard before decompression must not use a post-decompression size threshold

**When it bites:** a compressed-resource decoder throws "data too small" (or
similar) on a handful of resources whose on-disk size is small but not
implausibly so, and the guard fires *before* any decompression is attempted
— especially if the threshold looks borrowed from an unrelated uncompressed
header/payload size rather than derived from the compressed format itself.

A compressed resource's raw on-disk length has no necessary relationship to
its decompressed output length — a small, well-compressed image can be a
tiny fraction of its real decoded size. A guard of the form `if
(data.length < SOME_HEADER_SIZE) throw 'too small'` placed at the very top
of a decoder, before the compression stream is even inspected, silently
rejects exactly this class of resource: valid, decodable data that simply
compressed extremely well. The bug is subtle because the threshold value
usually **is** meaningful somewhere in the format (e.g. the smallest known
*uncompressed* header size) — it's just being checked against the wrong
buffer at the wrong pipeline stage.

Confirmed on the Excal-family engine's shared `decodeIMAG()`
(`src/assets/formats/imag.ts`, middilgard project): the guard required
`data.length >= 27` (`IIGS_HEADER_SIZE`, the largest *uncompressed* header
variant) applied to the **raw, still-compressed** resource bytes, before
`packBitsDecompress`/`lzssDecompress` ever ran. Two real resources across
two different games sharing this decoder failed this way: Vengeance of
Excalibur's `TITLE32A.RES` #110/#112 (26 bytes raw each) and Warriors of
Legend's `res32/object.res` #7049 (22 bytes raw). All three LZSS/PackBits-
decompress to their declared size exactly (196/206/22 bytes) and decode as
small-but-fully-self-consistent images once decompression is actually
attempted. Both games' docs had previously written these up as separate,
unrelated "no header variant fits"/"data too small" mysteries — they were
the identical bug, hit independently in two different investigations
months apart, because nobody had traced the guard back to what buffer it
was actually checking.

**Fix:** any pre-decompression length guard should only check what's needed
to safely read the compression header itself (e.g. a 4-byte size prefix) —
not a decompressed-payload-shaped threshold. The real "is this a plausible
decoded image" check belongs *after* decompression, against the
decompressed buffer, where a payload-size floor is actually meaningful.
Before trusting a "data too small" or similar early-exit error message on a
compressed resource, check which buffer (raw vs. decompressed) the failing
comparison is actually against — if it's the raw compressed bytes, the
threshold is very likely borrowed from the wrong side of the pipeline.
