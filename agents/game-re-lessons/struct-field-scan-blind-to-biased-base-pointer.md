# A struct-field dataflow scan keyed on the literal displacement byte is blind to any function that biases its own base pointer

**When it bites:** a literal-displacement census ("any `sw ...,0x94(reg)`?") gives a clean but suspicious negative for a known struct field, especially in a hot loop, a struct-tail init or copy, or an array-of-structs walker. Also: dismissing a `disp(reg)` hit as "a different field". Also: transcribing loop-body offsets by hand. Also: a raw-displacement census jumps from 0 to hundreds of hits.

A field census that matches the instruction's displacement operand assumes the base register points at offset 0 of the record. Compilers (and hand-written asm) bias the pointer once and address fields relative to the bias, especially in loops and tail inits, where it saves the most instructions:

```
addiu $a2, $t0, 0x98      ; $a2 = record+0x98  (the bias)
lw    $v0, -0x4($a2)      ; really record+0x94
sw    $v0, -0x4($a2)      ; the write you were hunting
```

The literal `0x94` never appears. However exhaustive, a literal-displacement census cannot match it. This applies to any ISA: 68k `LEA` + `(d16,An)`, ARM register-relative loads, and so on.

**Check / fix:**
- Run a **forward symbolic pass** tracking `reg == root + k` through `addiu` and register-move idioms (`addu rd,rs,$zero`, `or rd,rs,$zero`). For every load **and store**, test the effective `k + disp` against the target, with `disp` allowed to be **negative**. It runs in seconds over a whole image, and corpus-wide it doubles as a uniqueness proof.
- **Self-increment** `addiu $r,$r,K` (loop advance) sets a **fresh checkpoint** `{root:r, k:0}`. Don't fold `K` into the existing bias. The tell is a positive `K` in a loop body that compares `$r` (or a paired index) against a bound.
- **Derived registers:** also trace registers built by adding two already-traced registers (`addu $v0,$s1,$s3` → `0x20($v0)`), not only `addiu`-with-immediate, and not only the register a sibling read happens to use. For stack-copied tables, enumerate every `addiu $r,$sp,X` that could be the block's base.
- **A read-question census isn't complete for a write question.** Extend the same pass to stores before concluding "no producer".
- **Explain every hit.** N census hits need N individual explanations before the round closes.
- **Manual review and hand transcription:** never call a hit at `disp(reg)` "a different field", or record loop-body displacements as record-relative, until you've resolved `reg`'s bias (check every `addiu $base,$other,K` between loop entry and the first body instruction).
- **Oracle for a bias correction:** check whether the corrected `k + disp` offsets land on fields a sibling/similar struct decoder already named. Also grep the project's docs for the *resolved* offset label (e.g. `obj+0x1c`), not only the canonical field name (`doc-self-cross-reference-before-fresh-disassembly.md`).
- **The noise direction:** once the corpus is complete, small literal displacements collide with unrelated structs. Root the census at the confirmed base idiom, reduce displacements modulo the stride, and then triage every distinct survivor by hand. A residue-only (`k mod stride`) tracker still produces coincidences.
- A project that has hit this twice should run the bias-tolerant pass *before* trusting any further literal-displacement negative.

**Canonical example:** Valkyrie Profile (PSX, `valkyrie`). The per-frame `actor.x += actor.velX` commit was searched across the 369,036 B field overlay by three independent passes: a register-tracked dataflow scan, a move-idiom-tolerant successor, and a 168-function call-graph sweep for `sw ...,0x94/0x98(reg)`. All three reached the real function `FUN_80039b5c` (5th of 12 calls in the per-frame dispatcher) and reported zero. It does `addiu $a2,$t0,0x98` and accesses X at `-0x4($a2)` and Y at `0x0($a2)`. A purpose-built "pointer-indirection scan" also missed it, because it accepted only positive derefs (`0`/`4`). The symbolic pass found exactly three biased stores at effective `0x94`/`0x98`, all in that function.

**Variants (all `valkyrie`):**
- Room-installer zero-init: `a1 = runtime+0x38` makes the `+0x20`/`+0x24` stores `-0x18(a1)`/`-0x14(a1)`.
- Flag word `obj+0xe4` resisted four techniques. `FUN_800367d8` biases `$s2 = actor+0xc8` and uses `0x1c($s2)`. The sites had been seen and dismissed as "different field", and a sibling doc already listed them as `obj+0x1c`. A later loads-only census on the same bias missed a producer until it was extended to `sw`.
- Loop pointer: `lw $s4,…; addiu $s4,$s4,0x108; addiu $s0,$s4,0x90; lw 0x58($s0)` = `actor+0xe8`. Accumulating gave `k=0x198`, which defeated a `re-oracle` store-extended census as well.
- Hand transcription: an `addiu $a0,$s2,0x16` before a stride-`0x20` loop was never added back. The corrected `+0x19`/`+0x1c` matched `itemTable32`'s named fields.
- Noise: a stride-`0x30` platform array's tail `0x2c`–`0x2f` gave 0 hits on an incomplete corpus and 334 on the complete one. Rooting at `*(0x8007f10c)` and reducing mod `0x30` left 6 addresses: 3 coincidental, 2 already known, 1 genuine new reader of a field documented as having "no reader".

Related but distinct: `narrow-opcode-form-census-false-negative.md` (opcode-form gaps), `indexed-operand-needs-base-provenance.md` (ambiguous base identity).

**History:** 8 recorded instances (all `valkyrie`): full log in `_archive/struct-field-scan-blind-to-biased-base-pointer.md`.
