# Round-looking leading longwords can be bitmap rows, not a header

**When it bites:** a candidate header's leading longwords all look
suspiciously round (many trailing/leading zero bits — the exact heuristic
used to spot size/offset/count tables), especially in a file whose name or
context suggests a centred, symmetric sprite (a vehicle, creature, logo,
or any top-down/side-on object rendered nose-on or centre-frame). Also
bites the inverse shape: a render at some candidate geometry shows real,
crisp, non-noise structure but doesn't cohere into a shape, and you've
been feeding the decoder a byte range with N bytes trimmed off one end
because they "looked like" a header/footer to skip.

A centred sprite's own bitmap rows are *inherently* round-looking: each row
is a contiguous run of set bits (`0b000...0111...1110...000`), which as a
raw integer has exactly the same "many zero bits, especially at the
edges" signature real size/offset fields have. The "suspiciously round
values" heuristic (recommended elsewhere for spotting header tables) cannot
distinguish the two by inspection alone.

Confirmed on Jungle Strike AGA's `heli_sprite` (the player Apache
helicopter): three prior passes read the leading longwords
(`0x00018000`, `0x0003C000`, `0x0007E000`, `0x000FF000`, `0x001FF800`,
`0x003FFC00`, ...) as a 6-field size/count header and searched for a
directory that was never there. They are literally the first ~8 rows of
frame 0's leftmost bitplane: a helicopter fuselage nose-on, narrow at the
tip and monotonically widening — i.e. the file has **no header at all**,
pixel data starts at byte 0.

**The fix:** before trusting "round-looking longwords = header", plot the
candidate values' bit-widths (or just eyeball the 0/1 pattern per word) and
check whether they monotonically widen-then-narrow, or stay symmetric
around a centre column, across consecutive words — that's a bitmap-row
profile, not a header/table. A real header's fields are usually not
monotonic in this way (a width, a height, a count, an offset don't form a
smooth curve). If the file's name suggests a discrete, roughly-symmetric
sprite, render the first N bytes as a 1bpp bitmap at a few plausible
narrow widths (32/48/64px) before spending more time on a header
hypothesis — a real render answers the question in one shot.

**Second confirmed case — the trailing-field variant, not just "no header
at all".** Desert Strike (Amiga)'s "object atlas" sprite format
(`docs/desertstrike/amiga/data-structure.md`): a 5,248-byte frame opens
with long `0xFF` runs that a prior pass read as "background, strip the
first 64 bytes as a header" before decoding the remaining 5,184 bytes as a
72x72 chunky image — every render showed real, crisp, non-noise structure
(a distinctive "X" cross-hatch) but never resolved into a shape, across
multiple geometry sweeps. The leading `0xFF` runs were genuine pixel data
(the top-left corner of a mostly-transparent sprite canvas); the real bug
was on the *other* end — the frame is 5,248 bytes, not 5,184, and the
missing 64 bytes are a **trailing** palette table, not a leading header.
The fix was the same in spirit as the first case (stop stripping bytes on
the strength of "this looks like a header/footer" and decode the *whole*
declared buffer), but the trimmed region was at the end, not the start —
check both when a "clean strip" isn't producing a coherent render.
