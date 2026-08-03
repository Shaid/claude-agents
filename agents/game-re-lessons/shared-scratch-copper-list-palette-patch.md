# A copper-list-shaped byte run isn't necessarily anyone's palette

**When it bites:** a mechanical byte-pattern scan for "another 32-word
copper-colour run" (register words `0x180`+`2n` incrementing consecutively)
finds one or more additional candidates beyond an already-confirmed static
palette, and you're about to read their colour values as a second screen's
real palette.

Not every screen's colours live in one static copper list the way the
first one you find usually does. Some engines install a **blank or stale**
copper list first, then **patch** its `COLORxx` register words in place at
runtime from a separate source table, via a small generic subroutine (68k
shape: read a 16-bit word from a source array, stop on a negative/`$FFFF`
sentinel; otherwise scan forward through the target copper list for the
next word in the `0x180`-`0x1BE` range and overwrite it — repeat). When
several different screens share one scratch copper-list slot for this
purpose (patch-then-install, reusing the same fixed address each time),
the bytes sitting in that slot at any moment in the file are just
whatever the *last* screen to use it left behind — not that screen's own
canonical table, and not any other screen's either.

Confirmed in Jungle Strike AGA (`JS`, the AGA build's main binary): one
already-confirmed static copper list (`$10b224`, the world-map palette)
coexists with a shared scratch slot used by three unrelated screens
(a HUD status panel, a mission-briefing image, and the main-menu
background) at different times. A mechanical scan for "another 32-entry
copper-colour run" found 6 further candidates that *looked* plausible
(one even had a green/black "HUD-ish" shape) — all were stale leftovers,
not any screen's real source. The real per-screen source tables lived at
completely different file offsets, invisible to a copper-list-shape scan
because they're plain data arrays, not copper instructions.

**Fix:** don't trust a copper-list byte-pattern scan as a palette oracle
once you've confirmed one screen patches its colours at runtime instead of
using a static list. Instead trace each screen's own *load* call site
(filename-string address + crunched/compressed-size immediate cross-matched
against the corpus, the same technique used to identify which buffer slot
loads which file) forward to its `LEA <source>,A0` / `BSR
<patch-routine>` / `install-copper-list` triplet — the source operand of
that `LEA` is the authoritative table, not whatever a shape-scan turns up.

A useful corroborating check once you have a candidate real palette but a
static render still doesn't fully match a reference screenshot: a static
UI/HUD asset frequently contains only the *empty* frame (borders, labels,
tick marks) with the coloured gauge fills and digit text supplied by a
separate runtime sprite/font overlay the static asset never contains at
all. If every non-fill element matches a reference exactly and only
variable-fill regions (bars, counters) differ, that's evidence the palette
is right and the missing content is a runtime layer outside the format's
scope — not evidence the palette is wrong (Jungle Strike's `status` HUD:
this is exactly what "WEAPONS bars are the wrong colour" turned out to be
once the real palette was found — the bars aren't wrong-coloured, they're
simply not present as fixed pixels in the static bitmap at all).
