# A sibling format sharing a field's position/role doesn't mean it shares that field's numeric-scale convention

**When it bites:** extending an already-confirmed decoder for one format to
a structurally similar sibling format (same container architecture, same
field roles, ported across platforms or engine generations) that also
reuses a shared rendering/interpretation function — specifically a numeric
field whose *hardware or platform-specific scale* (a fixed-point divisor, a
"what raw value equals 1.0/100%/max" convention) was hardcoded for the
original format. A render comes out over- or under-saturated in a way that
"looks like a colour bug" rather than an obviously wrong value.

## What went wrong

Confirmed on Dragon's Crown (PS3, `vanille`), decoding `FMBS` — the PS3
sibling of Odin Sphere/Grim Grimoire's PS2 `FMBP` sprite-model format. Both
formats store the same field in the same role and position: a per-vertex
RGBA colour byte used to modulate a sampled texture pixel. `FMBP`'s
rasterizer had one already-confirmed, byte-exact-verified convention for
this field: the PS2 Graphics Synthesizer's own vertex-colour scale, where
`0x80 == 1.0` (not `0xFF`) — a well-documented PS2 hardware quirk, correctly
built into the shared `rasterize()` helper as a hardcoded `/128` divisor.

`FMBS` uses the *same byte position and role* for its colour field — but a
different hardware, since PS3 dropped the PS2 GS entirely. Its real
convention is the ordinary `0xFF == 1.0`. Reusing the shared rasterizer
unmodified (still dividing by 128) over-brightened every `FMBS` render: a
fully-opaque vertex (raw alpha `0xFF`) computed to `ca = 255/128 ≈ 1.992`
instead of `1.0`, silently clamping through the pipeline. On `Barrel00` this
just looked like "washed out, oddly bright" — easy to dismiss as a texture
issue. On `Flask00` it was decisive: a real gray glass-shard texture
(sampled value ~130) multiplied by `1.992` and clamped, rendering as a
**solid pure-white square** (mean opaque RGB exactly `255,255,255`) —
because the underlying pixel data was genuinely correct, this let the bug
mimic "wrong page/UV binding" or "blank/missing texture" at a glance.

## The tell

An exact/near-exact clamp signature — mean or peak channel value landing
*precisely* at the format's max (255, or a suspiciously round multiple) —
is a scale-mismatch tell, not proof of missing/wrong source data. Before
chasing a UV or texture-binding bug, crop and view the *raw source texture*
region actually being sampled: if it's real, non-blank art (confirmed here
by cropping the FTX atlas directly), the bug is downstream in the colour
math, not in what's being read.

## The fix, generalized

Treat a numeric field's *scale/unit convention* as an independent axis from
its position and role — same as byte order
(`port-wide-byte-order-convention-not-uniform-across-formats.md`) and field
role (`header-field-role-not-transitive-across-sibling-format.md`) already
are in this project's lesson set. A shared container architecture and
identical field layout only tell you *where* the data is and *what it
represents*; the original hardware's own value-to-unit mapping (PS2 GS's
`0x80` idiom, a fixed-point Q-format, a DAC's non-linear curve) is a
property of the platform that produced it, and a platform-ported sibling
format needs its own convention re-derived, not inherited. The practical
fix here was making the shared `rasterize()` helper take the divisor as an
explicit parameter (default matching the original format) rather than a
hardcoded literal, so each sibling format states its own convention at the
call site instead of silently reusing whichever one was confirmed first.
