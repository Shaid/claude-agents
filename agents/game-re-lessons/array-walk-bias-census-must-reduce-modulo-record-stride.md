# A biased-base field census over an array walk must compare the bias MODULO the record stride, not the raw constant

**When it bites:** a struct-field consumer census that already tracks
"register = root + k" bias chains (the `struct-field-scan-blind-to-biased-
base-pointer.md` fix, including its self-increment-checkpoint refinement)
still returns a clean zero for a field you have real reason to believe is
read somewhere — especially for code that walks an ARRAY of those structs
(a 96-actor table, a 40-record pool) and compares "this" record against
"every other" one. The tell in the census's own output: biased hits whose
`k` is larger than one record (`k = 0x1ec` on a `0x108`-byte record) that
were silently dropped because `k + disp != field`.

## The trap

A compiler that starts an "every other record" loop at `table + 1 record`
and then biases the loop pointer to a hot field emits:

```
80030810  lw    $v0,-0xf1c($v0)    ; v0 = actor-table base
80030818  addiu $s2,$v0,0x108      ; candidate = table + ONE RECORD (skip slot 0)
80030830  addiu $s0,$s2,0xe4       ; s0 = candidate + 0xe4        <- k = 0x108 + 0xe4 = 0x1ec
80030894  lw    $v1,0x0($s0)       ; candidate.e4  (effective 0x1ec, i.e. 0xe4 of record 1)
800308c4  lw    $v1,0x4($s0)       ; candidate.e8
80030a64  addiu $s0,$s0,0x108      ; next record -- bias preserved
```

A bias tracker that accumulates constants faithfully computes
`bias[s0] = tableBase + 0x1ec` and then asks "is `0x1ec + 0 == 0xe4`?" — no —
and discards the hit. It is *correct* arithmetic and the wrong question:
`0x1ec` is `0xe4` **of the next record**, which is exactly what an array walk
addresses. Valkyrie Profile (PSX, `~/Development/valkyrie`): six effective
`obj+0xe4`/`obj+0xe8` loads inside the per-frame collision resolver's
96-actor anchor-eligibility loop (`FUN_8002fee4`, `0x8003085c`-`0x800309e8`)
were invisible to THIRTEEN rounds of censuses plus two prior `re-oracle`
escalations, and two of them were the sole consumers of `obj+0xe4` bit 17
and `obj+0xe8` bit 11 — bits that had been carried as "producer found, no
consumer after five independently-shaped techniques". The same round-13
census that had just been *fixed* for the self-increment idiom
(`addiu $r,$r,0x108` = fresh checkpoint) still missed these, because the
loop's initial `+0x108` is not a self-increment — it is a plain hop off the
table base, and the tracker added it in.

Adding modulo reduction found 13 previously-invisible effective accesses
overlay-wide in one run, every one a real actor-record access on manual
inspection (a second identical `+0x1ec` loop in a different function, a
`+0x198` = `0x108 + 0x90` walk, a fixed-slot `table + 8*0x108 + 0x90`
access, and a `table + 0x901` / `lw 0x27($s0)` pair that only makes sense as
`8*0x108 + 0xe8`).

## The fix

When the bias chain is rooted at a known **array base** (a global table
pointer) or has passed through any `± stride` hop, compare
`(k + disp) mod stride` against the target field, not `k + disp`. Keep the
raw value too — the slot number `(k + disp) div stride` is itself
information (a hardcoded "slot 8" access is a finding). Two side conditions
that keep the false-positive rate at zero:

- only reduce when the root is the array base or the chain saw the stride
  (a generic `addiu $s0,$a0,0x1ec` off an unknown parameter register is NOT
  reduced — it may be a different struct entirely);
- keep the existing self-increment checkpoint rule for `rs === rt` hops that
  are NOT a stride multiple (a fresh unknown base), but treat `rs === rt`
  hops that ARE a stride multiple as bias-preserving (the loop advance).

Report every hit with `k >= stride` separately from the `k < stride` ones: the
former are exactly the population every earlier census structurally could
not see, so they are the list to hand-check first.

## Why the usual controls did not catch it

- The positive controls used in every prior round (already-known bits) all
  lived in loops that address the *acting* actor via a plain register or a
  sub-record bias (`+0x90`, `+0xc8`) — never through a `table + n*stride`
  hop — so a census blind to stride-offset biases passed every control.
- A `lui $r,0x2`-style mask-constant scan that checks "does a literal
  `0xe4($reg)` access appear within +N instructions" fails here twice over:
  the load is *before* the `lui` and it is not literal.
- The prose answer already existed in a sibling doc section written for a
  different question (the anchor-eligibility gate list named
  `candidate.e4 & 0x00020000` explicitly) — `doc-self-cross-reference-
  before-fresh-disassembly.md` applies; grep every sibling doc for the bare
  mask value before building a new census.
