# An opcode census for "does any code reference this" is only as complete as its addressing-mode/register-class coverage

**When it bites:** a byte-pattern census for "does any code load/write/test/call X" (a struct offset, an A5/global slot, a table address, a call target, a mask constant) returns zero or too few hits and you are about to write "no consumer exists" — especially when sibling constants in the same family *did* hit with the same census.

A census matches one encoding; the compiler or hand-coder picks whichever encoding is shortest or most convenient per site. Zero hits measures the census's own coverage, not the target's reference count. A family where most members hit but one or two miss is a signal to widen coverage, not evidence of absence.

**Check / fix:** before concluding absence, enumerate every way the operation could be encoded, and run the full sweep routinely after the first hit (the negative is only trustworthy if the wide sweep ran):
- **Register class:** address-register loads (`MOVEA`/`ADDA`/`LEA`) *and* data-register loads (`MOVE.L …,Dn`) *and* compare/test forms (`CMPA`/`TST`); all 8 registers, not just the one in the first hit.
- **Addressing mode:** PC-relative *and* absolute-long immediate (`MOVEA.L #imm.L,An`); absolute *and* direct-page/zero-page (65816 `STA $21` after setting DP to `$2100`).
- **Encoding width:** `bra.b` and `bra.w`; `moveq` vs wider immediates.
- **Call form and entry point:** `jsr` *and* `jmp` (tail call) to the same target; every equivalent entry point (an unconditional sibling entry a few bytes past the wrapper, a shared trampoline).
- **Walked pointers:** a field reached via `lea $60(aN),aM` then `(aM)+` stores carries the displacement only in the `lea` — census the address computation, not just displaced accesses.
- **Mask construction:** `lui+ori`/`lui+addiu` *and* single `addiu $r,$zero,-N` (any mask whose signed 16-bit value fits); same idea for ARM `MVN` vs literal pool, x86 sign-extended imm8.
- **Dispatcher idioms:** a generic property/API dispatcher tests a bit with shift-then-mask (`SRL; XORI 1; ANDI 1`), not the inline `ANDI #mask` idiom — census both shapes from the start.
- **Strength reduction:** no `MULT` opcode and no constant bytes does not mean no multiply — symbolically trace nearby shift/add chains (`dsll`/`daddu`, x86 `LEA` chains, ARM `LSL`/`ADD`).
- **Control-flow shape:** a self-recursion census misses an iterative counted loop (`DBF`) calling a shared kernel.
- **Alternative anchor:** when an xref scan on the table's address fails, census a marker instruction the consumer's *body* must contain (a terminator compare such as `cmpi.b #$40,d0`) — independent of operand addressing and of linear-disassembly alignment.

**Canonical example:** Black Crypt Amiga `bcdfa` directory slot `0xE8`: a census of `MOVEA.L (d16,A5),An`/`ADDA.L (d16,A5),An` (all 8 An) found real consumers for sibling slots `0xD4`/`0xDC`/`0xB4`/`0xE0` but none for `0xE8`, written up as "no consumer exists" — which blocked identifying a 20,195-byte bank. The consumer used `MOVE.L (d16,A5),Dn`; widening to Dn forms found it immediately, plus two sibling slots' consumers within 40 bytes.

**Variants:**
- *Width + entry point undercount* — Knights of the Round (CPS1): `moveq`+`bra.w` census missed `bra.b` and a sibling entry; count rose from under 20 to 125.
- *PC-relative-only xref* — D&D Shadows over Mystara (CPS2, `kolbold`): monster-name table "zero references"; consumer used `MOVEA.L #imm.L`; found via a `cmpi.b #$40,d0` marker census (7 hits, 1 real).
- *Post-increment writes* — D&D Tower of Doom (CPS2): HP-init via `lea $60(a0),a4` + `move.w dN,(a4)+`; `move.w X,$60(An)` gave 6 unrelated hits, `lea $60(aN),aM` gave 26 incl. the 2 real ones (the prequel used displaced stores).
- *jsr/jmp + trampoline* — ddsom second enemy pool resolved 18/28 with the jsr-only `$1a32` census; adding `jmp` and the `$103d6` trampoline reached 25/28.
- *Single-`addiu` clear mask* — Valkyrie Profile PSX `obj+0xe8` bits 6/7 looked like a one-way latch for rounds because clears used `addiu $v1,$zero,-0x41`/`-0x81`; VP2 PS2: a "missing" `1664525` LCG multiply was a `dsll`/`daddu` chain; Midwinter (`hunter`): fractal generator was a 50-iteration `DBF` loop, not recursion.

Related: `lvo-byte-pattern-false-positive.md` and `indexed-operand-needs-base-provenance.md` (the false-positive face); `negative-from-addressing-root-not-shapes.md` (general fix).

**History:** 11 recorded instances (Black Crypt, kolbold KotR/ddsom/ddtod, valkyrie VP1/VP2, hunter, Urban Strike SNES) — full log in `_archive/narrow-opcode-form-census-false-negative.md`.
