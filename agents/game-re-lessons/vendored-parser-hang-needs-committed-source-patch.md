# A vendored third-party parser/decompiler hanging (not crashing) on real game data can need a deliberate, committed patch to its own source — not just a driver-side workaround

**When it bites:** driving a vendored, open-source parser/decompiler
(UELib, a community disassembler, any third-party library pulled in via a
`setup-<tool>.sh`-style vendoring script) against a *large, real* corpus of
game files, and one specific invocation runs far longer than any other
(minutes, not the sub-second cost every sibling file takes) with no crash
and no output — a hang, not an error. Especially when this only surfaces at
full-corpus scale, after a small development sample looked completely
healthy.

Confirmed on Drakengard 3 (PS3, `flower`): UELib's
`PackageFileSummary.Deserialize()` reads two optional trailing header
fields (`AdditionalPackagesToCook`, `TextureAllocations`) gated by a
version threshold this game's `ArVer` (860) clears — but this specific
title's own cooker never actually wrote either field. The garbage count
read back from whatever real bytes happen to follow sent the read loop
into a multi-minute stall (confirmed via a direct, non-piped `timeout`-
bounded invocation, not a Node-side artifact) instead of a fast exception —
on a real **majority** of this game's ~1,900 Level/Map packages, not a
rare one-off. A 5-file development sample never hit this because those
files' specific garbage bytes happened to produce plausible-looking small
counts or a fast EOF instead.

**Root-causing it**: bisect by adding temporary `Console.WriteLine`/print
statements immediately before and after each suspect read in the vendored
source (build, run against the one hanging file, observe which print line
never appears), then **revert the instrumentation** once the exact call
site is found (`git diff` on the vendored checkout should go back to
clean before deciding on a real fix) — this is much faster and more
certain than guessing from the stack trace of a *different*, already-
caught exception a few fields later.

**The fix that generalizes**: a *bounds check* on the declared count,
which the read loop was missing entirely (unlike a structurally identical
sibling field a few lines away, which had a `try/catch` but no bound —
demonstrating that "it's wrapped in a try/catch" is not the same
protection as "it can't run for a long time before throwing"). Two bound
designs were tried and rejected before finding the one that worked — worth
recording as its own sub-lesson, since both failure modes are easy to
reach for first:
- A bound relative to the **whole remaining file length** was too loose —
  a several-hundred-thousand garbage count still "fits" comfortably within
  an 8MB package and still stalls.
- A bound relative to a **nearby already-parsed offset field** (here, the
  package's own `NameOffset`) was too tight and produced false positives —
  on some real files this header region's own trailing optional fields
  legitimately extend past that offset (co-located with the start of
  whatever comes next), so the bound goes negative and rejects even a
  genuinely valid, harmless declared value of 0.
- What worked: a **hard, absolute cap** with no dependency on file size or
  other header fields at all — no real game ships more than a handful to a
  few dozen of "these optional per-package extras," so a generous fixed
  ceiling (tuned an order of magnitude above every legitimate value seen,
  well below every garbage value seen) cleanly separates the two
  populations.

**Apply the patch as a deliberate, version-controlled artifact, not a
one-off local edit that gets lost**: save it as a real `.patch` file
(`git diff` in the vendored checkout after fixing), commit it alongside
the project's own driver code, and have the `setup-<tool>.sh` vendoring
script apply it automatically and *idempotently* (check for a marker
comment in the target file before re-applying, so re-running setup from
scratch or against an already-patched checkout both work cleanly). This
keeps the fix reproducible for anyone who re-runs the setup script, and
keeps the pinned-vendored-commit convention honest (the patch is an
explicit, reviewable diff on top of a named commit, not a silent local
mutation). **Regression-check any other already-proven pipeline that goes
through the same vendored code path** after patching — here, re-running
the already-documented UnrealScript decompile pass (a completely different
consumer of the same `PackageFileSummary.Deserialize()`) reproduced its
exact prior byte-for-byte counts, confirming the patch only changed
behavior for the two fields it touched.