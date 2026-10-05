# `check(label, word === (a<<26)|(b<<21)|c, ...)` silently parses as `(word === (a<<26)) | (b<<21) | c` — a false-positive PASS machine

**When it bites:** writing a verify script's `check(label, condition,
detail)`-style boolean argument where `condition` reconstructs an
expected bit-packed value (a MIPS/68k/any fixed-width-ISA instruction
word, a flags byte, an FOURCC) by OR-ing several shifted immediate fields
directly inside the same expression as a `===` comparison against the
real decoded value — e.g. `word === (opcode << 26) | (rs << 21) | (rt <<
16) | imm`.

## The trap

In JavaScript/TypeScript, `===` binds **tighter** than `|` (bitwise OR).
So `a === b | c | d` does not mean `a === (b | c | d)` — it means `(a ===
b) | c | d`: compute the boolean `a === b`, coerce it to `0`/`1`, then
bitwise-OR that against `c` and `d`. The result is a **number**, not a
boolean, and almost always nonzero (any real `c`/`d` operand is nonzero
for a non-trivial opcode/field), so a `check()` helper that just checks
truthiness (or a caller that treats any nonzero return as "passed")
reports **PASS regardless of whether the real comparison held** — the
check has been rendered inert, silently, with no runtime error.

## Confirmed case

Valkyrie Profile round-202 rigor-audit verify script
(`tools/valkyrieprofile/verify-enemy-stat-record-rigor-audit.ts`)
contained:

```ts
check('0x80059478 = addiu a3,v0,0x394',
  addiu394.word === (0x24 << 26) | (2 << 21) | (7 << 16) | 0x394, ...);
```

This parsed as `(addiu394.word === (0x24 << 26)) | (2 << 21) | (7 << 16)
| 0x394` — a nonzero number, truthy in every code path that mattered.
TypeScript's `tsc --noEmit` caught it as a real type error (`TS2362`/
`TS2345`: an arithmetic operand of `|` was a `boolean`, and the `check()`
parameter expected a `boolean` but received a `number`) — which is what
surfaced the bug at all, since the script runs under `tsx` and would
otherwise have executed with no crash and printed `[PASS]`. Fixing the
precedence in isolation (wrapping the OR chain in parens) then exposed a
**second, independent** bug the broken check had been masking: the
hand-computed expected opcode constant was `0x24` (the `lbu` opcode)
instead of `0x09` (the real `addiu` opcode) — the check had never
actually been evaluating the right comparison at all, in either
direction.

## Fix / general defense

- **Always parenthesize a multi-field bit-reconstruction expression as a
  single unit** before comparing it: `word === ((opcode << 26) | (rs <<
  21) | (rt << 16) | imm)`. This is cheap and removes the ambiguity for a
  human reader too, not just the parser.
- **Type the `check()`/assertion helper's condition parameter as
  `boolean`** (not `boolean | number` or untyped `any`) so `tsc --noEmit`
  can catch this class of bug — this is a direct, concrete payoff for
  running the full triad (including `tsc`) even on throwaway-adjacent
  verify scripts, not just committed production code.
- Treat a genuinely mysterious `[PASS]` on a check you have independent
  reason to distrust as a prompt to re-read the boolean expression's own
  operator precedence, not just its operand values — the check can be
  structurally incapable of failing.
- After fixing a masked comparison bug like this, re-verify the
  now-live check actually still passes for the RIGHT reason (re-derive
  the expected constant from the real opcode table), since the bug it
  was hiding may be a second, unrelated error rather than nothing at all.
