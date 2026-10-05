# A TODO.md/plan.md status claim — or a confident corpus-count number in the spec doc itself — survives unverified across session boundaries unless you re-derive it

**When it bites:** starting work on a TODO.md row (or a plan.md session-log
entry) whose description already reads as settled/confirmed, and you're
about to build the next step on top of it without opening the
`data-structure.md` section its Evidence column points to. **Also** bites
when `data-structure.md` itself states a specific whole-corpus count
("N instances counted recursively via a depth-4 walk") as if it were a
settled fact, and the probe script that produced it either wasn't
committed or no longer exists to audit — a session's plan built entirely
around explaining a "gap" against that number (why coverage is only 12 of
297, say) can spend a full pass rationalizing a number that was simply
wrong from the start, with no bug anywhere in the current code to find.
Confirmed on Drakengard (PS2, `flower` project): a prior session's
`docs/drakengard-cavia-archive-format.md` stated "297 instances [of
`mmodel.bin`] counted recursively" with no surviving probe script; a fresh
walker deliberately built to mirror the production `walkCaviaContainer`
exactly (container-name histogram, not a leaf-only scan) found the true
figure was **12** — self-consistent with every other already-shipped
count (LOD/animation container totals all divided evenly by 12, not 297).
The "297" wasn't a bug to explain, it was never correct. Fix for this
variant: before treating an unaudited whole-corpus count as a planning
premise, re-derive it with a walker that matches the real production code
path, not the prose.

Wizardry 6 Amiga's `docs/wizardry6/TODO.md` carried this row forward across
a full session boundary: *"Section 6 is now confirmed (400×32B monster
encounter/spawn groups, independently re-verified against the monster
catalog — e.g. record 5 decodes to a legible 7-species group)."* Confident
prose, a specific example, an "independently re-verified" claim — every
surface signal of a real result. It was never written into
`data-structure.md` or any investigations file at all — a whole-tree `grep`
for the claim's own supporting details (record counts, the "7-species
group" phrasing) found nothing. Dispatching a fresh agent to verify it from
scratch found it flatly **wrong**: section 6 is a general scripted
event/opcode table (message-display triggers, probability-gated recursion,
dice rolls), not monster data — refuted by fresh disassembly plus an exact
statistical cross-check (174/174 and 46/46 field matches against a
different, correct interpretation) that took under an hour to produce.

The failure isn't "an agent hallucinated" (this project's existing
`verify-escalation-artifacts-not-just-claims.md` already covers not trusting
specialist output blindly) — it's narrower and easier to miss: **the
project's own convention says tracker files (`TODO.md`, `plan.md`) point at
evidence, they don't contain it.** A well-written status row is
indistinguishable, by tone alone, from a genuinely verified one. Nothing
about *reading* the row tells you whether anyone ever actually chased its
Evidence pointer and found real disassembly/statistics behind it, versus a
plausible-sounding summary an agent wrote and a later session's own summary
just re-stated without re-checking.

**A ninth variant: the "how to reproduce this" pointer itself names a script
that was never committed at all — not stale, not wrong, simply absent from
both the working tree and git history.** Valkyrie Profile (PSX,
`valkyrie`)'s `scene-script-vm.md` § 1 cited `build/vm/verify.ts` as the way
to re-derive its own headline corpus-size claim (1,118/1,013 scripts,
2.4-2.7M instructions across both discs). A round-208 rigor audit found the
file doesn't exist on disk and `git log --all --follow` on that path returns
nothing — a stronger absence than
`local-decode-cache-may-be-stale-reverify-fresh.md`'s stale/wrong-length
cache (that lesson's artifact at least *exists*; this one's citation points
at a void). The correct response was still to re-derive the claim from
scratch rather than either trust it on prose alone or dismiss it as
unverifiable — doing so reproduced every published number exactly,
including an independent secondary figure (14 rejected candidates) the
original methodology had also reported. The general lesson is symmetric
with the rest of this file: a dead reproduce-pointer is exactly as much
reason to distrust a claim as a live-but-unopened one, but distrust is not
disproof — it's a mandate to actually re-run the derivation, and a genuinely
correct old claim surviving that re-derivation is a real (if unglamorous)
outcome, not a wasted round. See
`fresh-census-skips-projects-own-false-positive-filter.md`'s second
manifestation for what the fresh re-derivation itself had to get right once
the dead citation forced it.

**A tenth variant, the opposite polarity of every case above: a doc's own
`> Correction` block can UNDER-state what its own cited verify script
already covers, wasting a future round's effort re-deriving something
already done.** Valkyrie Profile (PSX, `valkyrie`), round 210: a prior
round's correction block for the SLZ compression container's header-field
checks narrated its re-verification as covering "the `decompressedSize`/
consumed-byte invariants... 5,000+4,881 subtype-1 blocks... and
8,645+8,131 subtype-2 blocks" — explicitly calling out subtypes 1 and 2,
never mentioning subtype 0. A later round, planning to extend the (still
small-sample-only per the prose) subtype-0 check to the full corpus,
opened the cited script itself before writing new code and found it
already looped over subtype-0 blocks too (127+127, both discs, 0
failures) — the script's own scope was wider than its citing paragraph's
prose ever said. Running the script fresh confirmed the check was already
done; no new work was needed, only a five-minute verification instead of a
new probe script. The fix mirrors the file's other variants exactly but in
the other direction: before spending effort re-deriving or extending a
claim a doc's prose calls incomplete, open (and re-run) the script the doc
itself cites as evidence — its actual code, not the paragraph summarizing
it, is the ground truth for what was checked.

The fix: before treating any TODO.md/plan.md claim as a starting assumption
for further work — not just before treating it as fully closed — open the
doc section its Evidence column names. If that section doesn't actually
contain the specific claim (not just related material), the claim has never
been substantiated regardless of how it reads, and needs to be re-derived
or refuted from scratch, not carried forward. This costs one `grep`/`Read`
and is cheap enough to do for every row you're about to build on, not just
ones that feel suspicious.

**An eleventh variant: the same citation-chain failure, but between two
*committed verify SCRIPTS* rather than between a script and a doc — and a
grep sweep that finds a whole POOL of instances at once, not just one.**
Valkyrie Profile (PSX, `valkyrie`), round 219: this project enforces "every
committed verify script must read live from both real disc images, not a
`build/cache/` blob." `verify-move-entry-field00-approach-offset.ts`'s own
header comment justified reading only a cached, single-disc overlay file
by citing a SIBLING script, `verify-actor04-register-compare.ts`'s
`loadSlot1490()`, as "this project's own already-established convention...
both discs cache byte-identical copies." That cited function's own comment
made the identical claim ("re-confirmed below rather than assumed") — but
its code only ever returned a single disc-1 entry; nothing was actually
re-confirmed anywhere. Two scripts, two confident citations, zero live
re-derivation at either end of the chain — the exact `tracker-prose`
failure shape, just instantiated between code comments instead of between
a tracker row and a spec section. The root mechanism that produced the
FIRST violation in the chain: a new verify-style script's header cited both
a verify-style sibling (which genuinely reads live from both discs) and
probe-style siblings (which legitimately read a cache, since probes are
throwaway) in the same breath, and copied the probe convention's file-path
constant instead of the verify convention's live-read helper — an easy
mistake when a project's script-naming convention (`probe-*.ts` vs.
`verify-*.ts`) carries an implicit rigor distinction the citing comment
didn't track. **The technique that scales past spot-checking one
instance:** grep every committed `verify-*.ts` for a cache-path file read
with no live-source import (e.g. `grep -l 'build/cache' verify-*.ts | xargs
grep -L 'vp-corpus'` or the project's equivalent) — this single query
surfaced 11 candidates on the first pass, and the first 3 checked in depth
(spanning early-to-late rounds of a 200+-round campaign) were *all* genuine
violations, including one whose closing TODO row's own regression test had
literally only ever run one disc's data (`vp1psx-collision-primitive-types`,
closed round ~9, extended to a second disc only in round 219 — the disc-2
numbers matched exactly once actually checked, so the underlying finding
was fine, only its verification rigor wasn't). Treat "does script X
actually read from where its own convention says it must" as its own grep-
sweepable audit category, separate from "is script X's claim correct" —
the two failure modes (wrong finding vs. right finding under insufficient
rigor) need different fixes and neither audit substitutes for the other.

**Follow-up, one round later (round 220): the "11 candidates" count above
was itself wrong — a wider grep found 13 MORE genuine violations the
original query missed entirely, all fixed the same way.** The prior
round's sweep query and fix pass (`verify-actor04-register-compare.ts`/
`verify-move-entry-field00-approach-offset.ts`, 2 of the 11 actually
fixed) left 9 unexamined; re-running an equivalent `grep -l 'build/cache'
verify-*.ts | xargs grep -L 'vp-corpus'`-shaped query the NEXT round,
against the current file set, turned up 13 additional scripts the earlier
pass's own query apparently never surfaced or never got to — none of them
newly written, all pre-existing at the time of the original sweep. The
practical lesson: treat a sweep's own reported hit COUNT as a snapshot of
what got checked that session, not a ceiling on how many real instances
exist — re-run the identical query (not a memory of its result) at the
start of any follow-up round that continues this class of remediation, and
diff the file list against what was actually fixed last time rather than
assuming "already swept" means "fully swept." A sweep that reports N and
fixes M<N candidates has, by construction, left N−M unconfirmed — don't
let "N candidates found" get remembered as "N candidates handled."

**A twelfth variant, two rounds later still (round 224): a genuinely
different sweep QUERY closes some of the gap the first two left, but the
query's own positive signal has a false-negative shape that lets a real
mixed-compliance violation hide in plain sight.** Round 221 had already
tried a third, differently-shaped query ("imports `vp-corpus.ts` AND
contains both `'disc1'` and `'disc2'` string literals") specifically
because it is independent of the `build/cache`-path grep the first two
rounds used, and it found 3 more real violations. Round 224's own spot-check
sample (6 previously-untouched scripts, chosen to avoid files any of rounds
219-223 had already touched) found a 7th: `verify-battle-anim-shared-
page-source.ts` reads its PRIMARY instruction-level claims (a jump table, a
VRAM-destination table, several dispatch-code checks) from a single
`readFileSync('build/cache/.../codeoverlay_slotN.bin')` call with zero live
disc reads — exactly what the first sweep's query targets — but the file
*also* imports `vp-corpus.ts` and iterates `for (const discId of
['disc1','disc2'])` for a SECONDARY claim later in the same file (a
whole-TOC content scan unrelated to the stale primary checks). Round 221's
own query (`imports vp-corpus.ts` AND `has both disc1/disc2 literals`)
would have scored this file as compliant on both counts, a clean FALSE
CLEAR — the secondary section's live, both-discs code satisfies the query's
positive signal while the primary section's stale single-disc read sits
untouched a few dozen lines away in the very same file. Neither of the
first two rounds' `build/cache`-path grep would have missed it (it's a
textbook hit for that query too), but round 221 never re-ran that ORIGINAL
query — it moved on to a differently-shaped one on the assumption that a
new query finds a disjoint set of new violations, when in fact a single
file can satisfy one query's positive signal while still failing the other
query's own check. **Fix, generalizing past this specific pair of queries:**
none of a compliance sweep's candidate queries are supersets of each other
just because they're both aimed at "verification-bar compliance" — a file
that imports the live-read helper and iterates both discs ANYWHERE in its
body is not thereby proven to use that helper for EVERY claim the file
makes, so "imports X and mentions both discs" is a real but weaker signal
than "every `check()`/assertion in this file traces back to a live,
both-discs read." When continuing a multi-round compliance-sweep campaign,
re-run every PRIOR round's query too (not just introduce a new one), and
for any file that already passed a structural query (import present, both
discs mentioned), still skim for a second, independent stale-read pattern
in the SAME file — e.g. a module-level `const overlay = readFileSync(...)`
or `Buffer` bound once at the top and reused by many `check()` calls further
down, which a per-file "does it read live somewhere" boolean can't
distinguish from "does it read live for its OWN primary claims."

**Round 225 (still `valkyrie`) ran the same per-claim skim as a deliberate,
scaled-up spot-check (5 previously-untouched scripts sampled at random) and
found the identical shape 5 more times, confirming this is not a rare edge
case — plus two sharper sub-shapes worth naming explicitly.** All 5 hits
were a disassembly-based Part (byte-exact instruction words, or a call-site/
dataflow census — i.e. exactly the "PRIMARY claims" class the twelfth
variant describes) reading one stale `build/cache/.../codeoverlay_slotN.bin`
snapshot while a separate Part in the same file already did a live,
both-discs TOC walk. Two of the five sharpen the pattern further: (a) one
guarded its stale read with `existsSync(...)` and, on a cache miss, printed
`SKIP` and moved on — silently passing zero checks rather than erroring or
falling back to a live read, the stealthiest failure mode in this family
since a missing cache produces no visible symptom at all, just quietly
fewer assertions; (b) another's "cross-disc byte-identity" check compared
**two different stale cache files to each other** (`SLUS_011.56` dated one
session, `SLUS_011.79` dated a different, later session) rather than either
to a live disc read — so a check that LOOKS like a both-discs comparison by
name and by argument count can still be 100% cache-only, with the
differently-dated timestamps themselves a free tell that the two snapshots
were never guaranteed to be mutually current. All 5 were fixed the same way
(a small `decodeOverlaySlotN(discId)` / `extractMainExecutable` helper,
looped over both discs) and re-verified with zero drift from the stale
bytes in every case — the compliance gap was real in all 5 regardless of
whether the cache itself happened to be stale.

**A fifth variant, this time about an EXTERNAL reference/community project's
own documented completion state rather than this project's own tracker:**
a prior session's TODO row characterized a still-open format as "algorithm
shape confirmed via the community catalog but not independently re-derived"
(LZSS) and "geometry solved by the community project for 2 of 23 opcode
families only" (TMD 3D models), based on that session's own read of a real,
actively-maintained community decompilation project
(`GabeRealB/parasite-eve-2-decomp`). Parasite Eve II (PSX,
`~/Development/parasite`): a later session cloned that same project fresh
rather than trusting the prior read, and found it had progressed enormously
in the interim — a complete, well-documented, working LZSS decoder, and
**all 23** TMD draw families fully mapped (not 2), each independently
confirmed against real disc bytes this session. Had the later session
trusted the stale "2 of 23" characterization, it would have spent
significant effort re-deriving (or worse, escalating as unsolvable) a
format the reference project had already fully solved. The general fix
mirrors the first four variants exactly, just aimed outward: a doc's
characterization of an *external* prior-art project's progress is itself a
tracker claim with a timestamp, not a permanent fact — before building on
"upstream only solved N of M" or "not yet independently verified" for a
still-active external project, re-fetch its current state (a fresh `git
clone`/`WebFetch` of its docs) rather than trusting a previous session's
snapshot of it, especially when re-deriving from scratch would be
expensive.

**A sixth variant, this time about a citation attached to the WRONG one of
two similar sibling items rather than a wrong or stale claim in general:**
a TODO row for Valkyrie Profile (PSX, `valkyrie`)'s player-character sprite
bank 3606 stated, with a specific citation, "its rooms' dialogue is mixed
(`Platina`/`Lucian` in the prologue, `Valkyrie` in Dipan-past)" — and the
"Dipan-past" half traced, elsewhere in the same doc, to a real, correctly
decoded speaker line at a real TOC slot. Running a full census (not a spot
check) of all 156 of bank 3606's own rooms found **zero** speaker
attributions in any of its 35 real `Castle of Dipan(past)` rooms — the cited
TOC slot (4192) turned out to belong to a *different* sprite bank's own room
set (3607's `Forest of Woe`), evidently conflated when a multi-bank
investigation's findings were condensed into one row. The citation itself
was real, correctly decoded evidence — just for a different item than the
one it was written under. This is a sharper failure than "unverified prose":
the claim reads exactly like the other, correctly-cited claims in the same
row (a real TOC slot, a real quoted line), so spotting it requires actually
re-deriving which item the cited slot belongs to, not just checking that the
citation resolves to *something* real. Generalizes to any doc investigating
several similar sibling items in one pass (adjacent IDs, overlapping
naming conventions, a shared "which one does this evidence belong to"
join) — before trusting a citation, re-derive which of the *several* items
under investigation it actually names, not just whether it's real.

**A fourth variant, caught on Millennium 2.2 (`methanoid` project):** a
pipeline's own header comments and `TODO.md` stated, across two separate
prior sessions, that three Data-tab tables (`note_pitch_table.json`,
`envelope_curves.json`, `arpeggio_tables.json`) were "registered in the
viewer's Data tab" — plausible-sounding, specific, and repeated verbatim a
session apart (which itself reads like corroboration). A `grep` of the
actual consumer, `tools/viewer/data-view.ts`'s `DATA_SOURCES_BY_GAME`
object, found none of the three ever listed — only the two palette tables
from an earlier session were. The claim wasn't a hallucination about game
data; it was a wiring step a session believed it had done (or meant to do)
that silently never landed, and no later session's own registration check
caught the gap because nobody had reason to doubt a routine-sounding "also
registered in the viewer" aside. This generalizes past corpus counts and
format claims to any doc assertion that a producer script's output is
*consumed* somewhere else in the codebase (a viewer registration, a
pipeline wiring, a manifest category) — that class of claim is just as
cheap to falsify (one `grep` for the referenced identifier in the claimed
consumer file) and just as easy to carry forward unverified.

**A seventh variant: an incidental, unhedged label dropped into a *format-spec
doc's own table* while investigating something else entirely, formatted
identically to the row's genuinely-verified neighbors.** Valkyrie Profile
(PSX, `valkyrie`)'s `scene-script-vm.md`: a round investigating `obj+0xe8`
bits 6/7 found, in passing, a reader site that also happened to test bit 13,
and its own results table named that bit "ledge-grab (bit 13, `0x2000`)" —
no hedge word, no "hypothesis," sitting in the same table format as rows
whose labels *were* derived from a full producer trace. A later round,
finally tracing bit 13's actual producer chain, found it has nothing to do
with ledges — it's an unrelated lift-and-throw task's internal "treat as
already settled" override, discoverable only by reading the SET side, which
the naming round never did. The tell distinguishing this from a genuinely
verified row (missed until the correction) was that every neighboring row in
the same table cited concrete SET-site addresses and a construction/property
mapping, while this one cited only the single TEST address it happened to be
read at — the row's own internal evidence density, not its prose confidence,
was the signal that it was a guess. **Fix, generalizing the existing rule
past `TODO.md`/`plan.md`:** the same discipline applies to any label written
inside a `data-structure.md`-style spec doc's own tables, not just tracker
files — before reusing a bit/field/enum's name in a later investigation,
check that its row actually cites a SET (producer) site, not only a TEST
(consumer) site; a label backed by only one side of the round-trip is exactly
as unverified as a bare TODO.md status line, even when it looks identical in
format to rows that did the full trace.

**An eighth variant: a "byte-identical across N instances/discs/platforms"
claim, and the pipeline helper everything downstream relies on silently only
ever reads ONE of them, justified by a doc citation rather than an executable
check.** Valkyrie Profile (PSX, `valkyrie`)'s `item-skill-system.md` § 5
stated "byte-identical in 6 places... md5 `d53acc...`, 6/6 identical" — a
specific hash, a specific count, from a real one-time escalation probe — and
the section had since accumulated several in-place correction blocks, which
reads as evidence of active scrutiny. But `collectItemTable()`, the function
`battle-data-corpus.test.ts`'s real (not synthetic) corpus assertions are
keyed to, reads **Disc 1 only**, and its own doc comment justifies that by
*citing this exact section* ("§ 5 for the item table") rather than checking
Disc 2 in code. The item-name join — the thing the section's headline claim
is actually about — had therefore never been independently decoded on Disc 2
at all, for the entire life of the finding. A round-206 rigor audit
(re-deriving the byte-identity across all 6 copies fresh, and re-running the
name-join on Disc 2 via the low-level primitives directly, bypassing the
disc1-only helper) found the original claim was in fact correct — but the gap
was real regardless of the outcome: nothing had ever executed the check on
the disc the doc's own citation was implicitly resting on. Generalizes past
discs to any multi-instance resource (per-region, per-platform, per-revision
copies of "the same" table/asset) where a helper function's own doc comment
says "reads instance A only, because instance B is already confirmed
identical — see § N," and § N's own evidence is a hash or byte-count quoted
from a probe that was never turned into a script anyone can re-run. The tell
is the same shape as the other variants — confident, specific, well-formatted
prose — but the executable proof covers a strict subset of what the prose
claims, and the citation loop (helper cites doc, doc's only evidence is a
one-time unscripted probe) can hide that indefinitely since nothing in it is
false, only unchecked.
