# A constant-argument accessor call can be compiler-inlined into a direct memory write, leaving no call at all to census

**When it bites:** hunting for the setter of one specific flag/property id
through a documented `SetX(id, value)`-shaped accessor, and two censuses
have already come back clean — a literal-immediate `jal SetX` scan with
`a0==id` (or equivalent register-argument form), AND a computed-argument
dataflow trace (`SetX(exprThatEvaluatesToId, ...)`) — yet an external
oracle (a script property table, a sibling doc section, domain knowledge of
what must set this flag) says a real setter exists somewhere.

## What happened

Valkyrie Profile (PSX, `valkyrie`). Flag `0x449` ("Surt has been defeated")
had no setter findable by any call-site census against the documented
`SetFlag(id, value)` accessor. The real write, in the battle overlay's
`startVictorySequence` (Surt-defeat branch, `0x8006c66c`-`0x8006c6d8`), is:

```
varBase[0x676] |= 0x02        // no call to SetFlag at all
```

`0x676` and `0x02` are exactly `SetFlag`'s own `base+1+(id>>3)` /
`1<<(id&7)` formula evaluated at `id=0x449` — the compiler constant-folded
the whole accessor body at this call site because the flag id was a
literal at compile time, and emitted only the resulting bit-set
instruction. There is no `jal` to any accessor left to find, so neither a
literal-argument census nor a computed-argument dataflow trace can ever
find it — both are structurally scoped to *calls*, and this site has none.

This is a third, previously-uncategorized blind spot for a flag/property
setter search, distinct from the two a project's own censuses usually
cover:

1. **Fresh literal call** — `li a0,0x449 ; jal SetFlag` — found by a plain
   literal-immediate-argument census.
2. **Computed-argument call** — `SetFlag(computedId, ...)` where `computedId`
   is built from a table/register — found only by a dataflow trace of the
   argument register back to its producer (indexes, table lookups, etc.).
3. **Compile-time-inlined poke** — no call at all; the accessor's own
   internal arithmetic (base+offset formula, bit-mask formula) has been
   evaluated at compile time and only the resulting direct read-modify-write
   on the flag block's raw address survives. Invisible to both (1) and (2)
   because there is no callee to attribute the write to.

The fix that found it was a **direct byte/bit-poke scan**: search for any
instruction writing through `varBase + K` where `K` matches the accessor's
own offset formula for a candidate flag id, with no call instruction
required at all — then confirm the write's *base register* really is the
flag block by re-deriving its provenance (see below), not by assuming it
from a same-named variable elsewhere in the docs.

**A second error compounded the first this same round.** The base register
at the write traced to `lookupResource(ctx, key=6)`, and an earlier pass
had dismissed this as "unrelated" by loosely matching the name "varBase"
against a *different* `lookupResource(ctx, key=3)` call documented
elsewhere as resolving to an unrelated struct (`P`, the party/save-state
block). Two different registry keys had been conflated under one informal
doc variable name. This is `indexed-operand-needs-base-provenance.md`'s
lesson applied to a *resolver function's key argument* rather than a raw
struct-offset literal — the fix is identical: re-derive each lookup's own
key and resolved target independently; never assume two same-named
"varBase"-style mentions in different doc sections point at the same
object.

## Fix

1. When a documented accessor's call-site censuses (literal AND computed
   argument) both come back clean, and an external oracle says a setter
   must exist, run a **direct byte/bit-poke scan** next: enumerate every
   store instruction writing through the accessor's own base pointer (or
   any pointer whose provenance you can independently confirm resolves to
   the same underlying block) at an offset/mask combination matching the
   candidate id's `base+1+(id>>3)` / `1<<(id&7)`-shaped formula (or
   whatever the accessor's real arithmetic is) — with **no call instruction
   required** as part of the match.
2. Before accepting or rejecting a candidate write found this way, resolve
   its base register's provenance fresh (which resolver, which key/index
   argument, which resolved target) rather than pattern-matching a doc
   variable name against a different section's use of a similarly-named
   variable.
3. Treat "no call found" as evidence about **calls**, not about the flag —
   a compile-time-inlined write leaves the flag's semantics completely
   intact while erasing every trace a call-based census depends on.
