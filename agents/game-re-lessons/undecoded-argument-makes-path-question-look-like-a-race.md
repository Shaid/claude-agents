# An unnamed argument, a shared gating flag, or a bounded-either-way outcome can settle a "race" outright — check before building machinery to order two mechanisms

**When it bites:** an open question is framed as *which of two writers/handlers/objects wins* or *which ordering applies* — "needs the per-frame driver's scheduling", "a timing question static analysis cannot settle", "needs live/emulator capture" — and you are about to build a scheduler trace or emulator harness to order them.

The tell of a wrong premise: the framing names an untraced mechanism (a scheduler, tick order) as the prerequisite, asserts the two mechanisms are "independently triggered" without checking one's entry gate against the other's side effects, or asks for live capture of an outcome when both mechanisms are already fully decoded. Usually one of three things dissolves the race into a reachability fact or an invariance proof — both stronger than a live capture, which would only ever show one ordering.

**Check / fix:**
1. **Decode every still-unnamed argument/flag** (`extra`, `unk`, `flags`, `arg3`) on the dispatch path to both writers. It may select which path runs at all. Tell: call sites differing only in that argument, where one also hand-rolls a copy of the other path's side effects (popup, SFX, string) — the duplication exists because the flag suppresses the generic path.
2. **Disassemble both mechanisms' own entry conditions** and look for a shared variable — one may be gated on a flag the other sets (close kin of `guarded-call-confirmed-called-but-precondition-unreachable.md`).
3. **If the ordering really is free, compute both orderings** with the already-ported formula against a *time-varying* input (not a constant) and diff the outputs; check per-frame equality and absence of drift.
4. **Null-control a path claim by recording the storing PC, not the value.** Patch the call site's argument (and separately `nop` the candidate store); when both paths store the same number, only writer identity distinguishes them.

**Canonical example:** Valkyrie Profile PSX (`valkyrie`), `battle-logic.md` § 63.8: "which slot-7 duration survives for Dampen Magic — the spell's `turn+3` at `0x8005ce6c` or `fcn.80046938`'s generic `turn+2` at `0x80046aa4`; ordering needs the apply driver's scheduling." The shared request routine `fcn.80077340(target, statusMask, extra)` had `extra` never revisited: it is an immediate-apply flag (`sll $v0,$s6,16` in a delay slot, then `or`/`sh` into `0x59e`). The spell passes `1`, so the status is active on return, `fcn.80046938` never runs on that path, and the real writer is a third function's already-active branch (`0x80046c90`). Nothing to schedule. 3 of 16 call sites pass `1`; all three hand-roll the popup/SFX.

**Variants (VP1 PSX):**
- *Shared gate* — Feathered Pocketwatch: a 20-frame fade-out writes `actor+0x04=5` at 30 frames; the menu fade-in writing `4` was called "independently triggered". Both fade-in call sites are gated on `ctx->0x111e == 0`, the freeze field the Pocketwatch sets and never clears, so the hard-write always lands first.
- *Free ordering, bounded outcome* — `FUN_80039b5c` commits a 96-slot actor array in slot order; a rider reads its anchor fresh or stale depending on runtime slot order. From `rider.x = anchor.x + xOffset`, `rider.y = anchor.y + velY + gravityVelY + yOffset`: either ordering tracks one axis exactly and is off by that frame's own velocity on the other, never accumulating. Confirmed by running the ported formula for both orders over 500 frames of sinusoidal anchor velocity.

Related: `gating-argument-may-be-a-compile-time-constant-not-data.md` (trace a gating argument's origin — it may be a literal).

**History:** 3 recorded instances (valkyrie VP1 PSX) — full log in `_archive/undecoded-argument-makes-path-question-look-like-a-race.md`.
