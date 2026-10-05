# A shared engine family's "index 0 = blank placeholder" tile-bank convention isn't universal across every sibling title

**When it bites:** porting a confirmed tile-bank/asset-bank indexing
convention from one title in a shared engine family to a sibling title's
own, differently-shaped tile-bank container, especially when several
sibling titles already agree on the convention and the new one is assumed
to follow suit without checking its own addressing arithmetic first.

Across this project's whole SSI Gold Box GLIB/DaxFile corpus (Pool of
Radiance, Curse of the Azure Bonds, Secret of the Silver Blades, Champions
of Krynn, and others), every confirmed WALLDEF-style tile bank reserves
index 0 as a blank/placeholder slot (`buildTileBank`/
`buildWallSpecificTileBank` in `tools/poolofradiance/amiga/walldef.ts` /
`tools/shared/goldbox-walltiles.ts` all prepend one), with real tile content
starting at index 1. It would be easy to assume this holds for any new
tile-bank format found in a sibling title from the same family.

Confirmed false on Death Knights of Krynn's `8x8d1.daa` (a BIG-ENDIAN
sibling container to the corpus's own "DOS DaxFile" format, cracked via a
`re-oracle` escalation — see `individually-failed-fixes-may-combine-cleanly.md`):
its own addressing is a "quarters" scheme where the raw WALLDEF view-cell
byte's full 0-255 range is split by its own high 2 bits into 4 sibling
`.DAA` entries (wall id `W`, `W+20`, `W+40`, `W+60`), each holding exactly
64 tiles — `slot = idx >> 6`, `tile = idx & 63`. This exactly and
completely covers the byte's whole range with **no reserved slot at
all** — index 0 is a real tile (the first quarter's own first tile), not a
placeholder. Assuming the corpus-wide convention here would have produced
an off-by-one tile bank for every wall in the title, silently rendering
each real tile one slot early while treating tile 0's real content as
"blank."

The check: before reusing a sibling title's tile-bank *addressing*
convention (as opposed to its *container/codec*, which can transfer
completely unchanged — see the many GLIB-titles' shared-format entries in
`game-re-corpora/crawl.md`), verify the new format's own byte-range
coverage arithmetic from scratch. If a byte's full addressable range (e.g.
0-255) divides evenly and completely across the confirmed real content with
no leftover distinguished value, that's itself strong evidence there is no
reserved placeholder in this particular format — don't import one anyway
just because sibling titles have one.

See also `first-usable-fallback-assumes-reserved-slot-is-empty.md` for the
same underlying non-transitivity ("a sibling format's reserved/conventional
slot isn't guaranteed to follow the convention you've already confirmed
elsewhere") showing up as a *content-emptiness* assumption in a fallback
selection heuristic, rather than as addressing arithmetic.
