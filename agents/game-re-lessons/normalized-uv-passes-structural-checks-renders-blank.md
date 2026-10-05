# A normalized-[0,1]-vs-raw-pixel-space UV convention swap passes every structural check and renders completely blank

**When it bites:** porting an already-solved multi-platform sprite/mesh
format's texture-coordinate (UV) field to a new platform port, where every
structural/count/range invariant passes cleanly on the first attempt
(correct header layout, correct section strides, every index in range, 0
skipped/out-of-range parts) — yet the rendered output is uniformly blank,
solid-colour, or otherwise visually degenerate. Check whether the new
platform stores UV as normalized `[0,1]` texture-space floats rather than
the sibling platforms' raw pixel/texel-space floats (or vice versa) before
suspecting the container/record decode itself.

Confirmed on 13 Sentinels: Aegis Rim (Switch)'s `FMBS` sprite-model format
(`vanille` corpus). The Vanillaware "paper-doll" model family was already
solved on three prior platforms (PS2 `FMBP`, PS3 `FMBS`, Wii `FMBS`), all of
which store `uv` fan coordinates as raw pixel-space `f32` values (e.g.
`[512.0, 340.5]` against a 1024px-wide texture page). Porting the format to
Switch, every header/section/record structural check passed on the first
attempt — 436/436 files matched the expected `headerSize`, every section's
byte length divided out to `count * stride` with 0 exceptions, every part's
`page`/`uv`/`colour`/`xy` index landed in range across 120,546 sampled
parts. A render attempt reported entirely plausible statistics too: correct
output dimensions, a non-zero drawn-part count, 0 skipped parts (meaning
every part resolved a valid page/texture). The rendered PNG was
**completely blank white**.

The cause: Switch stores `uv` fan coordinates as normalized `[0,1]`
texture-space floats relative to the sampled page's own dimensions, not raw
pixel space. A rasterizer's nearest-neighbor texture sampler that clamps
`u,v` into `[0, textureWidth)`/`[0, textureHeight)` before indexing treats
every `u,v <= 1.0` as pixel `(0,0)` or `(1,1)` — the texture's extreme
top-left corner — regardless of the part's real intended source rectangle.
On the sampled textures that corner happened to be transparent/background,
so every part sampled the same blank pixel and the whole render came out
uniformly empty, with **no error, no out-of-range value, and no failed
invariant anywhere in the pipeline** to flag it. Confirmed via a
whole-corpus range check (0/100 files sampled had any uv fan corner value
outside `[0,1]`, versus prior platforms whose uv values routinely exceed
1.0 by two to three orders of magnitude) and fixed by scaling `u` by the
sampled page's `width` and `v` by its `height` before rasterizing, gated on
the new platform's layout tag so every prior platform's behaviour is
unaffected.

**The general lesson:** a coordinate-space/scale *convention* (normalized
vs. raw, texel-space vs. UV-space, a different fixed-point Q-format) is
invisible to every structural check a format decoder normally runs —
header shape, section strides, index-in-range censuses — because the
numeric *values themselves* are still perfectly well-formed floats/ints in
whatever range the check expects. It only surfaces as degenerate *visual*
output, and specifically as a **uniform** degeneracy (solid blank, solid
one colour, or a single repeated texel) rather than scrambled/noisy
garbage — because every sample collapses toward the same clamped corner
regardless of the part's real position. This is exactly the class of bug
the method's "render at least one asset and inspect real pixels before
calling anything confirmed" rule exists to catch: a purely
structural/numeric verification pass reports 100% success here. When
porting an already-solved format's coordinate field to a new platform and
the render comes out uniformly blank/flat despite clean structural stats,
range-check the coordinate values against `[0,1]` (or against the known
texture dimensions) as the first diagnostic step, before re-auditing the
record layout itself.
