# A community RAM-map's per-byte bit-string can imply the wrong field order — trace real bit-extraction instructions instead

**When it bites:** a reference doc/RAM-map describes a multi-byte packed
bitfield as an MSB-first-per-byte bit-string (e.g. `aaaaaaab bbbbbbcc
ccccdddd...`, read left-to-right as "first byte's high bit starts field
a"), and you're about to transcribe field offsets/widths straight from
that notation without checking a single real instruction that reads one
of the fields.

The prose notation is easy to misread as "fields pack MSB-first, byte by
byte, in the order written" — but the actual on-disk packing can instead
be a single **little-endian bitstream across the whole multi-byte span**:
field 1 occupies bits 0-N of the *first* byte (its low bits), field 2
starts wherever field 1 left off and can straddle into the *next* byte's
low bits, and so on, with the *last*-named field in the prose ending up
in the *high* bits of the *last* byte — effectively the reverse of what
the left-to-right string suggests at a glance.

Confirmed on FFVI (SNES, `ceres` project): a 6-byte packed field in
`MapProp` (naming which graphics/tile-formation resources a map uses) is
documented by the community's own RAM map as `aaaaaaab bbbbbbcc
ccccdddd dddeeeee eeffffff fggggggg` — read at face value, field `g`
(`tileset1`) would sit at the very end of the 48-bit span, in the last
byte's low bits. The real 65816 loader code (`LoadMapGfx`,
`src/field/map.asm`) reads `tileset1` as `byte0 & 0x7f` — the low 7 bits
of the *first* byte. Tracing all 7 subfields' actual bit-extraction
instructions one at a time (each a distinct `lda`/`asl`/`lsr`/`and`/`xba`
sequence) showed the true packing is LSB-first across the entire 48-bit
little-endian span: field 1 in the low bits of byte 0, the next field
starting exactly where the previous one's bit-width ends (crossing byte
boundaries transparently), with the *last*-named field in the prose
landing in the *high* bits of the *last* byte — the mirror image of a
naive left-to-right reading.

**Fix:** treat a bit-string RAM-map note as a *lead*, not ground truth,
for any field that isn't a single whole byte. Find at least one real
instruction that reads each subfield (an `AND`/shift/mask sequence
against the record's raw bytes) and derive the bit offset/width from that
arithmetic directly, the same way a byte offset would be confirmed from a
`lda struct+N,x`. A quick sanity check that generalizes: if you can find
*any* two independently-confirmed subfields whose bit ranges are
adjacent, check whether they're adjacent in prose-reading order or in the
reverse order — that alone tells you which packing convention the whole
record uses before you invest in decoding the rest by hand.
