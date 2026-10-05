# Re-verifying an old "this renders wrong" claim with a fresh standalone reimplementation can manufacture a false confirmation, not check it

**When it bites:** a project doc has an old, dated claim that some asset
"renders as noise/garbled/wrong" (or any other visual-defect claim), and the
plan to re-check it is to write a fresh, standalone probe script that
reimplements the decode/composite pipeline from scratch — rather than
calling the project's own current, already-verified, committed decoder
function.

## The trap

A freshly hand-rolled reimplementation is new code with no track record. If
it has its own undiagnosed bug, it can independently reproduce — or even
invent — the exact defect it was written to check for, and the result reads
as a second, independent confirmation of the original claim. It is not
independent: both "confirmations" are artifacts of buggy code, not of the
underlying data. The check gives false confidence instead of a real one,
and specifically fails in the direction that's hardest to notice — it makes
a wrong old claim look freshly re-validated instead of raising a new
question about the new code.

## Confirmed case

Valkyrie Profile (PSX, `valkyrie`), round 121: `data-structure.md` had a
dated note that two specific room-layer instances rendered as visible
noise (predating several later corrections to the shared room decoder). To
re-check whether the noise was still real, a standalone, from-scratch
tile+CLUT compositor script (not the project's committed `composeRoom`/
`parseRoomLayer` functions) was written and run against the same two
layers — and it rendered one of them as clear striated noise, appearing to
confirm the old claim. This was wrong: the standalone script had its own
bug (root cause not pinned down, and not worth chasing once superseded).
Switching to a technique built strictly **on top of** the real, unmodified,
already-verified decoder — patch the room's placement list so one specific
layer's index points at a nonexistent slot, render with the real
`composeRoom` both with and without that patch, and diff — showed the
layer is clean, coherent, correctly-positioned content. The original 2026-
08 "noise" observation was itself stale, and the standalone-script re-check
manufactured a second false positive for it via a completely unrelated bug.

## Fix

When re-verifying an old "this decodes/renders wrong" claim, prefer a
technique built strictly on top of the **current, already-committed,
already-verified** decode path over any fresh, standalone reimplementation
of the same pixel/byte pipeline:

- **Ablation/isolation diffing**: surgically remove or patch out the one
  element in question from the real input (a placement, a record, a
  layer reference) and diff the real decoder's output with vs. without it,
  rather than building a second renderer to look at the element alone.
- If a fresh reimplementation is unavoidable (e.g. checking the committed
  decoder itself for the first time), treat any surprising negative result
  from it with the same suspicion as a surprising positive — a from-scratch
  probe has no track record and needs its own independent sanity check
  (a known-good input, a cross-check against the committed path) before its
  output overturns or reconfirms an existing claim either way.

This is a sibling of `standard-codec-delegate-to-trusted-decoder-not-hand-
reimplementation.md` (prefer a trusted decoder over a hand-rolled one when
producing a decode) and `test-fixture-encodes-same-wrong-model-as-
implementation.md` (a fixture sharing the implementation's own wrong
assumption can't catch it) — but distinct from both: here the fresh
reimplementation is the *verifier* itself, being trusted to arbitrate an
existing claim about a *different*, already-more-verified code path, and
its own unrelated bug corrupts the arbitration.
