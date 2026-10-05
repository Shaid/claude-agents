# A struct-field dataflow scan keyed on the literal displacement byte is blind to any function that biases its own base pointer

**When it bites:** searching for who writes/reads a known struct field
offset (e.g. "does any code do `sw ...,0x94(reg)`") via a literal-immediate/
displacement census, and getting a clean but suspicious negative across a
large, well-covered call graph — especially for a hot per-frame/per-element
loop, since compilers bias a base pointer exactly there to save one
instruction per iteration. If a dataflow scan visits the right function
(it's in-graph, reachable, even walked by name) and still reports zero
hits, don't trust the negative yet.

## The trap

A field-write census that matches the instruction word's own displacement
operand assumes the struct's base pointer always points at offset 0 of the
record. A compiler (or hand-written assembly) is free to bias the pointer
by a constant first and then address every field relative to *that*,
shrinking every subsequent displacement:

```
addiu $a2, $t0, 0x98      ; $a2 = &record.fieldAtOffset0x98  (THE BIAS)
...
lw    $v0, -0x4($a2)      ; really record+0x94
lw    $v1,  0x4($a2)      ; really record+0x9c
sw    $v0, -0x4($a2)      ; *** the write to record+0x94 you were hunting ***
```

The literal bytes `0x94`/`0x98` never appear anywhere in this function's
body. A census keyed on the literal displacement is *structurally*
incapable of matching it, no matter how exhaustively it's run.

## Confirmed case

Valkyrie Profile (PSX, `valkyrie`): the field engine's per-frame position
integration commit (`actor.x += actor.velX`) was searched for across the
complete 369,036 B field overlay by **three independently-built passes**:
an exhaustive register-tracked dataflow scan, a move-idiom-tolerant
successor (propagating tags through `addu $rd,$rs,$zero`/`or
$rd,$rs,$zero` register-copy idioms), and a 168-function reachable-
call-graph sweep for `sw ...,0x94/0x98(reg)`. All three correctly reached
the real function (`FUN_80039b5c` — it's the 5th of 12 calls in the field
engine's own per-frame dispatcher) and all three reported zero hits,
because `FUN_80039b5c` biases `$a2` via `addiu $a2,$t0,0x98` and then
accesses X at `-0x4($a2)` and Y at `0x0($a2)` — the literal bytes `0x94`
and `0x98` appear nowhere else in the function.

A fourth, purpose-built "pointer-indirection scan" (looking for
`addiu $rd,$rs,OFFSET` followed by a small dereference) was built
specifically to catch base-pointer bias and **still missed it**, for two
compounding, narrower reasons: it only accepted a small *positive*
dereference (`0`/`4`), missing the real `-0x4` effective offset, and it
only reported the single `+0x9c` construction it did find, not every
biased-base store in the image.

## Fix

Run a **forward symbolic pass** tracking `reg == root + k` through
`addiu`/register-move idioms, and for every load/store off that register
test the *effective* offset `k + disp` against the target field offset —
with `disp` allowed to be **negative**, not just a small positive
constant. This is cheap (seconds over a whole image) and, run corpus-wide,
doubles as a uniqueness proof: on this target it returned exactly three
biased-base stores whose effective offset was `0x94`/`0x98`, all three
inside the one function that had evaded every earlier scan. Not MIPS-
specific — the identical trap applies to 68k (`LEA` + `(d16,An)`), ARM
(`ADD`/register-relative loads), or any ISA where a base register can be
pre-offset before a loop body.

**General defense**, independent of tooling: before writing up "no
consumer/writer exists" from any struct-field census, ask whether the
*absence of the literal offset itself* could mean the base was biased
rather than the field being genuinely unwritten — particularly inside a
tight, already-confirmed-reachable loop body, which is exactly where a
compiler has the most incentive to do this.

Related but distinct: `narrow-opcode-form-census-false-negative.md`
(addressing-mode/opcode-form coverage gaps) and
`indexed-operand-needs-base-provenance.md` (an indexed operand's *base
identity* being ambiguous). This lesson is about a *correctly identified*
base register whose own offset arithmetic silently retargets the literal
displacement the census searches for.

## Third confirmed instance: an installer's own zero-init loop

Confirmed a second time in the same project (Valkyrie Profile, PSX,
round 121, 2026-09): a room-installer's copy loop that zero-initializes a
runtime struct's tail fields was searched for literal `sw zero,0x20(reg)`/
`sw zero,0x24(reg)` stores and found none, seemingly confirming those two
fields were left unzeroed. The loop actually ran with `a1 = runtime+0x38`
biased once before the loop body, so the real stores were `sw zero,
-0x18(a1)`/`sw zero,-0x14(a1)` — invisible to the literal-offset search for
exactly the reason this file describes. Two independent instances in one
project is a strong signal this trap is common wherever a compiler
zero-inits or copies a struct's *tail* fields specifically (the bias saves
more instructions the further into the struct the fields sit), not just in
hot per-frame loops as the original case suggested.

## Sibling-table variant: one shared base, reached through a DERIVED register

The bias doesn't have to sit in the base register a census already knows
about — it can sit in a **third register built by adding two already-traced
registers together**, one of which is the shared base and the other a
per-iteration index, with the sum only ever materializing right at the
point of use. Confirmed on Valkyrie Profile (PSX, `valkyrie`): a
party-formation initializer copies three same-shaped 4-word tables onto
consecutive stack slots (`sp+0x10`/`sp+0x20`/`sp+0x30`) and takes **one**
base register to the whole 48-byte block, `$s3 = sp+0x10`, set once near
the top of the function. Two of the three tables are read later via
`$s0 = seat*4 + $s3` and displacements `0x0($s0)`/`0x10($s0)` — an ordinary
biased-base pattern. The third table's own read, dozens of instructions
away in a different branch, reuses the *same* arithmetic but computes it
into a **different** register on demand: `$v0 = $s1 + $s3` (`$s1` = the
identical `seat*4` value, computed once, reused for both `$s0` and this),
then `lw $v0, 0x20($v0)`. Three independently-built census passes across
two sessions of the same project all missed it — one searched literal
re-materializations of the table's own global address, one searched
constant `sp+0x34..0x3c` displacements directly off `$sp`, and one searched
specifically for `0x20($s0)` (the register the other two sibling reads
happen to use) — and a fourth session's own prose actively **mislabelled**
the exact instruction as reading a *different* sibling table, having
assumed the register in play without checking which table's base the
arithmetic actually traced back to. The read was sitting in plain sight in
an already-transcribed disassembly listing the whole time.

**Sharpened fix for this variant:** when several same-shaped structures
are copied to consecutive slots of one stack block, enumerate every
`addiu $r,$sp,X` that could be the block's own base (`X <=` the slot you
care about), then trace **every register later built by combining two
already-traced registers via plain register-to-register arithmetic**
(`addu`/`add`, not just `addiu`-with-a-fresh-immediate) — not only
literal-`$sp`-relative displacements, and not only the one register a
*sibling* read happens to use. A "no consumer" verdict on a stack-copied
local is only as good as this enumeration; a census that stops at "the
usual register" for a table's neighbours will confidently mis-attribute or
miss the one table addressed through a register nobody expected.

## Fourth confirmed instance: FOUR independent techniques, one shared bias, closed only by `re-oracle`

Confirmed a fourth time in the same project (Valkyrie Profile, PSX,
round 131, 2026-09): the field engine's actor flag-word bits 12/27/29 at
`obj+0xe4` resisted **four differently-shaped static passes in the same
session** — a literal `lw/andi 0xe4` window scan, a from-scratch
register-chain forward-dataflow tracer (SET/CLEAR census via in-place
`andi`/`ori` and register-register `and`/`or` against a tracked-constant
table), an `ori`-based census, and a corpus-wide same-src/dst filter — all
four returning a clean negative on `obj+0xe4` specifically. Per this
project's escalation ladder, two genuinely different failed approaches
already justified escalating; four were tried before doing so. A
`re-oracle` escalation found the real cause in one pass: `FUN_800367d8`
(the field draw-list walker / animation ticker) biases `$s2 = actor +
0xc8` once, then reads/writes the flag word as `0x1c($s2)` — real effective
offset `0xc8 + 0x1c = 0xe4` — never as the literal byte `0xe4` anywhere in
the function. This is the **third time this exact project** has hit this
family of trap (see the two instances above), which is itself worth
noticing: a project that has hit a pattern twice should default to
running a bias-tolerant symbolic pass *before* trusting any further
literal-displacement negative on the same struct, not after four retries.

**New, sharper failure mode this instance adds:** the real sites had
already been noticed and briefly considered during hand-review, but were
dismissed as "a different field" because the visible displacement was
`0x1c`, not `0xe4` — and, separately, a sibling doc in the same project
(`dungeon-field-mechanics.md`) had *already documented these same sites*
the day before under the label `obj+0x1c`, which a
`doc-self-cross-reference-before-fresh-disassembly.md`-style search (grep
the project's own docs for the *resolved* offset, not just the field's
canonical name) would have surfaced without any new disassembly at all.
The general fix from the base case still applies (a forward symbolic pass
tracking `reg == root + k`, negative `disp` included) — but this instance
underscores that the same discipline has to hold during **manual**
review, not just automated census-building: never dismiss a hit at
`disp(reg)` as belonging to "a different field" until `reg`'s own bias
`k` has been resolved and `k + disp` checked against the field you're
hunting. A biased hit looks exactly like a legitimate different-field
access until that arithmetic is done.

## Fifth confirmed instance: the same bias, but the census only tracked LOADS, and its own prior hits went half-explained

Confirmed a fifth time in the same project (Valkyrie Profile, PSX, round 12
of the `vp1psx-scene-script-opcodes` campaign): the round-11 pass had
already built and run a biased-base census against `FUN_800367d8`'s
confirmed `$s2 = actor + 0xc8` bias and gotten 3 hits at effective
`obj+0xe8` — but the census tracked `lw` (load) roots only, and a follow-up
producer search for a *different*, still-open bit (a write, not a read)
came back negative for two more rounds before `re-oracle` found it by
**extending the identical census to also match `sw` off the same biased
register**, immediately turning up the missing producer. Separately, of
the 3 original load hits, round 11's write-up had only explained what 1 of
them did; the other 2 sat unexplained in the census output across an entire
round before this session traced and closed them. **Two compounding
generalizations:** (1) a biased-base census built to answer a *read*
question is not automatically complete for a *write* question on the same
struct — a "producer not found" search on a field with a confirmed biased
consumer should extend the same symbolic pass to stores before concluding
the producer doesn't exist, not build a separate literal-offset search from
scratch; (2) once a biased-base (or any) census returns N hits, all N need
to be individually explained before the round closes — a census's own
unexplained-hit backlog is exactly the kind of thing
`doc-self-cross-reference-before-fresh-disassembly.md` warns can sit
unread in a doc for a full round while a fresh investigation starts
elsewhere.

## Sixth confirmed instance: a self-incrementing LOOP pointer as the bias root, not a plain function argument

Confirmed a sixth time in the same project (Valkyrie Profile, PSX, round 13
of the `vp1psx-scene-script-opcodes` campaign). Every prior instance's bias
root was a single `addiu $rt,$rs,K` hop off a register whose bias was
already null (usually a function argument holding the raw struct pointer),
so a symbolic tracker that resets `bias[d] = null` on every `lw` and treats
one `addiu` from a null-biased register as `{root: rs, k: K}` catches it
fine. This instance's root is a **self-incrementing loop pointer** instead:

```
lw    $s4, -0xf1c($s4)   ; $s4 = actorTableBase (a fresh lw -> bias[s4] = null)
addiu $s4, $s4, 0x108    ; SELF-increment: "$s4 IS the current actor now" (loop idiom)
addiu $s0, $s4, 0x90     ; second hop off the just-incremented pointer
...
lw    $v0, 0x58($s0)     ; effective actor+0xe8 -- but 0x90+0x58=0xe8 only if
                          ; the self-increment is treated as a fresh k=0 point
```

A tracker built for the base case computes `bias[s4] = {root: s4, k: 0x108}`
(accumulating the self-increment's own displacement onto the pre-increment,
null-biased register) rather than recognizing that the self-increment
*redefines* what "offset 0" means — the loop's own semantics are "$s4 now
points at the current struct," not "$s4 is 0x108 past some other base." The
resulting `bias[s0].k` comes out `0x108 + 0x90 = 0x198`, not `0x90`, so a
real `0x58($s0)` access is invisible to a census matching `k + disp ==
targetOffset`. This is a distinct failure from the sibling-table variant
above (which needed tracing a register built by ADDING two already-traced
registers) and from the fourth/fifth instances (a single missed hop, or
loads-only coverage) — here the tracker sees the whole chain, follows every
hop, and still computes the wrong `k` because one hop in the chain is a
self-referential increment, not a fresh displacement from a known-zero
point. It also defeated a `re-oracle` escalation's own "biased-base census
extended to stores" (built to close the load-only gap the fifth instance
found), because that extension inherited the same accumulation bug.

**Sharpened fix:** when building a symbolic `root+k` bias tracker for a
loop that walks an array of structs, special-case `addiu $r,$r,K` (`rs ===
rt`, the same register on both sides — a loop-advance idiom, not an
arbitrary displacement) as establishing a **fresh checkpoint**,
`bias[r] = {root: r, k: 0}`, rather than folding `K` into whatever bias `r`
already had. A cheap tell that this idiom is present: grep the function for
`addiu $r,$r,K` with a positive `K` inside a loop body that also compares
the same register (or a paired index) against a bound — a table-walk
signature. Any array-of-structs walker (an entity list, a room table, a
task pool) is a candidate for this exact shape, on any ISA with an
add-immediate instruction, not just MIPS.

## Seventh confirmed instance: the trap bites a HUMAN transcription too, not just automated censuses — and the fix doubles as a verification oracle

Confirmed a seventh time in the same project (Valkyrie Profile, PSX, round
190): every prior instance was a *census* (automated code) missing a biased
base. This one was a prior **round's own hand transcription** of a
disassembly listing: an `addiu $a0,$s2,0x16` sat once, before a loop, and
`$a0` then self-incremented by the record stride (`addiu $a0,$a0,0x20`,
the sixth instance's exact shape) each iteration. The prior round correctly
transcribed the loop body's literal `lbu $v0,0x9($a0)`-style operands into
a table, but wrote them up as record-relative offsets `0x9`/`0x1`/`0x3`/
`0x6`/`0x0` — never adding back the `0x16` hoisted onto `$a0` before the
loop started. Same trap, same fix (a forward `root+k` pass, self-increment
special-cased as a fresh checkpoint) — but this time the fix must be
applied by a human/AI reading a listing by eye, not just by code: **never
transcribe a loop body's literal displacement operands as record-relative
without first checking every `addiu $base,$other,K` between the loop's
entry and its first body instruction.**

This instance also surfaces a cheap, generalizable **verification oracle**
for a bias-correction hypothesis: the *corrected* offsets (`0x16+K`) landed
exactly on two fields (`+0x19`, `+0x1c`) an unrelated, already-confirmed
sibling struct decoder (`itemTable32`) had independently named weeks
earlier — one as the exact bit tested a few instructions later, the other
as an already-named-but-unattributed byte. Two independently-derived field
offsets landing on already-known semantics is strong corroboration that a
bias correction is right (not a coincidence worth re-deriving from
scratch): when a suspected pre-loop bias is found, check whether adding it
back makes any of the loop's literal displacements land on an
already-named offset of a structurally similar/sibling record before
trusting (or discarding) the correction.

## Eighth confirmed instance: fixing corpus completeness turns "0 hits" into hundreds of hits, almost all noise — the bias-rooted fix is a noise FILTER here, not a miss-recovery, and its own output still needs per-hit manual triage

Confirmed an eighth time in the same project (Valkyrie Profile, PSX, round
220): every prior instance here was about a census returning a **false
negative** because the base was biased. This instance is the mirror image —
a *raw literal-displacement* census (immediate `0x2c`/`0x2d`/`0x2e`/`0x2f`,
no bias-awareness at all) against a stride-`0x30` platform-record array's
tail fields returned **0 hits beyond the known constructor/remover** under
an incomplete corpus (a single disc, several `build/cache/` images with a
wrong base address or truncated content). Fixing the corpus's own
completeness — live-extracting both discs correctly — made the SAME raw
census return **334 hits**. This jump is not evidence of new content: the
literal bytes `0x2c`-`0x2f` are common small struct-field offsets, so a
complete corpus scan collides with many unrelated structs at the same
numeric displacement purely by chance, and the collision rate scales with
how much corpus the census actually covers, not with how much real content
exists. The fix is this file's own bias-rooted census — but built to REJECT
noise here, not to recover a miss: rooting the scan specifically at the
confirmed platform-array base (the `lui`/`lw` idiom that materializes
`*(0x8007f10c)`) and reducing every hit's displacement modulo the record
stride (`0x30`) collapsed 334 raw hits down to 6 distinct addresses. Even
that residual still wasn't automatically trustworthy: a **residue-only**
bias tracker (tracking `k mod stride` rather than the exact `root+k`) has
its own nonzero coincidence rate, since two genuinely different offsets can
be congruent mod the stride — of the 6 rooted addresses, manual disassembly
found 3 were still coincidental (an unrelated struct's field happened to be
`stride`-congruent with the target), 2 were already-documented reads the
raw scan could never see (pre-biased base registers with a literal `0x0`
immediate), and exactly 1 was a genuine, previously undocumented second
reader of a field a doc had called "no reader anywhere in this corpus."

**Two compounding generalizations:** (1) don't trust a raw literal-
displacement census's hit COUNT as a signal at all once a corpus becomes
"complete enough" to hit real background noise — the count you should
trust is the bias-rooted one, and even a jump from 0 to hundreds of raw
hits, on its own, is not evidence of a new consumer; (2) a bias-rooted
census reduces noise, it doesn't eliminate the concept of noise — every
DISTINCT address it returns still needs individual manual disassembly
triage (which struct is `reg` actually pointing at here?) before any of
them are reported as findings, exactly as the base case's "root+k" tracker
already required for a single hit, just now at small-residual scale instead
of one-hit-at-a-time.
