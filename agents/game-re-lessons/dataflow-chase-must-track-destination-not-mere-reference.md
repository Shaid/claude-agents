# A register-chain dataflow chase's continuation/termination rule must key on the instruction's own WRITE target, not opcode shape or mere operand presence

**When it bites:** building (or re-running) a forward register-chain
dataflow census — following a value loaded into a register through
`ANDI`/`ORI`-in-place, register-register `AND`/`OR` against a tracked
constant-register table, shift-extract idioms, or any similar chain — to
find every SET/TEST/CLEAR site for a specific bit in a struct field. The
census needs a rule for "does the NEXT instruction that touches my tracked
register continue the chain, redefine it to a new alias, or kill it
outright" — and that rule fails in **two opposite directions** unless it is
keyed on the instruction's own **write (destination) target**, not on
opcode shape or on whether the tracked register merely *appears* somewhere
in the instruction.

**Direction 1 — over-permissive continuation (false positive).** Granting a
blanket exception to a whole opcode class ("an `ori` is usually just
building a constant, so it never breaks the chain") lets a stale, already-
consumed value survive past a real redefinition. Confirmed on Valkyrie
Profile (PSX, `valkyrie`): a bit-12/bit-29 census over `obj+0xe4` flagged a
false CLEAR site that was really an unrelated bit-21 TEST followed, several
instructions later, by an *unrelated* `ori $v0,$v1,0x8` that reused `$v0`
for a genuinely different purpose (building a bit-3 SET value from a
different source register). The chain's "harmless constant builder"
exception matched on the opcode alone and never checked that *this specific
instance* referenced an already-proven constant, so it treated `$v0`'s new,
unrelated value as a continuation of the old chain and misattributed a
mask to the wrong bits.

**Direction 2 — over-aggressive termination (false negative), the mirror-
image bug.** Treating ANY instruction that merely *references* the tracked
register as chain-ending — even when that instruction's own destination is
a completely different register, leaving the tracked register still live
and unchanged — silently drops real test sites and undercounts the census.
Confirmed on the same project, a later round: a corpus-wide `obj+0xe4`
bit-3 reader-site census was independently known to total 51 sites, but a
first destination-*unaware* dataflow chase found only 41-44. Root cause,
found by diffing against a cruder non-dataflow "check the very next
instruction" scan and hand-disassembling one discrepancy: `lw
$v1,0xe4($s1)` was immediately followed by `and $a0,$v1,$a0` — reading
`$v1` as a SOURCE but writing the CLEARED result into `$a0`, a different
register — and the real test, `andi $v1,$v1,0x8`, sat two instructions
later, still reading the same, still-live `$v1`. A chase that kills `live`
on any *reference* rather than any *write* never reaches it.

**Fix, the same structural principle both times:** a chain only continues
past a redefinition when the instruction's write target is the tracked
register AND the specific source(s) feeding that write are provably related
to the tracked value (a matched dataflow pattern with real provenance, not
"this opcode is usually X"); and a chain is only KILLED when the
instruction's write target IS the tracked register and the redefinition
does NOT match a recognized alias/copy-through pattern. An instruction that
reads the tracked register as a source into an unrelated destination must
neither continue the chain under a new name nor kill it — it is simply
irrelevant, and the chase must keep scanning past it with `live` unchanged.
Skipping this "does this instruction's OWN destination equal `live`" check
— in either direction — is the single most common way a hand-rolled
dataflow tracer silently produces a wrong count that still looks
plausible (a nonzero, non-crashing result). Regression tell: when a
positive-control bit reproduces cleanly but a real total disagrees with an
independently-known figure by a puzzling ~10-20%, diff the fast/naive scan
against the "smart" dataflow one and hand-verify every site only one of
them finds, rather than trusting whichever number is "more sophisticated."

**Third instance — the same polarity bug in an AUXILIARY constant-value
cache, not just the chase's own primary `live` register.** A larger census
often keeps a second symbolic structure alongside the primary bit-chase: a
per-register cache of "known 32-bit constant this register currently
holds" (built from `lui`/`lui+ori`/`addiu $r,$zero,imm`), consulted when a
later `and`/`or` needs to know the mask a sibling register carries. This
cache needs the exact same discipline as `live` — invalidate on ANY write
to the register that doesn't match a recognized constant-forming
form — but it is easy to instead implement the *inverse*, wrong-polarity
rule: "only explicitly null the cache entry when a NEW recognized
constant-forming instruction overwrites it," leaving the stale value
untouched by every other kind of write (an ordinary data `lw`/`lhu`, an
unrelated `addu`). Confirmed on Valkyrie Profile (PSX, `valkyrie`), round
18 of the `vp1psx-scene-script-opcodes` campaign: a combined-mask census's
`constRegs[$v0]` cache retained a `lui $v0,0x8008` value across an
intervening `lhu $v0,-0x19e0($v0)` real data load (the load instruction
matched none of the three recognized constant-forming shapes, so the cache
was never told the register had changed), and a later `and`/`or` against
that stale cached constant produced a spurious ~30-bit "clear" event at a
real address (`0x80034afc`) that looked structurally plausible until
manually disassembled. **Fix:** run one generic per-instruction pass, every
iteration, that nulls `constRegs[d]` for every destination register `d`
unless *this specific instruction* is one of the recognized constant-
forming forms — the same "kill by default, keep only on a matched
continuation pattern" polarity as `live`, applied uniformly to every
auxiliary register-keyed cache the chase maintains, not just its headline
tracked value.
