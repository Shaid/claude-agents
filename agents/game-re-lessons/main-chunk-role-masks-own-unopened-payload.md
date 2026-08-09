# A chunk already assigned a container-level role can still hide the missing sub-format inside its own body

**When it bites:** hunting for a still-missing sub-format (vertex/UV/index
data, a text table, an animation curve — anything a survey pass has
repeatedly failed to find) nested inside an already-solved container, and
every survey pass so far has scoped itself to "the *other* chunk types" —
because the largest/first chunk in the chain already has a name and a role
assigned (e.g. "this tag marks the record itself," "this is the character
wrapper"), its own un-opened payload bytes get implicitly excluded from
every subsequent search, pass after pass, without anyone noticing the
exclusion.

Valkyrie Profile 2 (PS2)'s `"FPS\0"`-tagged chunk-chain records are
character/skeleton bundles: `walkFpsChunks` correctly reports an `"FPS\0"`
chunk with a real byte `length` (tens to hundreds of KB — the largest
region in every record), followed by an `IDOM` bone-palette chunk and a
handful of small VFX/attachment chunk types. Two separate survey passes
each explicitly targeted "the chunk types nobody's classified yet" —
first `FPS\0`'s own 8 *minor* chunk types, then (after the same trap
recurred one level up) `RMAC`'s 13 minor chunk types — and both correctly,
rigorously ruled out every type they checked as VFX/lighting parameter
blocks, not geometry. Both passes were real, well-evidenced negatives.
Neither ever opened the `FPS\0` chunk's *own* body, because by
construction "minor chunk types" meant "everything except `FPS\0`
itself" — that chunk already had a role ("the character record wrapper")
assigned from the very first pass that discovered the chunk-chain
container, and nobody revisited whether its own payload bytes, not just
its wrapper role, might also be the answer. They were: the `FPS\0` body
turned out to be a literal, uncompressed PS2 VIF1 display packet —
hardware `VIFcode`s with vertex position/normal/UV/colour arrays inline
as `UNPACK` payloads, no disassembly needed to find it, just an actual
hexdump of the first few hundred bytes that had simply never been taken
(the tell was visible immediately: a valid `UNPACK V4-16` VIFcode opcode
pattern at byte offset 0x70 of the very first sample anyone would have
looked at).

Assigning a chunk/record a container-level role (it marks a character, it
wraps a resource, it's "the thing itself" as opposed to its metadata)
answers a *structural* question (how do I find and bound this record?) —
it says nothing about whether that same chunk's own payload also answers
a completely different, still-open *content* question (where's the
geometry/text/animation data?). Before concluding a corpus-wide survey of
"the unclassified sub-chunk types" has exhausted a container, explicitly
check: has anyone ever hexdumped and read the *main/already-named* chunk's
own un-opened bytes as a candidate host for the missing data, or has every
pass — including this one — silently scoped itself to "everything but
that one"? A role name is not a content classification.
