# An unknown opcode/type value can select a different *kind* of resource, not a variant of the same one

**When it bites:** a format has a small enum (opcode, type tag, mode byte)
whose known values all select variants of one thing — different channel
combinations of a bone track, different pixel depths of a sprite, different
field sets of a record — and real data contains an extra value your
reference decoder doesn't know (it prints "unknown opcode", or your own
table has no row for it). The instinct is to slot it into the same family
and hunt for which combination of the *same* channels it selects. It may
not be in that family at all.

## What went wrong

G1A animation (`_A1G`, Fire Emblem Warriors: Three Hopes,
`~/Development/chimera`). The community reference decoder (`fmt_g1m`'s
`processG1A`) knows opcodes `1/2/4/6/8`, each selecting some subset of
{scale, rotation, translation} for a bone. Real data also contains opcode
`0x66` — in **227 of 583 resources, 39% of the corpus** — which the
reference simply prints `"Unknown g1a opcode"` for and skips.

It is not a bone track with an exotic channel set. It is a **camera**: the
9 components are eye position (3), look-at target (3), roll, field of view,
and a constant. Its files carry `boneInfoCount == 1`, `boneMaxId == 0`, and
`boneId == 0` in 227/227 — a "skeleton" of one nameless bone, which is what
a free camera looks like when it is squeezed into a skeletal container.

## What settled it, cheaply

A **per-component value-range census** over the whole corpus, before any
attempt to trace consuming code:

| Comp | Range | Reading |
|---|---|---|
| 0,1,2 | X ±1,235 · Y **34 … 1,846** · Z ±1,867 | a world-space point; Y never negative = height above ground |
| 3,4,5 | same magnitude scale, Y tracks comp 1 | a *second* world-space point |
| 6 | −0.455 … 0.382 | a small signed angle — radians |
| 7 | 0.051 … 1.325, median **0.661** | 0.661 rad = 37.9°, a camera FOV |
| 8 | exactly 1.0 in 227/227 | a constant |

Nothing there fits "another bone TRS". Two same-scale position triples plus
two radian-ranged scalars is a camera and essentially nothing else. Three
independent signals then partitioned the corpus identically with 0
deviations — a header `animType` enum, the opcode, and whether the file
shares a package with a model — which is what upgraded the reading from
plausible to confirmed.

## The fix

Before assuming an unrecognised enum value is a variant, decode its payload
under the format's *generic* container rules (which usually still apply —
here the offset/keyframe grammar was unchanged) and **census the value
ranges of each field across the whole corpus**. Sign, magnitude scale,
always-positive-ness, and "does this look like radians" separate position
from direction from angle from flag far faster than tracing a consumer, and
they work with no executable at all. Then look for an independent
partitioning signal (a header enum, a container-level property) that agrees
with the split — if the unknown value really is a different kind of
resource, something *else* in the format almost always knows that too.
