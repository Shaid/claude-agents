# A dispatch table's N distinct target addresses can be N entry points into ONE shared routine, not N independent handlers

**When it bites:** a jump/dispatch table has several different index values
resolving to several different, non-identical target addresses, and the
natural next step is to treat each distinct address as a separate handler
(a separate screen, state, or behavior) worth investigating independently.

Enumerating a game-mode dispatch table's ~50 entries (D&D: Shadows over
Mystara, CPS2, `ddsom`) found 6 different mode byte values resolving to 6
different byte offsets — genuinely different addresses, not duplicates.
Investigating each address directly (rather than assuming 6 independent
screens) revealed they were all **entry points into one single, unbroken,
linear routine**: a full linear disassembly from the lowest target address
to well past the highest showed zero branches, jumps, or returns anywhere
in that span, meaning every entry point falls straight through into the
exact same tail code (in this case, a shared palette-load + object-setup +
BGM-cue sequence). Each entry point simply starts at a different point in
the same straight-line sequence, skipping a different number of leading
setup instructions the caller's own prior state had already performed
(e.g. one entry skips two initialization subroutine calls another entry
executes; another additionally skips a set of scroll-register clears).

This is a common, deliberate code-generation shape in hand-written 68k/Z80
game code: a single "enter this screen/state" routine with multiple named
entry points, used so several different callers (each having already done
a different subset of the common setup) can all converge on the same
tail without duplicating that tail's code or forcing every caller to
redo work it already did. It is easy to mistake for "N independent
handlers" if you only look at the *set of distinct target addresses*
without checking whether they're all inside one *contiguous* code region
with no intervening control flow.

**Fix:** before treating a dispatch table's distinct target addresses as
distinct handlers, sort them and check for gaps: linearly disassemble
from the lowest target through the highest (and a reasonable margin
past it) and look for any `bra`/`bcc`/`jmp`/`rts`/`ret` that would break
the straight-line assumption before the highest address. If none exists,
every entry in that address range is a skip-ahead variant of ONE routine,
not independent screens — and, usefully, this is itself positive
evidence about the *callers*: several different dispatch values reaching
the same tail is exactly the shape you'd expect for a commonly-reached
hub/shared screen (reachable from multiple prior game states), which can
strengthen rather than weaken a semantic hypothesis about what that
screen is, even without direct text/label confirmation.

Found in `~/Development/kolbold` (`ddsom`, CPS2) —
`docs/ddsom/cps2/data-structure.md` sec "3.5 Palette"'s "Update (3rd
follow-up session)" block.
