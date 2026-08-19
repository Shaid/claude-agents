# Name fields match but trailing record fields are misaligned (name width off by one)

**When it bites:** verifying a fixed-size record-table decode by checking
that record *names* match an oracle (a fan transcription, a sibling port's
data). If the on-disk name field is one byte wider than assumed — a 15-byte
name where you assumed 14, a trailing terminator/pad counted as part of the
name, a fixed-width name that includes a terminator byte — every numeric
field after the name shifts by one position. **The names still all match**
(the extra byte is a pad/terminator, invisible to a name comparison), so a
name-only verification passes while every stat field is wrong. The
misalignment also often produces a "constant lead byte" or "phantom field"
artifact at the exact boundary you misread.

**The fix:** verify full records byte-exact against an independent
transcription (every field, not just names) — that is what discriminates a
correct decode from a shifted one. When a numeric-field cross-check
mismatches *systematically* from the first record on, re-audit the field
*widths* of everything before the mismatch, especially the name — don't
invent semantics for the shifted bytes (a "constant lead byte" that is
actually the name's pad byte, an "extra 2-byte gap" that is actually a
2-byte field you double-counted).

**Confirmed on:** Might and Magic I (DOS) monster table in MM.EXE
(+0x1B312, 195 × 32-byte records): the name field is **15 bytes** (the 15th
byte is the real last letter for 15-char names like "12 HEADED HYDRA", else
a space pad). A 14-byte assumption made the first stats byte read as a
"constant 0x20 lead byte" whose special values were ASCII letters — which
was the clue that it was actually the tail of the name field. The name
comparison had passed 195/195 the whole time. Re-parsing with the 15-byte
name matched all 195 records byte-exact.
