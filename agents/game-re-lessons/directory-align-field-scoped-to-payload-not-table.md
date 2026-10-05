# A directory header's own `align` field governs payload spacing, not the header's own internal table layout

**When it bites:** a self-describing archive/wave-bank/directory header
declares both a record count and an `align`/`alignment` field, your parser
rounds an internal table boundary (e.g. "id table ends here, so the offset
table must start at the next `align`-byte boundary") up to that field, and
either the last entry's computed size goes negative, or every entry's
resolved byte range is subtly wrong by a fixed, small amount.

Confirmed on CRI's **AFS2** wave-bank format (`tools/shared/awb.ts`,
`~/Development/vanille`, Dragon's Crown PS3): the header is `"AFS2"` magic,
`offsetSize`/`idSize` bytes, a `u32 count`, and a `u32 align` (e.g. `32`),
followed by a flat `count`-entry id table, then a `count+1`-entry offset
table (the last entry an EOF sentinel). A parser computed
`offsetTableStart = roundUp(idTableStart + idTableLen, align)` — plausible,
since `align` is real and does mean something in this exact header. It's
just the *wrong* something: `align` governs how far apart consecutive
**data payload** offsets are placed later in the file, not the header's own
id-table→offset-table transition, which is unaligned
(`offsetTableStart = idTableStart + idTableLen`, no rounding). The bug
silently shifted the *whole* offset table forward by one 4-byte slot for
every real corpus file (their `idTableLen` always happened to be smaller
than `align`), corrupting every entry's resolved `{offset, size}` — most
visibly a **negative size on the very last entry**, since the shifted
"last" offset read landed on the sentinel with no next entry to diff
against, while every other entry just looked plausible-but-wrong (still
positive, still roughly in the right place).

**Root cause of the trap:** one field, two genuinely different roles
(internal header-table alignment vs. payload-region alignment), and only
one of those roles is the one the field's name/position suggests when
you're skimming the header shape. Nothing about the byte layout hints
which role applies where — you have to check against real data.

**Fix and verification:** an independent whole-file oracle settled it in
minutes — searching the real 161,966,642-byte `.awb` for the literal
4-byte magic of its payload codec (`"HCA\0"`) found exactly as many hits as
the header's declared `count` **and** as many as a trusted third-party
decoder (`vgmstream-cli`) independently reported as its own stream count.
The *unaligned* offset table reproduced all of those hit positions within a
small, expected intra-slot padding tolerance (0-30 bytes before each
stream's own magic); the *aligned* one reproduced none of them exactly.
This also affected every other consumer sharing the same parser — in this
case an *embedded* copy of the same wave-bank format nested inside a
sibling container (an ACB cue bank's `AwbFile` blob), which had the
identical bug for the identical reason since it went through the same code
path.

**Generalizes:** any self-describing directory/archive header that
declares one alignment constant is worth treating as **two separate
claims** — "this many bytes of internal table structure" vs. "payload
regions land on N-byte boundaries" — and verifying each independently
against real bytes, rather than assuming a single alignment field
uniformly governs the whole file. When in doubt, a corpus-wide magic-byte
census of the *payload* codec is a cheap, assumption-free way to settle
which reading is correct — see also `self-consistent-chain-wrong-unit.md`
(a sibling trap: an offset chain that's internally self-consistent proves
nothing without an external terminal check).
