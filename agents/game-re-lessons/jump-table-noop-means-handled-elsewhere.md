# A jump-table no-op case means "not handled here", not "not handled"

**When it bites:** a dispatch/jump-table case branches straight to a no-op or function epilogue, and — this is the part that's easy to miss — multiple well-formed, corpus-visible records reference that case, not just one or two stray/degenerate ones.

Three separate passes (two full sessions plus a first sub-attempt inside the
session that finally cracked it) all found a generic resource-loader's
5-case jump table where one case (`cmd=10`) branched straight to a no-op,
and all three concluded "this command does nothing, skip it" — when in
fact `cmd=10` was the single most important case in the whole table: it
marked resource records consumed by a **separate, dedicated reader routine**
reached through completely different code, never through this dispatcher at
all. The dispatcher's no-op branch exists specifically *because* something
else already claimed that job — dispatch tables in real engines commonly
have exactly this shape (a generic loader that handles the common cases and
explicitly no-ops the ones a specialized subsystem owns), and a no-op is
indistinguishable, from the dispatcher's code alone, from "this case is
truly dead."

The tell was sitting in already-collected data across all three passes: a
struct/catalog scan built for an unrelated purpose had already surfaced
39-50 real, well-formed records keyed to the "no-op" case, several with
suspiciously clean, purposeful-looking field products (e.g. a
`width * height` computing to exactly one full screen's worth of cells) —
and each pass looked right at those records and moved on, because the
*dispatcher's own code* said "nothing to see here."

**The fix, as a general rule:** when a dispatch table's "do nothing" case
has *multiple* real, structurally well-formed instances in the corpus (not
1-2 stray/degenerate outliers), that population size is itself evidence
against "unused" — go looking for a second, independent consumer of the
same descriptor/pointer shape elsewhere in the code, rather than trusting
that the dispatcher you already found is the only reader. Concretely: grep
for other code that reads the *same relative struct offsets* (the pointer
field, the size field) outside the dispatcher's own call graph; a second
routine doing so, especially one with its own jump table on a different
field of the same struct (here: a `format` field the generic loader never
looked at, read through a base pointer offset by a fixed constant from the
one the dispatcher used), is the real reader. This generalizes past
compression/graphics loaders to any opcode/command-dispatch structure in
any engine.

Found in `~/Development/strike` (Genesis/Mega Drive Strike engine
tilemap/nametable format) — see `docs/strike-megadrive-tilemap.md`. The
second reader was located by fingerprinting a distinctive instruction slice
from a confirmed sibling routine and searching for a corpus-unique
byte-exact match in the other game's ROM (see
`cross-disassembly-fingerprint-false-positive.md` for the uniqueness
requirement that made that search trustworthy).
