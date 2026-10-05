# An exhaustive disc-I/O call-graph census only proves "no dedicated load exists" — it says nothing about content synthesized from data already loaded for another purpose

**When it bites:** a whole-executable census of every raw-CD-read/disc-load
call site is exhaustive and finds no room-keyed, location-keyed, or
otherwise category-matching load — and that negative is being used to
conclude a whole *content category* doesn't exist at all (e.g. "no
background art", "no cutscene text", "no dialogue"), not just "no dedicated
load path for it exists".

Parasite Eve (PSX, `parasiteeve`): an early investigation into whether the
game has prerendered background art traced all 15 real callers of the raw
disc-read primitives (actor packages, icon variants, boot splash, FMV
setup, a generic UI/dialog loader, a name-randomizer, the `AKAO` audio
streamer) and found none keyed by room/location ID. This was a genuinely
exhaustive, correct answer to "is there a dedicated background-image load
somewhere" — and it is still true. But it was written up as "this game's
data does not store or load a monolithic prerendered 2D background bitmap
anywhere reachable from disc I/O", which reads as (and was later cited as)
a negative on background art existing at all. It doesn't need to: the
game's real background mechanism (a per-actor-package tile-scatter GPU
sprite compositor, see `data-table-stores-prepacked-value-code-census-
misses-it.md`) composites its background entirely from bytes **already
resident in RAM** as part of the ordinary actor-package load (chunk1's
texture pages + chunk3's tile-placement records) — no separate disc read
of any kind occurs or is needed. A census scoped to disc-I/O call sites is
structurally incapable of ever finding a mechanism that needs no I/O call
at all.

**Fix:** when a disc-I/O/file-load census comes back negative for a
content category, state the negative at its true scope — "no *dedicated
load path* for X exists" — and treat "could X be synthesized/composited
entirely from data already loaded for an unrelated purpose (a bigger
container, a per-object/per-package bundle)" as a separate, still-open
question requiring its own check (trace what the already-loaded data's
*other* consumers do with it, not just how it arrived). This generalizes
past backgrounds specifically: any content class you'd naively expect to
have its own load path (music cues, dialogue text, minimaps, UI chrome)
may instead ride inside a container loaded for a different primary purpose
and be assembled from it at render time with zero additional I/O.

**The same trap applies one layer down, to a buffer-*reference* census
instead of a disc-I/O-*call* census.** Millennium 2.2 (Amiga, `methanoid`):
an earlier session's "no static picture" verdict for the game's confirmed
live 320x200x4bpl screen buffer rested on a whole-file raw-longword scan
for the buffer's own pointer (`$68806`) that found "zero references
anywhere else... beyond [the allocation] routine and its own `BltClear`
calls" — but that scan was silently scoped to `DoIO`-destination operands
specifically (checking whether any track-read wrote disk bytes straight
into the buffer), not to *every* reference to the pointer. A later session
found Millennium 2.2 shares a byte-identical hidden compressed-art codec
with its own developer-lineage sibling Deuteros (see
`game-re-corpora/methanoid.md`), whose renderer reads `$68806.l` directly
and composites decoded RLE images into it via ordinary row/column
arithmetic — a real, `movea.l`-based reference the DoIO-scoped census could
never have matched. An unscoped raw-longword scan for the same address
found 16 hits, not zero. The general shape is identical to the disc-I/O
case above (a census answers only the specific access-mechanism it
actually checked, never "does anything touch this at all"), just applied
to "does anything write into this buffer" instead of "is this content
loaded from disc" — before trusting a "zero references" verdict for any
buffer/pointer, state which instruction *forms* the scan covered (a raw
literal-address scan already catches most forms, but a census built around
one specific consumer idiom — like `DoIO`'s `io_Data` field — will not).
