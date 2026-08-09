# In a mostly-zero sparse record table, adjacent nonzero bytes can look like a wider field purely by chance

**When it bites:** decoding an undocumented fixed-stride record table where
most bytes are `0x00` and only a few per row are nonzero, and you notice a
specific nonzero byte value (e.g. `0xC8` = 200) repeatedly appears with a
`0x00` byte immediately next to it across several rows — tempting you to
read that as a genuine multi-byte (e.g. 16-bit big-endian) field at a
consistent column position.

In a sparse table (most cells zero), a byte's neighbour being `0x00` is the
*expected*, default case, not a correlated signal — it says nothing about
whether the two bytes form one logical field. A handful of rows showing
"`0x00` next to `0xC8`" at what looks like a consistent pair position can
be pure coincidence of sparsity, not evidence of field width.

**The check that catches it:** tabulate, independently for *every* single
byte column (not just the ones from your initial sample rows), the full
set of nonzero values that column takes across the whole corpus. If the
"paired" value (`0xC8`/200 in the worked example) turns out to appear
standalone in many different columns — not just the two columns your
sample rows happened to show — it's a plain single-byte value that can
occupy any column, not a fixed-position multi-byte field. A genuine 16-bit
field would show the high byte capped near 0 *only* at its own fixed
column pair, with other columns free of it; a coincidental sparse-pairing
artifact shows the "paired" value scattered across most/all columns.

Confirmed on Phantasie III (Amiga, `nicodemus`)'s undeciphered
`inititem.dat`: two sample rows (of 181) showed `0x00`/`0xC8` immediately
adjacent at what looked like a consistent pair offset, and an earlier pass
recorded this as "a recurring 16-bit big-endian value 0x00C8 (200)
appearing at consistent-looking column pairs." Extending the check to
every column across the whole 87-nonzero-row corpus showed `0xC8`
appearing as a plain single byte in **12 of the table's 18 columns** —
not two — refuting the 16-bit-field reading and correctly reclassifying
it as "18 independent one-byte fields, one of which frequently takes the
value 200," a materially different (and much simpler) structural
hypothesis.

**General rule:** never confirm a multi-byte field's width or position
from 1-2 example rows in a sparse table. Tabulate the full per-column
value set across the whole corpus first; a value that can occupy many
different single-byte columns independently is not part of a fixed-width
multi-byte field at any one of them.
