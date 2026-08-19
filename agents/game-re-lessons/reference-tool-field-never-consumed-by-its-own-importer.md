# A fan tool's reader-side field decode is unverified if that tool's own importer/consumer never actually reads the field

**When it bites:** porting a per-field decode *formula* (not just a struct
layout/offset) from a community reverse-engineering tool's reader — a
normal/tangent/color byte-unpack, a fixed-point scale, a bit-packing
scheme — especially one that parses without throwing and produces
plausible-looking output (right value range, no crash). Before trusting the
formula, check whether the *same tool's own downstream consumer* (its
Blender importer, its renderer, its exporter) actually uses that decoded
field for anything visible.

## What went wrong

Porting PlatinumGames' `WMB3` mesh format (NieR:Automata PC,
`~/Development/flower`) from two independent, real, NieR:Automata-specific
open-source Blender importer/exporter projects: both decode a per-vertex
normal byte as `byte * 2 / 255` — an **unsigned** `[0, 2]` range that can
never go negative, clearly wrong for something meant to represent a
direction. Both tools' *struct-parsing* code is otherwise trustworthy (two
independent projects agree on every other field byte-for-byte). But neither
tool's own Blender *importer* ever reads `.normalX`/`.normalY`/`.normalZ`
anywhere in its import code — Blender's own auto-computed face normals are
used instead, with the imported model's normals only ever *flipped*
(winding-corrected), never *set* from the parsed byte values. The formula
was never exercised against a real "does this look right" check by the
people who wrote it, because their own tool doesn't actually need it to
work.

Caught only by reading real corpus vertex data directly and computing
vector magnitude for both the literal reference formula and a standard
signed-byte reading (`byte / 127.5 - 1`, algebraically the same formula
*with* the `-1` offset the reference tools omit): average magnitude
**1.0000246** across 2,281 real vertices with the offset, vs. the reference
formula's own ~1.5-2.0 average for the same data. The offset formula is
correct; the reference tools' literal code was not.

## The fix

A fan tool's field-level decode formula earns real trust from two
independent, structurally-agreeing sources — but that's trust in the
*struct layout* (what bytes exist, where), not automatically in every
*formula* applied to those bytes. Before porting a specific formula (as
opposed to just an offset/stride), check whether the tool's own downstream
consumer code actually reads and uses the decoded field for something a
human would have visually verified (rendering, export round-trip,
comparison against a reference image). If the consumer ignores the field
entirely — computes something else instead, or only uses it for a
non-critical adjustment — treat the formula as **unfalsified, not
verified**, and confirm it independently against a real invariant specific
to what the field represents (unit-length for a normal, a valid color
range, a plausible UV range) before shipping it. This is a sharper,
domain-general version of the mechanism in
`reader-side-may-still-be-export-target-math.md` (which is about a *file's*
reader/exporter classification not predicting whether its math is
hardware-accurate) — here the tell isn't which file a formula lives in,
it's whether the tool's *own pipeline* ever exercises the specific field at
all.
