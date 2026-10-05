# When every per-unit overlay/module shares one fixed load address, a hand-copied instruction address from scrollback can silently name the WRONG unit

**When it bites:** an architecture loads many separately-compiled units (per-
room/per-level native code, bank-switched code, per-object behaviour
modules) at the **same fixed virtual/runtime base address** every time — so
the same literal address (e.g. `0x800899b0+0x1c8`) is a valid, plausible-
looking instruction location in *every* unit, not just the one you were just
reading. You have probed several different units in a row (one `probe`/
disassemble call per unit) over a long session, and you are now writing
verify-script check assertions from memory of the scrollback rather than
re-reading each dump at the moment you cite it.

**What happened:** decoding Valkyrie Profile 1's (PSX) per-room `TASK`
native modules (`valkyrie`), 18 room-resolved dispatch entries were hand-
disassembled across ~20 separate `probe-room-task-disasm.ts` calls in one
session, each against a *different* TOC slot but the *same* fixed module
base (`0x800899b0` — every room's native overlay loads there). When writing
the verify script's instruction-address assertions afterward, one check
for "id 55" (module/slot 3638) was accidentally populated with bytes that
actually came from "id 54" (module/slot 4705) — both modules happened to
have superficially similar-shaped code (`lui a0; addiu a0; jal findTask`)
sitting near the identical relative offset `0x8008a17c`-ish from the shared
base, and the two dumps had scrolled together in the session transcript.
The resulting check cited a `findTask` target address that was real and
byte-correct — just for the *other* module. Separately, roughly a dozen
individual checks across the same script had a plainer error: the operand
byte for one MIPS instruction (e.g. an `addiu`/`sb` pair) was assigned to
the address of the *following* or *preceding* instruction word — a
systematic ±4-byte (one instruction) drift that crept in from parsing a
dense, multi-screen hex dump by eye across many separate probe outputs
rather than re-reading a small window fresh at write time.

**Why structural checks didn't catch it:** every one of these mistakes
produces a **syntactically well-formed, semantically plausible-looking**
check — a real opcode encoding, a real address in the module's valid range,
matching the general shape the surrounding prose describes. Nothing about
the check "looks wrong" on inspection; only running it against the real
bytes (which is exactly what the project's `[PASS]`/`[FAIL]` verify-script
convention is for) surfaces the mismatch.

**Fix:**
1. **Never write a check's expected byte value from memory of an earlier
   scrollback dump.** If more than a few instructions have passed since you
   read the bytes for a specific address, re-run a small, tightly-scoped
   probe (a handful of words, not the whole function) at that exact address
   *in that exact unit* immediately before writing the assertion — cheap
   (a few seconds) relative to a wrong finding surviving into committed docs.
2. **Tag every intermediate note with its owning unit (slot/bank/overlay
   id), not just its address**, whenever a target has this fixed-shared-
   base architecture. An address alone is not a unique key here; treat
   `(unit, address)` as the citation, always.
3. **Run the verify script and treat every `[FAIL]` as a real, expected
   diagnostic signal to re-derive that one specific check from a fresh
   probe** — not as a sign the underlying finding or the whole approach is
   wrong. In this session all ~11 failures on first run were exactly this
   class of transcription slip; every one was fixed by a fresh, narrow
   re-probe of the cited address, and the underlying RE findings were
   correct throughout.
4. This is the address-level sibling of
   `hand-transcribed-generated-table-drifts-from-source.md` (which covers
   the same "a second manual pass is a second independent chance to
   introduce error" failure mode for name/enum tables) and
   `hand-traced-byte-shuffle-needs-independent-resimulation.md` (independent
   re-derivation over trusting a careful-feeling manual trace) — the fresh
   re-probe *is* the independent re-derivation step here.
