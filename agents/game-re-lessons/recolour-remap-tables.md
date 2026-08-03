# Wrong colours can be correct pixels

**When it bites:** a decode's colours look wrong for a specific character/sprite even though the palette itself checks out elsewhere.

Engines recolour shared sprites at runtime via remap tables — e.g.
middilgard's 48-entry bitplane-mode table, `_ColorReMap`. Don't reject a
decode as wrong just because the palette looks off for one particular
character; check whether a runtime remap explains it first.

**Diagnosing "wrong colour, right shape" vs. "wrong decode": check whether
the SAME target palette index is bad across every candidate palette, not
just the one you tried first.** If a remapped/looked-up palette index
renders as an implausible flat colour (bright magenta, a "reserved" VGA
DAC slot, etc.), don't conclude the remap logic is wrong — dump that exact
RGB triplet from every other candidate palette file in the corpus. If it's
the *same* placeholder value (e.g. literal `RGB(255,0,255)`) in all of
them, the index range is a runtime-patched region no static palette in the
corpus populates (the live game overwrites it per-level/per-monster before
drawing — the same class of mechanism as EOB's `setLevelPalettes`), not a
wrong offset in your decode. Confirmed on Lands of Lore (DOS): VCN
wall-tile and SHP monster-shape colour-table indices resolved to
`RGB(255,0,255)` in the CPS-embedded main palette AND both standalone
`.COL` files found in the corpus — three independent palettes agreeing on
the same placeholder value ruled out "tried the wrong palette" and pointed
straight at "the real colours are patched in at runtime, from a source not
in this static data." Render the confirmed-shape/unconfirmed-colour result
in greyscale rather than either the placeholder colour or nothing — it
publishes what's actually verified (structure) without asserting what
isn't (colour).
