# A recurring "tag byte" or plausible-looking record stride found by scanning raw bytes can be reading the wrong thing entirely

**When it bites:** a byte-level scan of unstructured data (no record stride
confirmed yet, typically before any disassembly trace exists) finds a small
set of "lead bytes" recurring throughout a region and you're about to
document them as an escape/tag/sentinel scheme marking a distinct
sub-structure (an "overlay descriptor," a "command byte," etc.) — or a
brute-force stride scan finds a byte pattern that *partially* matches a
plausible record layout (a monotonic run of a few "offset"-shaped values at
one stride) and you're tempted to trust it before every field in every
record checks out.

Middilgard's `SCEN`/`NECS` scene-object format (Conan the Cimmerian, Vengeance
of Excalibur) was documented across multiple sessions as: a header, then
6-byte `{x, y, id}` entries, then a section of "overlay descriptors" tagged
with lead bytes `0xE4`-`0xE7`, then a footer. A full disassembly trace of
Vengeance's `_DrawScene`/`_DrawScenePiece` (the only game in the corpus with a
symbol-rich disassembly) found the real per-object record is a **4-byte**
big-endian packed bitfield, not 6 bytes — and once decoded at the correct
4-byte stride, `0xE4`-`0xE7` turned out to be nothing but the ordinary top
nibble of one specific, common field value (`typeIndex=14`) combined with a
clear flag bit; the four observed variants (`E4`-`E7`) were just the low 3
bits of an adjacent field varying underneath the same common top nibble.
There was no tag/escape scheme and no footer at all — confirmed by a
byte-exact, zero-deviation size formula (`resource.length === header +
(count+1)*4` across all 266 real resources) once the correct stride was
known. The "overlay descriptors" and "footer" were retracted outright, not
merely reinterpreted.

The mechanism generalizes: guessing a record stride from eyeballed byte
patterns (rather than a code trace or a size-formula fit validated
corpus-wide) misaligns every subsequent read. A misaligned read doesn't fail
loudly — it just samples different byte offsets each time, and if one
particular field value happens to be common (many records share the same
"type" or "flags" nibble), that value's byte(s) will appear to recur "as a
tag" at what looks like irregular intervals, especially if the wrong stride
assumption (6 bytes here) doesn't evenly divide the right one (4 bytes),
scattering the apparent tag positions unpredictably. Before documenting a
recurring byte value as a tag/escape/sentinel scheme: confirm the record
stride first (trace the reader if any disassembly is available, or fit a
byte-exact `size === f(count)` formula across the whole corpus with zero
deviation) and re-decode at that stride before concluding the recurring byte
is anything other than an ordinary field.

## The compressed-stream variant: a "plausible partial record" can be real signal seen through the wrong frame

A sibling trap, found reading raw (uncompressed) struct data that turned
out to actually be compressed: a byte-level stride scan can find a
genuinely non-coincidental partial match — a monotonic run of "offset"-
looking values incrementing by a real, meaningful constant — and still be
wrong, because the file is compressed and what you're looking at is a
tokenized encoding of the real record, not the record itself. Wizardry 6's
DOS `.pic` files showed a "stride-7" signal (`0x0258, 0x0278, 0x0298,
0x02B8` read as big-endian `u16`s, each exactly `+32` apart, matching the
format's known 32-bytes-per-tile constant) with 4 byte-identical trailing
5-byte suffixes across the first several apparent "records" — real,
reproducible, and completely wrong to trust as a raw struct read: the file
turned out to be a block RLE stream, and those bytes were the *little-
endian* directory offsets of the *decompressed* image, each preceded by a
1-byte RLE literal-count control byte (`0x02`, "copy the next 2 bytes")
that shifted every apparent field boundary by exactly one byte and made a
2-byte LE field look like a phantom BE pattern at stride 7 instead of the
real stride 5. The tell, in hindsight: some of the "field" bytes in the
suffix (`0xFD`, `0xED`) were small negative numbers when read as signed
bytes (`-3`, `-19`) — exactly the shape of an RLE run-length control byte,
not a plausible tile width/height/mask value. When a partial record match
is real but never resolves into a fully self-consistent layout, and
nearby "field" bytes look like small signed run/literal counts rather than
plausible dimensions/flags, test whether the data is compressed before
concluding the stride or field order is merely off by a little.
