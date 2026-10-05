# A bitwise-containment test (`imm & mask === mask`) can't distinguish "this instruction touches exactly bit N" from "this instruction's immediate happens to be a superset that includes bit N for an unrelated reason"

**When it bites:** you're censusing whether one specific bit of a flags word is individually tested, set, or cleared, when wider group masks exist on the same field or dense near-all-ones constants are in play. Also: an exact mask match whose source register came from a `jal` return value, not a load of the field. Also: a "producer" census that counts TEST-then-branch as SET/CLEAR.

A bare containment check `(imm & mask) === mask` matches every group mask containing the bit (`0xf0`, `0x2f0`) and every dense AND-clear constant (`0xfffffffd`, `0xfffe`), so bits that have no individual evidence still get "hits". Exact matches can mislead too, if the tested register's value has nothing to do with the field.

**Check / fix:**
1. Explicitly exclude every known group-mask immediate from the "individual" bucket. If the group masks aren't all known yet, sort candidate immediates by popcount and hand-check the wide or dense ones.
2. For "does anything clear ONLY this bit", require an exact complement match (`(~imm32)>>>0 === target`). Containment answers a different question: "clears it among others". Compute `popcount(imm)`. If it's small, treat `imm` as the touched set. If it's large (a keep-most `andi`), treat `~imm`, truncated to the field width, as the touched set.
3. Before trusting a register-tracked constant in an `or`/`and` census, check its popcount. Real flag constants are small and sparse.
4. Trace the tested register's **provenance** to its root. If it comes from `jal <callee>`, credit it only after reading every path that sets the callee's return value and seeing that it forwards the field. A callee that reads or writes the field doesn't thereby return it.
5. A SET/CLEAR (producer) census must also require a store back to the same effective address (`sb`/`sh`/`sw`) after the `andi`/`ori`. Followed only by a branch, it's a test.
6. Run known-answer bits through the same census in the same pass: positive controls, plus a bit known to have only test sites and no producer. A "producer" hit on that bit means the store-back check is missing.

This applies to any containment-based census (ARM `AND`/`ORR`/`TST`, 68k `ANDI`/`ORI`, symbolic trackers) once the field has more than one mask width in play. Related, distinct mechanisms: `struct-field-scan-blind-to-biased-base-pointer.md` (a true negative hidden by addressing) and `sparse-table-creates-spurious-multibyte-field.md` (adjacency).

**Canonical example:** Valkyrie Profile (PSX, `valkyrie`), `obj+0xe4` bits 5/7. An `andi` census reported hits exactly at the three collision-dispatch gates that use the group masks `0xf0`/`0x2f0`. After excluding those two values, bits 4 and 6 (the positive controls) kept real individual sites and bits 5 and 7 dropped to zero, which was verified correct across the 369 KB overlay. A register-level `or` census in the same session also matched `0xfffffffd`, an AND-clear mask for bit 1.

**Variants:**
- Provenance (`obj+0xe8`, round 10): 5 sites `jal FUN_8002fee4; andi $r,$v0,0x4` were exact matches, but `$v0` is a locally built status code (0–4, +8) where 4 means "at rest". The two real `lw 0xe8; andi 4` sites in the same function looked identical downstream, so positive controls alone don't catch this.
- Test vs producer (`vp1psx-scene-script-opcodes` round 16): a global-word SET/CLEAR census counted `andi; beq/bne` tests as producers, and an ungated `0xfffe` matched every other bit.

**History:** 4 recorded shapes (`valkyrie`). Full log in `_archive/bitmask-containment-census-false-positive-for-individual-bit.md`.
