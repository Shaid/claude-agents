# A CPU overflow/trap-avoidance instruction's "unchanged destination" is often a concrete, derivable value — not generic undefined behavior

**When it bites:** Porting a divide (or any instruction with a documented
"on overflow, the destination register is left unchanged, no trap" or
similar fixed-overflow-behavior semantic — DIVS.W/DIVU.W on 68000 is the
concrete example, but the same shape shows up on other CPUs' saturating or
overflow-checked instructions) and the overflow case is tempting to treat
as "can't happen for real data" or "undefined, just clamp/wrap it
somehow."

## What went wrong

Powermonger's `$101CA` road rasterizer computes a per-step height-ramp
delta via `DIVS.W` (32-bit dividend, 16-bit divisor, 16-bit quotient). For
realistic height-delta-to-cell-distance ratios (a delta of just a handful
of units over tens of cells), the naturally-scaled dividend (`delta <<
16`) routinely produces a quotient that doesn't fit in a signed 16-bit
word — this isn't a rare edge case, it's the common case whenever the
slope exceeds roughly 0.5 units/cell. A first instinct was to either
silently truncate the quotient to 16 bits (which produces a wrapped,
nonsense slope) or throw/skip (which discards real, intended game
behavior for what's actually a frequent situation).

The 68000 doesn't trap on `DIVS.W`/`DIVU.W` overflow — it sets the V flag
and leaves the destination register **unchanged**. That's not "undefined"
in any meaningful sense: it's exactly whatever was in that register the
instruction *before* the divide. At this specific call site, the
destination had just been set to `deltaHeight << 16` via a `swap`+`clr.w`
sequence immediately preceding the divide — so "unchanged" resolves to a
concrete value: the low word (which the following `ext.l` sign-extends
into the actual per-step delta) is still the 0 that `clr.w` put there.
Net effect: a steep road segment's height ramp doesn't wrap into garbage
and doesn't trap — it simply doesn't ramp at all, staying flat at the
first endpoint's height for the whole segment. This is a real, confirmed,
reproducible game behavior, not an implementation shortcut.

## The general technique

When porting any instruction whose documented overflow/exception behavior
is "destination unchanged" (or similarly "operands unaffected"), don't
stop at "leave it as a TODO" or silently wrap/clamp the mathematical
result. Trace what value the destination register actually held
*immediately before* the instruction executed at that specific call site
— compilers and hand-written assembly routinely set up the destination
register right before a divide/multiply for unrelated reasons (a shift, a
clear, a previous computation), and that setup often makes "unchanged" a
single well-defined, portable value rather than a genuinely unpredictable
one. This turns an "avoid this edge case" instinct into "here's exactly
what real hardware does here," which is usually both correct and cheap to
implement once traced.
