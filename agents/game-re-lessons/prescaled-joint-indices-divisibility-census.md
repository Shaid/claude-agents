# Stored vertex joint indices may be pre-scaled (slot x stride) — a corpus divisibility census is a cheap, decisive test

**When it bites:** any skinned-mesh exporter that reads a vertex's bone/joint
index attribute and uses the value directly as a palette/skin slot —
especially when an out-of-range gate (`if (idx < paletteSize)`) is silently
dropping some values, or when a reference implementation divides the index
by a constant anywhere (`bPID /= 3`, `jointMap[3*j] = ...`), even in a code
path you think is unrelated.

## What went wrong

Koei Tecmo G1M (chimera — FE3H, FE Warriors, Three Hopes) stores each rigid
vertex's bone index as **palette slot x 3** (a matrix-byte-offset-style
engine convention). The shared exporter read the raw value as the slot for
three full game corpora: values `3..paletteSize-1` bound the *wrong* slot,
larger values were dropped by the range gate and fell back to slot 0. This
shipped invisibly because every palette composite is identity at bind pose
(`world[bone] x IBM = I`), so renders, Playwright screenshots and
`gltf-validator` all pass regardless of joint assignment — the third live
instance of `bind-pose-render-blind-to-joints-index-space-bug.md` in one
project. The observed value shapes even looked self-consistent: small ints,
mostly "in range" for big palettes.

## The decisive test (minutes of compute)

For every submesh, collect the distinct index values and check:

1. all values are multiples of a candidate stride N, and
2. `max(values) / N == paletteSize - 1` (or close).

FE3H: **1,369/1,369 rigid lod-0 submeshes** passed for N=3 with 0
exceptions — probability by chance ~(1/3)^distinct per submesh, i.e. zero.
The census also *discriminated* index spaces: the same game's cloth-type
submeshes failed it (614/618 not divisible), correctly flagging their
indices as direct ordinals into a different table (see
`cloth-submesh-repurposes-vertex-attributes.md`). Cross-checks: an FE
Warriors u16 sample (values 0,3,...,309 against a 104-slot palette) and the
reference implementation's own bone map built as `jointMap[3*j] =
palette[j]`.

Rule: before trusting raw joint indices, run the divisibility census once
per corpus, and grep any reference decoder for a division/stride on its
index path — a `/= 3` in its cloth branch is evidence about its rigid
branch too.
