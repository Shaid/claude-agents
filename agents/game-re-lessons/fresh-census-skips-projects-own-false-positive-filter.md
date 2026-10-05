# A fresh probe you write from scratch can skip a false-positive filter the project already established

**When it bites:** writing a brand-new, throwaway census/probe script to
settle a specific open question ("how many real uses does opcode/field X
have"), on a project that has *already* documented — anywhere in its own
docs — that a naive/blind/structural scan over this exact corpus produces a
known population of false positives, distinguishable only by some specific
oracle (a boundary check, an entryIndex/jump-target cross-reference, a
minimum-count threshold, a magic-plus-context check). The new probe answers
a *different* question than the one that already-documented false-positive
population was found for, which makes it easy to forget the filter applies
here too. **Also fires when the "new" walk isn't fresh code at all** — an
already-committed, already-exercised helper function elsewhere in the
codebase can carry the identical gap, because it was validated against a
consumer that happens to be false-positive-tolerant (see the second
manifestation below).

Confirmed on Valkyrie Profile (PSX, `valkyrie` project), round 183: the
project's own `scene-script-vm.md` already documented, in general terms,
that a blind scan for scene-script content produces "~1,000 false
positives" per disc — SLZ/group-directory blocks that structurally satisfy
`parseSceneScript`'s header checks (valid `codeSize`, in-bounds string
table) without being real script content — and that the fix is an
"entryIndex boundary oracle" (the header's declared entry-point word index
must land on a real decoded instruction start; fake blocks fail this). A
fresh probe written to settle an unrelated question ("does opcode 7 ever
get used with an off-value that makes its 3-bit mask meaningful") iterated
every TOC slot's scene-script-shaped blocks directly (not via the project's
already-known-contaminated "blind `scanSlzBlocks`" path), which felt safe
enough to skip the filter — but the group-directory walk still visited the
same contaminated population. The result: 22 raw hits, several with
absurd `regionType` values (`3148048`) or huge `entryIndex` values with no
possible referent in a 4-word body — and a first pass very nearly wrote up
a detailed (and wrong) "20/22 are inert dead stores, 2/22 are live" analysis
built entirely on garbage, before re-deriving and applying the
already-established entryIndex check retroactively showed **all 22** were
false positives, and the real corpus-wide count was 0 — matching a
frequency column the project's own spec doc had already published
correctly.

**Fix:** before trusting a fresh census's raw hit count on a corpus this
project has *already* characterized as containing a specific false-positive
class, re-apply that project's own already-documented filter/oracle
explicitly in the new probe, even if the new probe's own question feels
unrelated to whatever question the filter was originally built for. A cheap
sanity check that would have caught this immediately: diff the fresh
census's count against the already-published table/frequency column for the
same item, if one exists — a mismatch (here: 22 raw vs. an already-published
`0`) is the tell to go looking for a missing filter before writing up either
number as ground truth.

## Second manifestation (2026-09-27, `valkyrie`, VP1 PSX, round 208): the "obvious" already-committed helper is the wrong walker, not a fresh probe at all

An 11th rigor spot-audit set out to re-derive `scene-script-vm.md` § 1's
headline corpus-size claim (1,118/1,013 scripts, 2,731,134/2,424,468
instructions, both discs) from scratch. The doc's own "how to reproduce
this" pointer named a script that turned out not to exist at all — a
distinct, adjacent trap (`build/vm/verify.ts` was never committed to the
repo *or* to git history, closer to `tracker-prose-is-not-evidence.md` than
to this file). Reaching for the next-best thing, an already-committed,
already-exercised helper in the same codebase
(`probe-object-kind-census.ts`'s exported `forEachSceneScript(raw, fn)`),
felt safe precisely because it wasn't a fresh throwaway probe — it was
real, tested, production-adjacent code. It still produced the wrong
population (1,424/1,296 scripts, ~30% too many) for exactly the reason this
file's first manifestation warns about: `forEachSceneScript` walks every
region where `parseSceneScript(data)` merely *succeeds*, with **no
`regionType` filter** and **no entryIndex-landing check** — because the
census it was actually written for tolerates false positives at zero cost
(a garbage "script" just contributes a null/degenerate row to that census
and gets ignored). Reproducing a corpus-*size* claim has no such tolerance;
every spurious hit inflates the headline number directly. The fix was to
walk every TOC slot directly, filter `regionType === SCENE_SCRIPT_REGION_TYPE`
(4), and require `starts.has(script.entryIndex)` — the identical
already-documented two-stage filter from the first manifestation, just
reached this time by discovering an existing helper's blind spot instead of
writing a naive scan from zero. After applying it, every number in the
original claim matched exactly, including an independent "14 rejected"
figure the original methodology had also published.

**Generalized fix, sharpened:** "fresh probe" in this file's title should be
read as "any code path you're about to trust for THIS census," not just
code you're about to write. An existing helper's correctness is scoped to
the consumer it was validated against; before reusing it for a new
consumer with a different false-positive tolerance (especially a bare
corpus-size/count claim, which has zero tolerance), check its own filter
predicate for the same regionType/boundary-oracle gates the project's other,
already-correct census code applies — don't infer safety from "this
function already exists and already has callers."
