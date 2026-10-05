# A test fixture built from the same mental model as the code under test can't catch that model being wrong

**When it bites:** a decoder or VM test builds its input bytes or expected behaviour with a hand-written helper rather than from a real file or trace, and it has passed for a long time. Also: you're asked to (re-)confirm an order or offset that a dated "confirmed" comment, a doc, and passing tests already assert. Also (inverse): a hand-built fixture goes red against a guard.

A fixture builder written from the same understanding as the decoder encodes the same mistakes, so a field swap, wrong offset, inverted branch, or wrong stage order is invisible by construction, however many assertions the test has. This differs from `hand-computed-test-fixture-vs-real-run.md`, which is about hand-computing expected *outputs*. A dated citation, a code comment, and passing tests can look like three signals while all coming from one reading of the disassembly.

**Check / fix:**
- Whenever the format understanding changes, re-audit every bespoke fixture builder's field order and offsets. A builder can keep the pre-correction layout after the decoder is fixed, and vice versa. Prefer fixtures from real captured files or an independently written encoder.
- Regression tests for a suspected swap need genuinely **different** values in the two fields. A square or equal-valued case makes the swap a no-op.
- For branch or flag semantics, derive the expected path from the handler's own pointer-advance instructions and name options after the raw flag meaning. Add a real-ROM trace test whose next step can only be predicted from the real semantics (e.g. the inline payload is a call, so the step after the branch must be the callee's entry on one setting and `offset+7` on the other).
- When asked to confirm a fact, re-derive it from the primary source even if a dated citation exists, especially when the citation names only routine labels with no address range. Look for a shared register or variable that both routines touch; it settles order cheaply.
- Inverse: when a hand-built fixture fails, first ask whether that input can occur in a real file, and check it against a real instance before changing the code.

**Canonical example:** Three Hopes G1T extra-dims (`chimera`). The `buildG1TExtraDims()` test helper wrote `height` at `abs+0x14` and `width` at `+0x18`, the same wrong order `parseG1T` read, so `width=288,height=512` asserted cleanly. The swap was found by an escalation that derived the layout from decoded pixel content. Because 288≠512, the corrected fixture would fail under the old code, but a square case would not have.

**Variants:**
- FFV event VM (SNES, `ceres`): the `$F0` yes/no and `$E2` battle-result branches were both inverted, and `$09c4 & 1` means *party defeated*. Synthetic two-arm scripts couldn't see it. The fix renamed the option to `eventBattleDefeated` and added a trace test using a `CD xx xx FF` payload.
- FFVI damage (SNES, `ceres`): a dated comment, `data-structure.md`, and two tests all claimed variance/defense run before split/back-row/crit. Re-tracing `CalcAttackEffect` vs `CalcDmgMod` on `$11b0` showed the reverse order.
- Valkyrie Profile (PSX): a chain fixture at offset 0 was rejected by a correct guard (offset 0 aliases the header), so the fixture was impossible, not the parser broken.

**History:** 4 recorded instances (`chimera`, `ceres` ×2, `valkyrie`). Full log in `_archive/test-fixture-encodes-same-wrong-model-as-implementation.md`.
