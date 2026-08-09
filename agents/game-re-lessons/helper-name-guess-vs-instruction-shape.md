# A helper function's usage-context-guessed behavior can be a completely different algorithm — check its own instruction shape, not just its call site

**When it bites:** a small, previously-disassembled-but-not-fully-traced
helper function has a documented behavior that was inferred from *how
it's called* (its argument, its position in a larger formula, a
plausible-sounding name someone gave it) rather than from reading its own
instruction sequence end to end — especially language like "approximately
X" or "roughly computes Y" in an existing doc.

Confirmed on nicodemus/Phantasie I's combat damage formula
(`scripting-engine.md` §7.2a): a helper called as `roundedHalf(RollPercent())`
— fed a `0..100` roll, its result multiplied into a damage calculation —
was documented by a prior pass as "approximately half the roll, with some
rounding-correction arithmetic" purely from the name and the surrounding
formula's shape (a value that gets scaled down before being multiplied
into damage looks like it should be "the roll, halved"). A full
instruction-level trace this pass showed something structurally
unrelated: an initial estimate `⌊n/2⌋`, then a loop computing
`x' = ⌊(x + n/x) / 2⌋` (via the CPU's native signed divide) and updating
`x ← x'` **until `|x_prev − x'| ≤ 1`** — the textbook shape of
**Newton's-method integer square root**, not a rounding/halving
operation at all. Hand-simulated against two concrete inputs
(`roundedHalf(100) = 10 = √100` exactly; `roundedHalf(50) = 7 = ⌊√50⌋`)
confirmed the algorithm, and it also surfaced a real, faithfully-
preservable original-game quirk the "roughly half" framing could never
have predicted: input `n = 1` returns `0` (not the mathematically
correct `1`) because the initial estimate `⌊1/2⌋ = 0` trips an early-exit
branch before the Newton loop ever runs. The practical stakes are real,
not cosmetic: `roundedHalf(roll)` ranges `0..10` under the true
algorithm versus `0..50` under the "roll/2" guess — an implementation
built on the wrong guess would produce a damage formula with roughly 5×
too much variance, silently, with no error or crash to flag it.

**The tell, generalizable to any CPU/ISA:** a loop containing a divide
instruction whose result feeds back into computing the *next* iteration's
divisor, gated by a small-delta convergence check (`|prev − new| <= 1` or
similar) rather than a fixed iteration count, is a strong signature for
Newton's-method (or a close relative) — worth checking for *before*
accepting a context-plausible name/description for what the helper
"roughly" does.

**Fix:** before writing up or reusing any helper's behavior — even one
already labeled with a plausible name from a prior pass, even one whose
context (what calls it, what its result feeds into) suggests an obvious
guess — trace its actual instructions end to end and, where the shape is
non-trivial (a loop, more than 2-3 arithmetic ops), hand-simulate at
least one concrete input against the traced algorithm rather than the
guessed one. A `≈`/"approximately" qualifier already sitting in a doc is
a signal nobody closed this loop yet, not evidence the guess is close
enough.
