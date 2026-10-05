# Resampling animation curves onto a merged time base needs an explicit monotonicity guard and a zero-length-segment guard

**When it bites:** a decoded animation format stores each component of a
vector channel (quaternion x/y/z/w, position x/y/z) as an *independent*
curve with its **own** keyframe schedule, so exporting a vector track means
resampling all components onto one shared time base — typically the union
of their keyframe times, often densified so a non-linear segment survives a
LINEAR-interpolating consumer. Two things break silently here.

## 1. glTF requires strictly ascending sampler input

An animation sampler's `input` accessor must be strictly increasing.
A merged, densified time base can violate this in ways that never throw:

- the union may already contain the value you prepend (`0`, or a `-0.0`
  stored in the file — note JS `Set`/sort treat `-0` and `0` as equal, which
  saves you here but only by luck);
- densifying a segment can emit a point equal to a knot if the step count
  is computed from a rate rather than clamped;
- a keyframe time that is genuinely out of order in the source data passes
  straight through.

None of these produce an exception, a NaN, or a visibly broken file — they
produce a glTF a strict validator rejects and a lenient viewer renders
subtly wrong. Check it: on Three Hopes' G1A corpus
(`~/Development/chimera`), **63,786 decoded channels, minimum sample time
exactly 0, 0 non-ascending and 0 duplicate consecutive times**. That is a
one-line sweep and it is the only cheap proof the resampler is legal,
especially where no `gltf-validator` is installed.

## 2. The reference implementation probably divides unguarded

Segment evaluation normalises time within a segment as
`r = (t - t[k-1]) / (t[k] - t[k-1])`. Real data contains **zero-length
segments** — a keyframe at `t = 0` (so `t[k] == t[-1] == 0`), or two keys at
the same time. `fmt_g1m`'s `function3` divides here with no guard; ported
literally, one such keyframe poisons an entire channel with `NaN`/`Infinity`
that then propagates into every exported accessor. Force the ratio to 0 when
the span is 0 — the constant term `d` is the correct value there anyway.

## The fix

Whenever you resample onto a merged time base, ship two corpus-wide
assertions alongside the decoder: **0 non-finite values** across every
emitted sample (catches the unguarded divide and anything else numeric), and
**0 non-ascending or duplicate consecutive times** across every emitted
channel (catches the time base). Both are cheap, both are invisible without
being asserted, and the second one is not implied by the first.
