# An N-case dispatcher's selector may itself be forced to a near-constant value — trace its provenance before sampling case bodies

**When it bites:** a jump table or dispatcher is confirmed (it exists, has N cases, and gets called), and the next step looks like sampling or tracing a subset of its N case bodies. Also: you're about to declare a reachable-case collapse final from the one call site that led you to the function. Also: the selector passes through an intermediate lookup or rotate table.

A jump table's declared size is not its reachable size. The selector may be copied from another field that a different module forces to a constant, or fed through a degenerate table (an identity ramp, an all-same fill). A function found and named from one motivating caller may also have other callers with a different selector source.

**Check / fix:**
1. Find the selector's defining instruction(s), not just the `andi` that narrows it.
2. If it's copied or forced from another field, trace **that** field's writers, including in sibling overlays and modules.
3. Run a corpus census of the real input field to get the exact reachable case set and counts. Only then prioritize which cases to trace, and prove the rest dead.
4. If the selector goes through a lookup table, check whether the table's builder fills it degenerately (`table[i]=i`, a constant) regardless of input. If it does, an existing census of the real driving value may only need a wider loop bound.
5. Run a whole-binary `jal`/`bl`/`call` census for the dispatcher's own address. Scope any collapse verdict to the callers you have actually checked.
6. Disassemble from the true prologue, not from where your motivating trace entered. A verify script whose first cited address isn't the entry point leaves the code before that address unread.

Related: `negative-from-addressing-root-not-shapes.md`, `index-writer-may-be-a-loop-counter-not-a-selection.md` (whether it's a selection at all).

**Canonical example:** Valkyrie Profile (PSX, `valkyrie`). The death dispatcher `fcn.80034838` has a 32-entry table keyed on `actor+0x128 & 0x1f`. With `actor+0x129==2`, `+0x128` is overwritten from `+0x5b7`, which a shared actor-init in another overlay (TOC 1491, `fcn.8009ae4c`) zeroes for every enemy. A census of all 1992 enemy move records found only 6 distinct values of `field0a & 0x1f`, so 26 of 32 cases are provably dead, one of them a linker-adjacent alias into another function's table.

**Variants:**
- Same function, later round: the `jal` census found 7 callers, not 1. The other 6 take a prologue branch (`0x8003486c`–`0x80034900`) before the verify script's first address (`0x800348f4`), with a different selector source.
- That source, `fcn.800301fc`, reads a 3-slot table that `fcn.8009eb44` fills with `table[i]=i` for enemies, an identity table. The old census with its loop widened to `0..actionsPerPhase-1` gave the same reachable set.

**History:** 3 recorded instances (`valkyrie`). Full log in `_archive/dispatch-selector-provenance-collapses-reachable-cases.md`.
