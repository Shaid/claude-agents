# Wrong colours can be correct pixels

**When it bites:** a decode's colours look wrong for a specific character/sprite even though the palette itself checks out elsewhere.

Engines recolour shared sprites at runtime via remap tables — e.g.
middilgard's 48-entry bitplane-mode table, `_ColorReMap`. Don't reject a
decode as wrong just because the palette looks off for one particular
character; check whether a runtime remap explains it first.
