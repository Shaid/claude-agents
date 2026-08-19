# A legible text render is a weak palette-correctness oracle — unlike a photographic/painterly render

**When it bites:** about to accept a rendered text/UI screen (readable
letters, a legible label or sentence) as confirmation that a *palette*
resolution chain is correct, especially when that same chain also feeds
non-text (icon/photo/painterly) content you haven't independently verified.

## What went wrong

Tracing Urban Strike (Mega Drive)'s overlay-tile-bank palette question, a
per-level object-handle table (`$BBC2A`) resolved cleanly through the
project's own already-confirmed tilemap-tileset-link reader
(`resolveTilemapTileset`/`renderTilemapFromRom`), producing a fully
legible rendered screen: real English text ("RIG #3231 / BUILT: ... /
DECOMMISSION DATE: ... / BOUGHT BY MALONE CORP: ...") with 0 out-of-range
cells. This looked like strong confirmation that the resolved "palette
pointer" field was correct — a real, working code path, a real render, a
real oracle, matching this project's usual bar for "confirmed."

It wasn't. The resolved palette pointer turned out to be byte-identical
to the tilemap *header's own file offset* — the render was colouring the
header's own struct fields (width, height, format — small, low-valued
16-bit words) as if they were CRAM colour words, not real palette data.
The render stayed legible anyway, because **text legibility survives
almost any 2+-colour palette**: a letterform's shape comes entirely from
*which pixels share an index* (the tile decode), not from *which RGB
value that index happens to map to*. Two visually-distinct colours —
even two wrong ones — are enough to read a word. This is fundamentally
different from photographic/painterly content (a face, a room, a
landscape), where a wrong palette scrambles perceived shading/shape
boundaries into "confetti" — exactly what happened when the *same style*
of wrong-palette test was tried against non-text tile data in the same
investigation (visibly scrambled, not legible).

## Fix

Don't let a legible text/label render substitute for the project's usual
"unambiguous, recognisable photographic/painterly art" bar
(`crawl`'s pool-room/flight-helmet-class renders, etc.) when validating a
*palette* (as opposed to a *tile/pixel decode*, which text legibility
*does* validate well — the index pattern is real even when the colour
mapping is wrong). If a resolution chain's only available oracle is a
text render, treat the *palette* as still unconfirmed and look for a
second check: read the palette bytes directly and sanity-check them as
plausible colour data (not suspiciously equal to a known non-colour
struct's own field values, not all-zero, not mirroring an unrelated
pointer field elsewhere in the same descriptor), or find a non-text
instance reachable through the same chain to render as a stronger
cross-check.
