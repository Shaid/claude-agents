# A sequel sharing a container format and an `IMGx`-style codec *naming family* with its predecessor can still use a materially different byte grammar for that codec

**When it bites:** a sequel/later title in a series shares an
already-solved container format with an earlier game (same directory/header
shape, byte-exact), and its content codec has the same family-prefix naming
convention (`IMG1`/`IMG2` in one game, `IMG3`/`IMG4` in another) — tempting
you to apply the earlier game's already-confirmed decoder directly rather
than re-verifying the byte grammar for the new title. Also fires when the
most-cited/primary community reference for the exact game+file explicitly
marks that content as "not yet decoded"/"unknown format" — that's a signal
to search for a *second*, less-prominent community source, not to conclude
no answer exists.

Confirmed on Dungeon Master II: Skullkeep (Amiga, `crawl` project). DM1 and
Chaos Strikes Back (both Amiga, same engine, same data-file container
format) use the `IMG1`/`IMG2` pixel codec: 4bpp nibble-RLE, no local
palette. DM2's `GRAPHICS.DAT` uses the identical outer container and, by
naming-family resemblance alone, looked like it should decode the same way.
Applying `IMG1`'s decoder to real `GRAPHICS.DAT` bytes produced visual
garbage — flat black rectangles and vertical-stripe noise, nothing like
DM1/CSB's immediately-recognizable output on the same decoder. The
project's own primary community-docs source (the "dmweb" Dungeon Master
Encyclopaedia) confirmed *why*, but not *how*: its own per-file item-type
table for exactly this file marks **~4,521 of 4,630 items as `RAW1`** — its
own definition of `RAW1` being "not yet decoded." The most-authoritative
source for the exact game and exact file explicitly had no answer.

A **second, secondary fan-analysis source** ("Dungeon Master II Data Files
Notes," found by a follow-up search rather than stopping at the primary
docs' negative) named the real codec: `IMG3`(LE)/`IMG4`(BE), a 4bpp
nibble-RLE stream with a **6-nibble local palette prefix** and a **different
control-nibble grammar** than `IMG1` (bit 3 = single/multi run, bits 2-0 =
a colour selector that can mean "local palette index," "copy from the line
above," or "absolute colour via an extra nibble" depending on value — none
of which `IMG1`'s grammar has). Implementing this from the secondary
source and applying it to `GRAPHICS.DAT` gave 98.9% of image-shaped items
decoding cleanly with unmistakable real content (multi-language UI text,
weapon/wall-texture art) — confirming both the new codec and the primary
docs' own "not yet decoded" admission for this specific file.

**The generalizable move**: a shared container format across a series
(even byte-exact) is evidence about *packaging*, not about the *content
codec* inside it — a sequel can, and did here, ship an incremented-name
sibling codec (`IMG1`→`IMG3`/`IMG4`) with a genuinely different bitstream
grammar, not just a header/palette-size tweak. Render the earlier game's
decoder against the new title's real bytes before trusting it — garbage
output (not a parse error; nibble-RLE codecs rarely bounds-check
themselves, see `rle-decode-succeeds-on-garbage.md`) is real, cheap
evidence of a grammar mismatch, and cheaper to get than reading a full
spec first. And when the single most-cited community reference for a
game/file explicitly flags it as "unknown"/"not yet decoded" rather than
being silent about it, that flag is itself worth searching around — a
smaller, less-visible fan-analysis source may have solved exactly the gap
the primary reference names.
