# Two agents editing the same shared source file live, in the same working tree, need to converge on the live contract, not each insist on their own

**When it bites:** `git status` at task start (or partway through) shows
files modified/created that you did not touch — especially a shared
decode-library file (`src/data/formats/<format>.ts` or equivalent) whose
symbol names or return shapes don't quite match what you just wrote, and
the task brief mentions a sibling game/session is working the same engine
family concurrently. This is a live collision, not a one-time surprise —
the other agent keeps editing while you work, so a single "check git
status once" pass is not enough.

**Confirmed on Fire Emblem: Three Houses / Fire Emblem Warriors (both
`chimera` project, no git worktree isolation between the two sessions):**
both a Three Houses session and a concurrently-running FE Warriors session
independently derived a G1M model-container parser from the same public
010 Editor template family, converging on field-for-field identical
`G1MFile`/`G1MGeometry`/`decodeAttribute` shapes — but the *exact* return
signature of the top-level `parseG1M(bytes, start)` entry point ping-ponged
between "returns `G1MFile` directly" and "returns `{file, end}`" **three
times** across a few minutes, as each session's own edits landed on top of
the other's in the same physical file with no lock, no branch, and no
worktree isolation. Blindly "fixing" the file to match your own design each
time you noticed a mismatch just re-triggers the next round.

**Fix:** when you discover mid-task that a shared source file has drifted
from what you expect and a sibling agent is plausibly the cause, do **not**
treat your own design as authoritative and rewrite the file to match it.
Instead: (1) re-read the file's *current* live state fresh, right before
editing — not your memory of it from a few tool calls ago; (2) look at
what already calls the shared symbol from the sibling's own pipeline code
(their `build-*.ts`/consumer file) to infer the contract they're actually
depending on *right now*; (3) converge your own call sites to match that
contract rather than changing the shared file's shape again; (4) if a
genuinely new capability is needed that the sibling's contract doesn't
cover (e.g. this session needed a chain-walking variant with an end
offset, the sibling didn't), add it under a **new, distinctly-named
export** instead of changing the shape of the export the other session
already depends on — this is what actually stopped the ping-pong (adding
`parseG1MWithEnd` alongside the sibling's already-settled `parseG1M`
rather than re-arguing its signature a fourth time). Re-run `tsc --noEmit`
across the whole project (not just your own files) after every such
resolution — it will show the *other* session's call sites breaking or
compiling clean against your change, which is the fastest signal of
whether you actually converged or just moved the collision.

**Same collision, prose-doc variant: a duplicate section-number heading,
not a duplicate code signature.** Confirmed on Valkyrie Profile (PSX,
`valkyrie`): both the main session and a concurrently-running `re-oracle`
escalation independently wrote a new `### 20.40` heading into the same
long-lived spec file (`data-structure.md`) at nearly the same moment —
detected the same way (repeated `Edit` "file has been modified since read"
errors, confirmed by polling `md5sum`/`wc -l` until two consecutive reads
agreed the file had stopped changing). The escalation self-resolved by
renumbering its own copy to `### 20.41` as a stopgap. Once the fork's task
showed completed and the file was stable, the concrete reconciliation
recipe was: (1) diff both versions and pick the more complete/correct one
(here, the escalation's — it had traced more callers and caught two defects
in the other draft); (2) delete the inferior duplicate section entirely,
not just its heading; (3) renumber the surviving section back down to the
number it should have had, including rewriting any "supplement to §N"
framing that only made sense while it was a second, later section; (4)
**grep the whole project's doc tree for stray references to the temporary
number** (`grep -rn "20\.41" docs/`), not just the file that collided —
cross-references in a sibling doc (here, `battle-logic.md`) can cite either
section number and need fixing too. Skipping step 4 leaves dangling
citations that silently point at a section number that no longer exists
anywhere.
