# A ROM's UI text isn't all delimited the same way — some strings are NUL-terminated, others are one flat pool with zero separator bytes

**When it bites:** extracting a batch of UI/attract-mode/menu strings found
via a plain printable-ASCII scan, and a plausible-looking multi-label span
(e.g. several `"STAGE N"`/menu-option labels back to back) has no space, NUL,
or any other byte between two labels you know are semantically distinct —
before writing a heuristic splitter (on whitespace runs, on capitalization
changes, on expected label length) to force it into separate strings.

Confirmed on Golden Axe (Sega System 16B, `kolbold`): a `strings` scan over
the assembled, unencrypted `maincpu.bin` found real UI text in two different
conventions within the *same* ROM region. Some strings (`SELECT PLAYER`,
`TIME`, `GAME`, `ADVERTISE 1`-`4`) are cleanly bounded by `0x00` bytes on
both sides — a real per-string terminator convention, safe to split on. But
a nearby test-menu "select starting stage" string reads literally
`...STAGE 6 STAGE 8BONUS STAGEINCREASE YOUR POWERS` — no space and no NUL
between `"STAGE 8"` and `"BONUS STAGE"`, nor between `"BONUS STAGE"` and
`"INCREASE YOUR POWERS"`, even though these are unambiguously three distinct
menu labels. The same pattern showed up in a separate credits/attract-mode
string (`INSERT COIN`/`GAME OVER`/`CONTINUE?` etc, ~170 bytes, one single
printable run with zero interior separator bytes anywhere). This is a real,
deliberate flat string pool: the game's own code most likely selects
individual labels out of it via an `[offset,length]` index table elsewhere
(not located this session), not via an in-band delimiter.

The tell is structural, not aesthetic: if a "natural-looking" label boundary
inside a candidate multi-label span has **zero non-printable bytes** on
either side of it, there is no delimiter to find — the boundary is only
recoverable by locating the code/table that references it by explicit
offset+length, not by any smarter text-side heuristic (missing capital
letters, expected word length, etc. — arcade-era label pools do not reliably
signal boundaries visually). Do not force-split such a span by guesswork and
report it as a set of separately-verified strings; ship it as one raw pool
with a note, and treat the search for its real index/reference table as a
separate, still-open task. Meanwhile, do trust and split on a *real*
delimiter convention (e.g. `0x00`) wherever it is actually present in the
same ROM — the two conventions can and do coexist side by side in one
region, so check each span's actual boundary bytes rather than assuming the
whole ROM (or even the whole "UI text" area) uses one convention uniformly.
