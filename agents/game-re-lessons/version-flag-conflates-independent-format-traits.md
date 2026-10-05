# A reference decoder's single "is new version" boolean can conflate two independent format traits — an intermediate version splits them, and no value of the boolean is correct

**When it bites:** you're decoding a format version your reference
implementation (or the community binary template it came from) never saw,
and the port handles versions with one boolean — `isNewVersion`,
`version >= N`, `if (v == "0500")`. Especially when a project doc records
that the new version "falls through the existing path with no code change —
and it works."

A format that changed twice between the two versions your reference author
had samples of will have both changes gated behind one flag, because from
those two samples the changes are indistinguishable. If an intermediate
version exists that took only *one* of the changes, the boolean cannot
express it: `false` is wrong about trait A, `true` is wrong about trait B.
The port doesn't crash — it reads a fixed distance off, which stays
structurally well-formed and mostly decodes.

## What happened

G2A animation (Koei Tecmo, `chimera`). The reference (`fmt_g1m.py`) and the
`.bt` template only ever saw `"0300"` and `"0500"`, between which **two
independent things** changed: the bone-ID bitfield widened (10-bit ID /
18-bit offset → 8-bit / 20-bit) and the header grew a trailing `reserved`
u32 (28 → 32 bytes). Both were modelled as one `isNewVersion` flag.

FE Warriors: Three Hopes ships `"0400"`: **old bitfield widths, new 32-byte
header.** The project had documented it as decoding "with zero code
changes", falling through to the `"0300"` path. It did not work:

- every spline read started 4 bytes early;
- 110 of 4,569 blocks overran the buffer and decoded to nothing;
- the bone-info table was read one slot early, shifting every `boneId` down
  by exactly 1 (every clip cluster's recorded `maxBoneId` was off by one:
  80→81, 924→925, 265→266);
- many tracks decoded to **zero keyframe samples**.

The last symptom is why this cost a whole extra investigation: missing
samples and shifted bone IDs presented as a *skeleton-pairing* problem, and
a prior pass spent its effort hunting for a missing skeleton rather than
questioning the decoder.

## The cheap test: decompose the flag, then score the cross-product

Don't ask "is this version old or new". Ask **which independent traits the
flag is bundling**, then test every combination against structural
invariants that the corpus can settle on its own:

1. **A block-size identity pins header size independently of everything
   else.** `declaredSize == headerSize + sum(sectionSizes) + count*stride`
   gave `headerSize == 32` for **4,569/4,569** blocks, 0 deviations — before
   any bitfield question was touched. (The same identity had pinned 28 for
   `"0300"` and 32 for `"0500"`.)
2. **Score each combination on independent invariants.** Here, 2 header
   sizes × 2 bitfield widths, scored on: spline offsets landing inside the
   timing section, `firstDataIndex` inside `entryCount`, and the spline walk
   covering the timing section exactly (no slack, no overrun):

   | Header | Widths | Bad offsets | Bad indices | Section exactly covered |
   |---|---|---|---|---|
   | 28 | old *(what the code did)* | 7,229 | 385,120 | 58/4,569 |
   | **32** | **old** | **0** | **0** | **4,569/4,569** |
   | 32 | new | 227,376 | 56,116 | 292/4,569 |
   | 28 | new | 222,929 | 70,185 | 38/4,569 |

   One combination clean on every metric with zero deviations; the other
   three failing on thousands. No external oracle needed.
3. **Express the traits separately in the fix** — here `hasReservedField`
   (`"0400"`||`"0500"`) and `isNewVersion` (`"0500"` only). Check that the
   split is a provable no-op for the versions the sibling games use before
   touching a decoder they share (for `"0300"`/`"0500"`, the new predicate
   evaluates to exactly what the old one did — see
   `shared-decoder-behavior-is-a-cross-platform-contract.md`).

## A free size-based smell for this class of bug

Where a decoder densely samples curves, **output size is a correctness
signal**. The pre-fix export was 19 MB for 1,675 clips; correct decoding of
the same clips is roughly 10x that, because the bug had been suppressing
keyframe samples. Suspiciously *small* output — especially output that got
smaller than a sibling game's per-clip average — is worth a second look
before it gets recorded as a shipped result.

Sibling lesson: `format-field-width-unexercised-by-first-corpus.md` covers
the case where the version selector picks a *wrong* value because the first
corpus only ever exercised one; this is the sharper case where the selector
is under-*modelled* and no value of it is right.
