# A confirmed no-remap text-draw path is a free oracle for "what glyph does raw value V render as"

**When it bites:** a specific raw byte value's real on-screen glyph is in
question (commonly a readability hypothesis like "these two bytes probably
render as an apostrophe because they sit in apostrophe-shaped positions in
otherwise-legible text"), the tile/font ROM producing that glyph is already
decoded and rendered, and the instinct is to go hunt for a separate
ASCII→tile-index remap table to settle it.

Check first whether **any already-confirmed text-draw routine** for a
*different* string in the same ROM performs zero remapping — i.e. copies
the raw text byte directly into tile/character RAM as the tile index, no
lookup table in between. If one exists, it proves the tile ROM itself is
laid out identity-mapped (tile N = ASCII code N) for whatever range that
routine's real strings actually use, and that's a free, already-available
oracle for *every* other byte value's glyph: just render the confirmed
tile ROM at the raw byte's own index using the already-confirmed tile
decoder, and look at it. No new remap table needs to be found or decoded.

Confirmed on Golden Axe (Sega System 16B, `kolbold` project): a prior
pass had flagged bytes `0x7d`/`0x7e` in the confirmed intro-narration text
("WE`0x7d`LL", "FIEND`0x7d`S PATH`0x7e`") as probably rendering as an
apostrophe, since substituting `'` for both made the surrounding English
read correctly — a plausible but never-tested readability hypothesis. A
follow-up pass traced a *different*, definitely-real string's draw
routine (the credits/UI-label draw loop, confirmed via `LEA(pc)+MOVEQ`
call-site tracing) and found it does exactly `move.b (a0)+,(a1)+` — raw
byte straight into tile RAM, zero remapping. That meant the already-
decoded, already-shipped tile ROM (`decodeSega16Tiles8x8`, confirmed
earlier via legible-text rendering) could be queried directly: rendering
raw tile index `0x27` (the literal ASCII apostrophe code) showed an
unambiguous small apostrophe glyph; rendering raw indices `0x7d` and
`0x7e` showed two clearly different, larger, non-apostrophe shapes. The
apostrophe hypothesis was refuted in minutes, with zero new decode work —
by reusing an oracle (the no-remap convention + the tile decoder) that
had already been fully paid for confirming something else.

**The fix / generalizable move:** before spending effort locating or
decoding a hypothesized remap/lookup table to answer "what does raw value
V really render as," check whether an already-confirmed draw path for
*any* string in the same asset elsewhere uses a direct, unmapped
value→asset-index convention. If so, that convention is transferable to
every other value in the same index space — apply the existing decoder at
the raw value directly rather than hunting for a separate remap
mechanism. This generalizes past fonts/tiles to any "does raw field value
V mean asset/state X" question in a system where at least one confirmed
consumer is known to be identity-mapped.
