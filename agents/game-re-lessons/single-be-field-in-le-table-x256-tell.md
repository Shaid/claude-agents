# A single big-endian field inside an otherwise-little-endian table (the ×256 tell)

**When it bites:** decoding a fixed-record table from a game binary where
every field reads little-endian except one `u16` that is stored
**big-endian**. Reading it LE gives a value that is exactly **×256** the
true value for every record — a uniform multiplicative factor, which makes
it look like the game stores "scaled" units (fixed-point gold, fractional
XP, etc.) rather than a byte-order problem.

**The diagnostic:** when every decoded value of one field is a constant
multiple (×256 for a `u16`, ×65536 for a `u32`) of the expected value across
*all* records, suspect a byte-swap, not a scaling factor — re-read the field
at the opposite endianness before building a "scaling" story. The two
interpretations are indistinguishable from the values alone; only the
field's byte layout discriminates. Similarly, a u16 misread one byte left
or right (alignment slip) shows up as values that are ×256 of something or
asymmetric garbage.

**Confirmed on:** Might and Magic I (DOS) item table in MM.EXE (+0x19B2A,
255 × 24-byte records): every one of the 10 stat bytes is a plain byte or
`u16LE` **except the cost field**, which is `u16` **big-endian** (byte
offsets +20..+21). The first verification pass read it LE and reported
"cost is stored ×256" (Club 256 vs 1, Dagger 1280 vs 5, Hand axe 2560 vs
10 — all exactly 256× the ScummVM items.txt values); re-reading as BE
matched 255/255 records byte-exact. Second instance of the same trap in
the same file family: the monster table's `u16LE` experience field read as
BE produced a phantom "exp is fractional, ×256 units" claim. A constant
×256 (or ×65536) mismatch is a byte-order tell, not a unit story.
