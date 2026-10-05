# Porting Python's `//` to JS/TS `/` turns an exact array length into a silent fraction, with no type error

**When it bites:** porting a Python reference decoder/tool's formula for an
array length, record count, or index derived from a **pointer/offset gap**
(`count = (nextPtr - ptr) // recordSize`) to JavaScript/TypeScript, where
Python's `//` (floor/integer division) becomes a plain `/` in the port. JS
has no separate integer type, so this doesn't throw or warn — it just
produces a fractional number (e.g. `298.5`) that silently propagates.

Confirmed on Parasite Eve II (PSX, `~/Development/parasite`)'s TMD model
format: the reference Python (`pkg_model.py`, `GabeRealB/parasite-eve-2-decomp`)
computes `vertex_count = (norms - verts) // 8` and `normal_count = (stream_va
- norms) // 8` — a gap between two pointer fields, in bytes, divided down to
an element count. Ported straight as `(norms - verts) / 8` in TS, a debug
print showed `normalCount: 298.5` for a real model (the true gap wasn't an
exact multiple of 8 — a small amount of intentional or incidental slack
before the stream, which Python's `//` truncates away exactly as the format
intends). The bug is invisible in most consumers: a loop written as
`for (let i = 0; i < count; i++)` silently runs one extra iteration
(`Math.ceil` behavior for a non-integer bound), reading one array-length's
worth of garbage past the real data — no exception, no NaN, no obviously
wrong output shape, just one extra (or, depending on the loop form, one
fewer) element than the reference decoder produces.

**The fix**: every direct transliteration of a Python `//` needs an explicit
`Math.floor(...)` in the port, not a bare `/`. Grep the reference source for
every `//` before considering a numeric port complete, and treat any
computed "count"/"length"/"index" value that *could* end up non-integer
(anything derived from a gap or ratio, as opposed to a field read directly
off disk) as a place this needs checking. A quick sanity habit that catches
it fast: log a computed count during development and eyeball whether it's a
whole number — Python's own `//` gives no such visible tell since the
result is already an int, so this class of bug only shows up on the JS/TS
side of a port.

This is a different failure mode from `c-integer-wraparound-vs-js-doubles.md`
(that one is about *wraparound* at 2^32 during chained arithmetic; this one
is about *truncation direction* in a single division, and bites even for
small values with no overflow risk at all).
