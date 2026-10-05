# A "Correction" block's cited address can be byte-verified, real, and disassembly-confirmed — and still belong to the WRONG function

**When it bites:** a doc's `> Correction` block overrides an earlier claim
about function X's behavior, citing a concrete instruction-address range as
its evidence — before trusting it, confirm that address range actually
falls between function X's own confirmed prologue and its own return, not
inside a different, later-starting sibling function that happens to read
the same field names/offsets (common when two related formulas — e.g. a
physical-damage and a magic-damage calculation — share input fields like
"attacker accuracy" or "penalty range").

## The trap, and why it's sharper than it looks

`test-fixture-encodes-same-wrong-model-as-implementation.md`'s "Sharpened
fix" already warns that an undated, address-free citation is weak evidence.
This is the opposite, scarier case: the citation here is *maximally*
concrete — a byte-exact, both-discs-verified instruction range, correctly
disassembled, with no vagueness anywhere in it. The mistake isn't in the
disassembly at all; it's a pure **function-boundary attribution** error —
nobody checked whether the cited address range sits inside the SAME
compiled function the surrounding prose claims to be describing, versus a
structurally separate function that starts a few hundred bytes later in
the same overlay/file and happens to read an identically-named field.

## Confirmed case

Valkyrie Profile (PSX): `battle-logic.md` §31.5 (2026-09-03) disassembled a
real accuracy/graze-penalty roll at `0x8003b790`-`0x8003b7c8`, correctly
labeling it "inside `fcn.8003b648` (the outer physical-damage-roll
function)". A same-day "Correction" to the physical ATK/DEF formula's own
section (`fcn.8003ae48`) then used that citation to overturn the section's
ORIGINAL reading (a graze roll applied symmetrically to ATK/DEF, inside the
formula, before the subtraction) in favor of "the roll happens once, in a
separate outer function, applied to the whole already-floored result."

Both citations were byte-real. The error was that `fcn.8003b648` is **not**
`fcn.8003ae48`'s outer wrapper — it is a wholly separate, later-starting
function (its own fresh `addiu $sp,$sp,-0x28` prologue begins 8 bytes after
`fcn.8003ae48`'s own `jr $ra`), and it turned out to be the game's SEPARATE
magic-damage formula. It independently reads the identical field names
(`attacker+0x5ba` accuracy, `+0x5b8` penalty range) and rolls its own,
unrelated graze penalty for magic attacks — a coincidence that's not really
a coincidence at all, since both formulas need the same kind of input. A
round-198 rigor audit re-disassembled `fcn.8003ae48` itself from scratch and
found it has its OWN, previously undocumented graze roll (in fact closer to
the section's pre-correction reading than to the correction that replaced
it) — the "Correction" had silently swapped in a true fact about the wrong
function.

## Fix / general defense

When a `Correction` block's evidence is "function Y does Z, therefore
function X (the one under discussion) must not do W", don't stop at
verifying Y's disassembly — **independently re-derive function X's own
boundaries** (its own prologue, its own `jr $ra`/return) and confirm Y's
cited address range falls *outside* X, or that Y is genuinely X's only
caller/callee in the relevant sense, before letting Y's behavior override a
claim about X. Two functions sharing field names is not evidence they share
identity, especially when both plausibly need the same class of input
(accuracy, a stat, a flag) — that's exactly when a coincidental read of the
same offset in a nearby, unrelated function is most likely to occur and
most easily mistaken for "the same mechanism, more precisely described."
