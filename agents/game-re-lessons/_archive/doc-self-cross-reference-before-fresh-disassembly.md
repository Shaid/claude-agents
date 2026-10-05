# A doc's own already-solved section can silently answer a different section's "still open" row

**When it bites:** about to write up a fresh disassembly finding as novel
before running the project's own full test suite — a passing describe-block
name/assertion for the exact mechanism you just "discovered" is a stronger,
cheaper duplication-detector than a doc grep, and can catch cases a grep
(keyed on the wrong address citation, or worded differently in the doc)
would miss; see the twenty-third instance below. Also: about to run — or
about to trust the completeness of a prior round's — the id-extraction-
and-diff sweep this file's twenty-fourth instance describes: a naive
per-line `grep -oE` for a hyphenated slug-style id silently undercounts
whenever an id wraps across a markdown line break or a blockquote/list-
continuation line, and the same sweep is worth running over a long-running
`plan.md`-style narrative/checklist file too, not just table-and-prose
docs — see the twenty-fifth instance below for both. Also: just wrote (or
are reviewing) a `> Correction` block that supersedes an earlier round's
own "exhaustive"/"every one of them"/"all N" claim — check whether that
earlier round also left behind a committed `verify-*.ts` script asserting
the now-superseded claim as one of its checks; if so it now fails (or,
worse, still passes on a check loose enough to no longer test anything
real) on every future re-run, silently or loudly breaking this campaign's
own "every committed script exits 0" rule — see the twenty-eighth instance
below. Also: about to
conclude — or about to accept a prior round's conclusion — that a struct
field's real-world value is a **runtime-only question static analysis
cannot answer** (the trigger for reaching for `re-oracle` or for a live-
capture request under standing rule 1) for a field that is itself part of
an already-decoded per-object property/opcode system (a scripting VM's
`SETPROP`/`GETPROP`-style dispatch, an event-parameter table): grep the
doc for that exact field's offset among the property table's own rows
first — a script-settable property's literal operand values are STATIC
disc-resident bytecode, not runtime state, and a corpus census of them can
settle "does this field ever take a non-default value" with no emulation
at all; see the twenty-seventh instance below. Also: about to start fresh
disassembly tracing on an item a
project's spec doc lists as open/unresolved (a "still open" table row, a
`TODO.md` residual) — especially when the item names a specific address,
table, global variable, or field that sounds like it could be shared
infrastructure (a per-level lookup table, a shared A5/frame-relative
pointer, a shared dispatch helper) rather than something unique to the
open item's own feature area. Also: about to trust (or about to write) a
dated status-update/"done" block's characterization of a specific asset —
see the addendum below. Also: a "no traced writer" / "still open" claim
lives in a **source-code doc comment** (not just a `docs/*.md` spec file)
— check the very next comment block in the *same source file* before
trusting it; see the fourteenth instance below. Also: a `> Correction`
block itself claims that ANOTHER section's text "was never updated in
place" / "still reads as superseded elsewhere" — before trusting that
claim (or repeating it in a fix), `git log -S` the exact phrase and check
whether the in-place fix it says is missing actually landed in the very
same commit as the claim; see the sixteenth instance below. Also: two
large sibling docs describe overlapping content (e.g. a byte-level "engine
spec" and a narrative "investigation log" for the same subsystem) and
there is no specific flagged item to check yet — a proactive cross-doc
token sweep (not a reactive single-item grep) can surface drift neither
doc's own text would ever flag as self-contradictory; see the seventeenth
instance below for the technique and its own false-positive trap. Also: a
prior round already claimed to have found and fixed "N further stale
copies" of one specific refuted claim (a correction block says so) — don't
trust that tally or scope a re-check to sections downstream of the
correction; grep the exact phrase across the WHOLE doc in both directions
of file order plus source-code doc comments before believing the sweep is
done; see the nineteenth instance below. Also: a project maintains a
canonical per-record/per-opcode `summary`/`description` STRING LITERAL
inside a source-code data array (not a `/** doc comment */`, a plain
`string` field a `.md` table is generated from or mirrors) — grep
`tools/shared/*.ts`/`tools/<game>/*.ts` for that array's stale copies too,
not just `docs/**/*.md` and standalone doc comments; see the twenty-first
instance below. When triaging which of several restatements to fix first
under a time budget, a restatement in a DIFFERENT file from the correction
is the higher-priority miss — a same-file, same-section-or-next restatement
is more often tolerable forward-pointing (the campaign's own convention
allows "fixed one section over," see the twentieth instance's file for a
worked example) than a genuinely unreconciled gap; see the twenty-first
instance below for why. Also: a **source-code comment cites a specific
`docs/*.md` section number as justification for a claim** (most often
"resource X is byte-identical across discs/builds/regions, see § N") —
before propagating that claim into new code or a new verify script, open
the cited section and check it actually establishes the claim, not just
that a section with that number exists and discusses the same general
area; see the twenty-sixth instance below, where the cited section
established something adjacent (a load-base correction) but never once
mentioned the byte-identity claim the code comment attributed to it.

Large format-spec docs accumulate dozens of independently-written sections
over many sessions. A section written early can fully solve a table or
write site, complete with address and verification, while a *different*
section written later — describing a different consumer of that same
table — still calls its own copy of the question "not verified, no write
site searched for," because nobody grepped the doc for the address/table
name before writing that later section. The two sections never got linked.

Confirmed on Black Crypt (Amiga, `crawl` project): the viewport-rendering
section's "Still open" table listed `$51A(A5)` — "the door-family position
variant... when nonzero each adds +0x24 to its position table... almost
certainly 'this doorway square also carries a door frame' — not verified,
no write site searched for." A direct disassembly search for the write
site found it in one instruction, and the value it stores comes from a
13-entry per-*level* lookup table — which turned out to be the **exact**
table already fully decoded, named, and verified five independent ways in
a completely different, already-`**SOLVED**`-tagged section of the same
document ("Dungeon tileset selection" → "Selector 1 — per-level default"),
which even already listed `$51A(A5)` by name as one of that table's three
known readers. The "still open" row's entire premise (a per-door
condition) was wrong; the real answer had been sitting fully solved
elsewhere in the same file the whole time, just never cross-linked.

**Fix:** before disassembling anything new for a "still open" item, `grep`
the whole spec doc (not just the section the item lives in) for the exact
address/offset/hex-constant/global-variable name the item cites. If it
turns up in an already-`SOLVED`/`confirmed` section elsewhere, read that
section first — the answer, or most of it, may already be written down,
just not linked to the item that needs it. This costs one grep and can
save a full disassembly pass, and it generalizes past this one field: any
doc built incrementally across many sessions is at risk of solving the
same fact twice under two different names, or solving it once and leaving
a sibling "still open" row unaware of the fact.

This is the doc-authoring-time twin of
`working-tree-may-already-solve-a-docs-open-item.md` (which checks whether
*uncommitted code* is ahead of the docs) — here the docs themselves are
internally ahead of one of their own rows, and a plain text search of the
committed file is the fix, not `git status`.

**Addendum — the newest text in a doc is not automatically the most
correct.** The same failure mode runs in reverse: a dated "status
update"/"done" block appended to a doc can itself be wrong even though
it's the most recent writing, if it never cross-checked an *older* but
still-standing section describing the same asset. Confirmed on Phantasie
III (Amiga, `nicodemus` project): an implementation-status update dated
2026-08-18 called `Dng.csh` "a 320×200 picture that is ~99% flat black
with a thin border frame... no per-cell tile set", and built a whole
flat-colour dungeon renderer on that conclusion — directly contradicting
a `graphics-formats.md` render-verification section written a week
earlier that had *already* correctly characterized the same file as
"small icon sprites... scattered... near the top-left", i.e. an icon
bank, not a backdrop. The newer pass never grepped the doc for the
file's own name before writing a confident "confirmed" verdict about it.
**Fix, generalized from the base lesson:** before trusting *or writing* a
status-update/"done" block's characterization of a specific asset/file/
table as ground truth, grep the whole doc (not just the section being
updated) for that asset's name — a "confirmed" claim from an earlier pass
is not superseded just because a later block sounds more current.

**A second, later confirmed hit on the exact same project — the trap
recurs even when you already know it exists.** Valkyrie Profile (PSX,
`valkyrie` project): a full investigation round (code trace of a resource-
type handler, plus rendering a probe image and visually inspecting it) was
spent deriving that a slot-directory "type 12" tag decodes to a small
16-colour CLUT/palette bank, with a confirmed structural invariant
(`regionSize == 12 + 2×nx×ny`). Only *after* landing that conclusion did a
`grep -n "type-12"` across the same spec doc turn up that this exact
structure — same invariant, described as "16×16 5:5:5 CLUT bank" — had
already been found once before, completely independently, in a different
section of the very same document (a different slot, a different
investigation topic, a data-side-only decode with no code trace). The new
work wasn't wasted (it added the missing consumer-code trace and a
rendered confirmation), but the core structural rediscovery was pure
duplication a five-second grep would have caught before any tracing
started. **Sharpened fix:** grep for the *exact* type/tag/region-id
number under investigation (not just a broader keyword) across the whole
doc *before* writing the first disassembly instruction or probe script —
do this even in a session that already harvested this exact lesson
earlier, and even when the current section's own local context gives no
hint that the tag was ever seen elsewhere. Recurring on the same project
is itself informative: a spec doc built incrementally across dozens of
sessions accumulates cross-reference gaps faster than any one session
tends to remember to check for them.

**A third confirmed hit on the same project — and this time the check was
never run at all, across a whole multi-technique investigation, right up
to the point of escalation.** Valkyrie Profile (PSX, `valkyrie` project):
spent a full pass running a **6-angle static census** (literal-immediate
store-instruction scans across every top-level code overlay, 551 enemy
behaviour modules, 104 party behaviour modules, and 101 previously-
uncensused nested code blocks, plus a dedicated check for the project's
own separately-documented "bulk `memcpy` defeats an offset census" blind
spot) hunting for the writer of a specific struct field
(`word[actor+0x570]`). Wrote up all six angles as a well-documented
negative and escalated to `re-codebreaker`. The escalation's *first* move
was `grep '0x570' docs/` — the answer was sitting in the same project's
own `battle-logic.md`, verbatim (`word[actor + 0x570] = rec; //
<address> back-pointer`), committed by a *different, unrelated sibling
session* working a separate problem four hours earlier the same day. Not
one of the six census angles ever included reading the project's own
existing documentation for the literal field offset under investigation —
the search was exhaustive across *code* but never touched the *docs*.
**Sharpened fix, again:** the doc/grep check is not a step you do once at
the top of an investigation and then move on from — it has to be
satisfied again before a paths-tried table is considered complete enough
to write up or escalate. A "well-documented negative across N distinct
search angles" is evidence that N *code* searches were performed
correctly; it is not evidence the *docs* were ever searched, and those are
different questions that both need answering before escalating. Treat
"did I grep the project's own docs for this exact offset/address/table
name" as a mandatory line in the paths-tried table itself, not an
implicit assumption — if that line is missing, the table isn't done, no
matter how many code-side angles it lists.

**A fourth confirmed hit, same project — and this time the missed
cross-reference wasn't in `docs/` at all, it was in a shared decode
library's own source comment.** Valkyrie Profile 2 (PS2, `valkyrie`
project): a mystery lead (`"onoda"`/`"onodb"`, short lowercase strings
found near a `PAMM` record's own embedded `FIS\0` texture tag) survived
two full passes — every text cipher tried and refuted, then a real
structural anchor found (the tag sits a fixed 20 bytes past the `FIS\0`
magic) but the standard `FIS\0` decoder rendered only structured noise,
leaving it written up as "a real, caught-in-time overclaim, not a
solved mystery." It was solved on a third pass not by new disassembly
or a new cipher, but by re-reading `tools/shared/ps2-fis-image.ts`'s
own module-level doc comment — written during an *earlier, unrelated*
CLUT/sub-palette (`TEX0.CSA`) investigation, it already named and
characterized a real field at chunk-descriptor offset `0x14-0x19` as "a
short ASCII exporter-session tag ... unrelated to GS state." `0x14` =
20 decimal — the exact offset already on record for the `onoda` tag —
but the two findings, sitting in two different investigative threads
months apart, were never connected. **Sharpened fix, extended past
`docs/`:** the cross-reference search this lesson demands has to cover
the whole project's **shared decode-library source comments** too, not
just `docs/*.md` spec files — a format module's own JSDoc/header
comment is exactly the kind of place an earlier, unrelated pass records
a real field it found and characterized without giving it a name that
a later, differently-framed mystery would ever think to grep for. When
a byte-offset or structural-shape finding looks like a still-open
mystery, grep both the docs *and* every shared module touching the same
container/tag family for the same relative offset before assuming
nobody has seen it before.

**A fifth and sixth confirmed hit, same project, same session — and this
time the missing link was a numeric census result and a narrow-but-general
schema, not a name or address.** Valkyrie Profile (PSX, `valkyrie`
project):

- A `TODO.md` row proposed, as "the next step, not attempted," a
  corpus-wide byte census of a specific record field for one literal
  value. A *different* section of the same spec doc, written days earlier
  for an unrelated reason (confirming what that field's value meant, not
  whether it could equal this literal), had already run that exact census
  and published its result as a closed-form value set with 0 deviations —
  which made the "next step" answerable by inspection of an existing
  table, with no new search needed at all.
- A "Still open" row asked for a background-art discriminator no session
  had found yet. The exact discriminator — a specific 5-tag structural
  schema — was already written down in a *different* section of the same
  doc, derived by hand for one 51-slot population and never generalized.
  Applying it corpus-wide (a few minutes' work once found) resolved the
  open row almost completely. **This is a distinct flavor worth naming
  separately: the fix isn't always "the answer is already fully solved,
  just re-link it" — sometimes it's "a narrow, already-solved instance
  already contains the general answer, it just hasn't been scaled up
  yet."** Any doc row that reads "found for slot/case X, not yet checked
  elsewhere" is a live candidate for exactly this: before treating a
  sibling "no discriminator found" row as needing fresh work, check
  whether an existing narrow finding already generalizes.

A third near-miss the same session shows the fix working as intended, not
failing: before writing a "plausible, unconfirmed" semantic guess for two
slots (based on proximity to an already-confirmed neighbor) into the doc,
the actual content was decoded first — and turned out to be real text that
was already documented and shipped, under a different name, in yet another
section of the same doc. Catching this *before* commit (by verifying
instead of just writing the plausible-sounding guess) is the same
discipline this lesson has been arguing for all along, just applied
proactively instead of after an escalation caught it.

**This is the same doc, hit for the fifth and sixth time by the same
underlying failure, across at least four separate sessions.** The
generalized fix stands, but the recurrence rate on one project is itself
the strongest evidence in this file: treat "grep the whole doc for the
literal field/value/schema under investigation, including nearby
*already-answered* rows that might already contain the general case" as
the actual **first** move on any "still open" item, not a check to run
only after a search comes up empty.

**A seventh confirmed hit, different project, and this time it reached
`re-oracle` — the contradiction the escalation was called for dissolved in
one grep.** Fire Emblem: Three Houses (Switch, `chimera`): a pass wrote a
"current-format roster-array location NOT found" section (with a refuted
hypothesis, a failed brute-force scan, and a proposed next step) into
`docs/fe-threehouses.md`, and a `TODO.md` row to match — while the **same
document**, ~13,000 lines earlier, already held a "Save format CONFIRMED
against real bytes" section that had solved that exact array in the current
format (stride `0x24C`), applied a live patch to it, root-caused the crash
that followed, and shipped an executable patch. The later pass never
grepped the doc for `Characters[60]`, `0x24C`, or "save"; it had also read
a *different* community editor fork covering only the older revision (see
`reference-tool-data-revision-mismatch.md`). **Two sharpened rules:** (1) an
escalation brief that says "prior pass found X only on the old format /
old build / one platform" is itself the trigger — before deriving anything,
grep the target doc for the structure's name and every offset/stride
constant the brief cites; (2) when a doc is long enough that a section
written two weeks ago is out of any one session's context (this one was
23,000+ lines), the grep is the *only* memory — treat "grep hit nothing"
as a prerequisite line in the write-up, the same way the third instance
above demands it in the paths-tried table.

**An eighth confirmed instance, same project, sharpens the framing to
"an exhaustively-enumerated id table is a free lookup service."** Valkyrie
Profile (PSX, `valkyrie`), round 12 of the `vp1psx-scene-script-opcodes`
campaign: three still-open per-bit rows of a struct flag-word investigation
(`obj+0xe8` bits 5 and 9, plus a 3-bit packed field at bits 14/15/16) closed
without any new disassembly beyond confirming a native consumer, because
`scene-script-vm.md`'s own GETPROP/SETPROP opcode sections (§§ 11.2/12.2)
already listed **every** script-facing property id and the exact struct
bit each one reads or writes — a complete id→bit map sitting a few thousand
lines away from the bit-level investigation that kept treating those same
bits as unexplained native-only mysteries. The generalized shape: whenever
a project has *already* built a complete, closed-form id/opcode→field
lookup table for one subsystem (a property-setter dispatch, an event-code
table, a state-machine transition list), and a *separate* investigation
elsewhere in the same doc is hunting for "what does bit/field N do" on that
same struct, check the existing table for N **before** writing a single new
disassembly probe — a fully-enumerated table has already answered every
question that can be phrased as "which id/opcode touches this field,"
whether or not the two investigations were ever explicitly linked.

**A ninth confirmed instance, same project — the cross-reference to grep
for was a bare mask CONSTANT, not a field name.** Valkyrie Profile (PSX,
`valkyrie`), `obj+0xe8` bit 17: five census rounds and a `re-oracle`
escalation later, the consumer turned out to be described twice in the same
doc already — once as prose ("a bit-`0x20000`-gated clear-and-zero-velocity
step", round 6, word unnamed) and once as a census-table row that literally
labelled the site "`e8` bit 17" while a different round was hunting
`obj+0xe4`'s bit 17. Every prior grep had keyed on the field offset
(`0xe8`); a grep for the mask value itself (`0x20000`, `0xfffd`) would have
landed on both. **Sharpened fix:** for a bit-flag item, grep the doc for
the *mask constant and its complement halves*, not only the struct offset
or bit number — sibling investigations of a different field's same-numbered
bit record their hits under the constant, not under your field's name. See
`field-centric-bit-census-blind-to-sibling-reuse-and-split-mask.md`.

**A tenth confirmed instance, same project — an exact ADDRESS grep can miss
because the doc cites the function's own INTERIOR body, not its entry
point.** Valkyrie Profile (PSX, `valkyrie`), round 22 of the
`vp1psx-scene-script-opcodes` campaign: a round-21 census flagged
`0x80065b6c` as a brand-new, previously-uncatalogued sibling task function.
A plain `grep -n "80065b6c"` across every doc in the project came back
empty, seemingly confirming "no prior citation anywhere." It was actually
round 10's own already-fully-traced "scripted group-motion task" — round 10
had simply cited a different address, `0x80065b90`, 0x24 bytes (6
instructions) past this function's real prologue, because that's where the
specific mechanism it was documenting (a 7-slot member loop) happened to
begin, not where the function itself starts. The exact-address grep is
blind to this by construction: two different, equally valid citations of
the "same" function (entry point vs. a body landmark) don't share a
substring. **Fix:** when a fresh disassembly at address X shares strong
structural fingerprints with an already-documented mechanism (same field
offsets, same called-function addresses, same distinctive constants) but a
literal grep for X itself comes back empty, don't stop at the negative —
disassemble backward from X (or from any interior landmark you already
recognize) to find the function's real prologue, and grep for THAT address
too, plus the distinctive constants/callees themselves. An address-only
grep proves "this exact byte offset was never cited," not "this function
was never documented" — those are different claims, and a doc's own
citation convention (which point inside a function it happened to quote)
decides which one you actually tested.

**An eleventh confirmed instance sharpens the trigger itself: once a long
campaign's structured `TODO.md` rows run dry of tractable items, grep the
whole doc tree for informal "still not resolved" prose markers, not just
a named open row.** Valkyrie Profile (PSX, `valkyrie`), round 150+ of the
standing "determine all PSX gameplay logic" campaign: every `TODO.md` row
still open was either explicitly excluded, already escalated with a
hardened negative, or cosmetic/audio (no tractable new angle). Rather than
re-trying an exhausted item, a plain `grep -n "unnamed\|not yet named"`
across the whole `docs/<game>/psx/*.md` tree (not scoped to any specific
open row — nothing in `TODO.md` even pointed here) turned up a small,
untracked, real gap: a battle-formula section had flagged "a second,
unnamed item id `489`" and left its consumer as "not traced further this
pass." Both halves were already answered elsewhere in the same doc's own
already-shipped item-name-table decoder (a byte-exact, anchor-checked
lookup nobody had run against this specific id) and a sibling section's
own already-confirmed consumer trace, written the same week — never
cross-linked, and never promoted to its own `TODO.md` row, so no
structured-row search would ever have surfaced it. **Generalized fix:**
in a campaign whose tracked open items have genuinely run out, the next
productive move isn't re-trying a harder static angle on an excluded/
escalated row — it's a full-doc-tree grep for informal micro-residual
markers ("unnamed", "not yet named", "role open", "not proven", "still
unnamed") that got left inline in an otherwise-resolved section and never
got their own tracked row. These are cheap to find and often already
answerable purely by cross-referencing the project's own other
already-decoded tables/sections, exactly as the base lesson describes —
the only change here is *where the candidate "still open" item comes
from* when there's no row left to start from.

**The same round surfaced a free, cheap proofreading signal worth
generalizing on its own: a doc's own natural-language count disagreeing
with its own explicit list is itself a defect worth re-verifying, not just
a typo to shrug off.** Round 21's summary sentence read "...and 4 more
found fresh this round with no prior citation... `0x80062f38`,
`0x800633a0`, `0x80063ec4`, `0x80065084`, `0x80065b6c`" — five addresses
listed after a prose count of "4 more." Independently disassembling each
listed address's own real prologue (rather than trusting the round's own
"all N share this idiom" attribution) found that `0x80065b6c` (the tenth
instance above) didn't actually match the claimed dispatch idiom at all —
resolving the arithmetic discrepancy after the fact ("2 already named + 4
new = 6" is consistent; the fifth address was simply misfiled). **Fix:**
when a doc's own stated count and its own explicit list disagree by
exactly one (or any amount), treat that mismatch as a free, already-paid-for
signal that at least one entry in the list doesn't belong — re-verify every
item independently before extending or trusting the batch attribution,
rather than assuming it's a harmless wording slip.

**A twelfth confirmed instance sharpens the eleventh's own fix: a grep hit
found via the inline-marker sweep can itself be stale, and a matching
`verify-*.ts` script's existence is a faster tell than reading the whole
section.** Valkyrie Profile (PSX, `valkyrie`), the very next round after the
eleventh instance above: the same full-doc-tree marker grep surfaced
`battle-logic.md` sections 88-89, which named four still-open "enemy audio
tag" residuals with no `TODO.md` row -- a textbook match for the eleventh
instance's own trigger. Before spending a disassembly pass on them, a check
of whether a correspondingly-named tool already existed
(`tools/valkyrieprofile/verify-enemy-audio-tag-residuals.ts`) found one, and
`git log --oneline -- <that path>` showed a commit (`aae0fec`) titled
"...section 93: close all 3 residuals" -- a **later section in the identical
file** had already closed the exact residuals sections 88-89 still described
as open. The grep hit was real, but it was pointing at prose the document's
own later content had superseded in place, with no cross-link back and no
strikethrough on the earlier section. A second candidate from the same sweep
round (a writer cited from `dungeon-field-mechanics.md` lines 7140-7159)
turned out to be settled a few hundred lines later in the very same file
(section 21.24.2, line 8108+) -- the same shape, just without a script to
shortcut it. **Fix, layered on top of the eleventh instance:** an inline
"still open" marker found by grep is not itself ground truth that the item
is open -- before disassembling anything, (1) grep *forward* in the same
file past the marker's own section number for a higher-numbered section
describing the same field/table/id (this project numbers sections
monotonically by when they were written, so a higher number is always later
in time even when it isn't adjacent in the file), and (2) check whether a
plausibly-named `tools/`/`scripts/` file already exists for the exact
residual and, if so, run `git log --oneline -- <path>` on it before writing
a single new probe -- an existing verify script whose name matches your
"open" item is strong, near-free evidence the item was already closed by
whoever wrote it, and the closing commit's message will usually name the
very section that superseded the one you're looking at. This generalizes
past this one project: any doc built by monotonically-numbered sections (not
just this one) can have an early section's "still open" framing survive
un-struck after a later section answers it, and checking forward-in-file
plus committed-tooling history is cheaper than re-deriving the answer from
scratch.

**A thirteenth confirmed instance adds two refinements: staleness can occur
between two sections written the *same day*, and the fastest cross-check for
a residual is often the `TODO.md` row's own id string, not the address.**
Valkyrie Profile (PSX, `valkyrie`), round 162: a sweep of `battle-engine-spec.md`
found a "resolved" synthesis block dated 2026-09-05 (§10.2, "every item in
§10.1 is now resolved or closed") that had itself already gone stale by the
time of writing — a *later* pass the same day (§7.2.5) inverted a mechanism's
polarity (a documented "debuff" turned out to be a "cure" on the opposite
side) without ever being cross-linked back into the §10.2 synthesis, or into
the original command-code table both sections were describing. Date-based
reasoning ("this is the newest dated block, so it must be current") is not a
safe proxy for write-order within a single day when a doc accumulates several
independently-written passes between morning and evening. Separately, while
writing a correction that itself cited an "open residual" (a persistence-write
instruction not yet located), a `grep` of `TODO.md` for the exact TODO id name
mentioned in that residual's own text (`vp1psx-code3-cure-persistence-write`)
found the row already marked `resolved`, pointing at yet a third section
(§53.1) that had closed it two sections after the one first cited. **Fix,
layered on the twelfth instance:** (1) don't trust same-day dating as proof of
write-order — a section's physical position later in the file is still the
better ordering signal than its date stamp when several passes share one day;
(2) whenever a residual/open-item mention names or implies a `TODO.md` id
(even informally, e.g. "this is `vp1psx-foo`'s last open item"), grep
`TODO.md` for that literal id string before writing a correction that repeats
or extends the "still open" framing — a `resolved` status there is decisive
and cheaper than re-deriving whether the residual was closed by re-reading
prose.

**A fifteenth confirmed instance widens the trap two more ways: the
mistranscribed citation can be a TABLE'S OWN BASE ADDRESS (not just a jump
target), and a `> Correction` block can sit directly ABOVE its own
section's now-stale conclusion with zero distance between them —
found three fresh instances of the second shape in one session by
systematically checking every Correction block against the paragraph
immediately following it.** Valkyrie Profile (PSX, `valkyrie`), round 165:

- A dispatch function's jump-table base address had been transcribed as
  `0x8008ba0c`, one hex digit off from the real `0x8007ba0c` — computable
  in one line from the cited `lui $at,0x8008 / addu $at,$at,$v0 / lw
  $v0,-0x45f4($at)` operand bytes (`0x80080000 - 0x45f4 = 0x8007ba0c`).
  The wrong address happened to fall in a *different* code region (a
  per-encounter module window, not this function's own overlay), so
  nobody had re-derived it from the operands until this round did. This
  is the same "re-derive from the cited call site's own bytes" fix the
  base lesson already teaches for jump *targets*, just never previously
  triggered for a table *base* an index is later added to.
- Three separate `> **Correction (date, ...)**` blocks, in three different
  doc files, were each immediately followed by a paragraph — the
  section's own PRE-correction conclusion — that had never been struck
  through or reconciled, so the doc asserted the refuted claim and its
  refutation back-to-back with no acknowledgment either way: (1)
  `battle-logic.md` §29.5's Correction named two real confirmed consumers
  for two struct bytes; the very next paragraph, "Verdict," still called
  those same bytes' consumer status unconfirmed. (2) A stale field-table
  row in a sibling doc (`data-structure.md`) had never been backported at
  all from a `battle-logic.md` correction dated 13 days earlier — found by
  systematically grepping every `record+0x`/`actor+0x` offset appearing
  inside a `> Correction` block against `data-structure.md`'s per-field
  table for the same offset. (3) A "the master dispatcher is unreachable"
  finding was itself corrected by a later `re-oracle` pass in one section,
  but a trailing paragraph in that *same* section, a second doc's inline
  correction note, and a `TODO.md` row all still asserted the pre-
  correction "unreachable and unexplained" claim, none of them re-checked
  against the newer finding. **Sharpened fix, two parts:** (1) a table
  index/base computed via `lui`/`addu`/`ori` arithmetic deserves the same
  "recompute it from the raw operands, don't trust the cited hex constant"
  treatment a jump target already gets — a one-hex-digit slip in a base
  address silently redirects every entry to the wrong memory region,
  which can look structurally plausible (still land on *some* code) rather
  than obviously wrong; (2) whenever you insert or read a `> Correction`
  block, always read the paragraph immediately following it too — that
  position is exactly where a section's original, now-refuted conclusion
  tends to still live, unstruck, and grepping every offset cited inside
  existing Correction blocks against a sibling doc's own per-field/per-
  offset table is a cheap, systematic way to find more of these in one
  pass rather than stumbling onto them one at a time.

**A fourteenth confirmed instance moves the trap from doc prose into
committed source, and shrinks the cross-reference distance to zero —
the contradiction was two paragraphs away in the same file.** Valkyrie
Profile (PSX, `valkyrie`), round 164: a spec doc's "Implemented" note
(dated 2026-09-04) stated "nothing in the engine writes `+0x650`/`+0x656`
— neither byte has a traced writer." Both halves were already false: the
*same doc file*'s own separate "party's formation" section had already
disassembled `+0x656`'s real writer (a per-encounter table's own field),
and a sibling doc (written 2026-09-17, 13 days later) traced `+0x650`'s
writer without either fact ever being backported into the stale note. The
same false claim had ALSO been copy-pasted verbatim into a TypeScript
`interface` field's doc comment (`src/engine/types.ts`) — and the tell was
that the very next field's doc comment, two paragraphs below in the *same
source file*, already correctly described the sibling mechanism for a
related byte. Nobody needed to grep across files to catch this one; reading
one field further in the same struct would have. **Generalized fix, two
parts:** (1) the "no traced writer" / "still open" claim this lesson
already covers can live in a source-code doc comment, not just a
`docs/*.md` file — code comments go stale exactly like prose does, and are
just as worth grepping/re-reading before trusting; (2) when auditing a
struct/interface's field-level doc comments, read the *sibling* fields'
comments in the same block, not just the one under review — a same-file,
few-lines-away contradiction is the cheapest possible instance of this
whole lesson and is caught by simply reading the whole comment block, no
search needed at all. A related, smaller finding from the same round: the
doc's own field table had documented 4 fields for a per-encounter formation
record, but the shipped TypeScript array only carried 2 of them
(`slotOffset`/`homeDepth`, dropping the very fields the stale note was
about) — when a doc names N fields for a table and the shipped data
structure has fewer, the doc is usually the correct, more complete source
and the shipped structure is what's behind, not the reverse.

**A sixteenth confirmed instance: a Correction's own "never updated in
place" claim can be stale from the moment it was written, when the fix it
points at landed in the SAME commit.** Valkyrie Profile (PSX, `valkyrie`),
round 166: a systematic sweep grepped every hex offset/address cited
inside all 408 `> **Correction` blocks across a 6-file doc set against a
sibling doc's own field table and `TODO.md`, hunting for the class of bug
rounds 162-165 had already found several instances of (a correction that
landed but was never backported). One `> Correction` block asserted "\[the
sibling section's\] own text was never updated in place. Read \[it\] as
superseded by \[this section\]" — but the sibling section, read directly,
already carried the exact fix inline. `git log -S` on the literal phrase
"never updated in place" showed why: the SAME commit that added this
"still not fixed elsewhere" claim had *also* added the in-place fix at the
sibling section, in the same diff. The claim was true at zero points in
the doc's committed history — it described a gap the author closed within
the same edit, then forgot to walk back and soften the sentence describing
the gap. **Generalized fix:** a Correction block's claim about a *different*
section being stale/unreconciled is itself a factual claim about doc
history, not just about the code/data — verify it the same way you'd
verify any other claim, by reading the cited section directly (not just
trusting the Correction's characterization of it), and when in doubt
`git log -S <exact phrase>` to check whether the "still needs fixing"
claim and its own fix were introduced together. This generalizes past
this one file: any doc-authoring pass that fixes A and, in the same
breath, notes "B still needs the same fix" is at risk of the B-fix landing
in a subsequent edit to the SAME commit/session without the note being
revisited — self-referential correction chains need the same skepticism as
the original claims they're correcting.

**A seventeenth confirmed instance introduces a proactive TECHNIQUE, not
just another reactive catch — and surfaces its own false-positive trap.**
Valkyrie Profile (PSX, `valkyrie`), round 167: with the reactive version of
this lesson (grep a *specific* flagged item's cited offset) largely
exhausted after three straight rounds re-running it against
`data-structure.md`'s field table, the technique was generalized to run
with no specific item in hand at all: extract every `identifier+0xHEX` /
`identifier[0xHEX]` token (regex over the whole plain-text doc, no
disassembly needed) from **two large sibling prose docs describing
overlapping content** (`battle-logic.md`, a narrative investigation log,
vs. `battle-engine-spec.md`, a byte-level reference spec — both documenting
the same battle-actor struct), keep only tokens both docs cite, and read
the surrounding prose for each shared token side by side. This found 4 real
stale claims in one pass, none of which either doc's own text looked
self-contradictory about in isolation: three were same-file (an earlier
section's "writer not traced" / "not named anywhere" / "not pinned down"
claim silently superseded by a same-day-or-next-day *later* section in the
very same file, discovered only because the cross-file token match pointed
at the stale line in the first place) and one was genuinely cross-file and
higher-stakes — `battle-engine-spec.md`'s own §4.1 prose still described a
field as "limited-use charges... decrements it... if the charge is
exhausted," a reading two sibling citations (`battle-logic.md` and
`data-structure.md`, plus that *same file's* own field table 400 lines
earlier) had already refuted by name — and the **shipped engine code**
(`src/engine/ai.ts`) already implemented the corrected reading, meaning the
spec prose had drifted behind the very code it was supposed to specify.
Each fix needed a `> Correction` block, not a silent edit — the point of
the sweep is finding drift, not resolving it invisibly.

The same pass hit a **false-positive trap worth naming explicitly**: the
identical token-sweep applied to a second doc pair (`scene-script-vm.md`
vs. `dungeon-field-mechanics.md`) found a superficially stale-looking
summary row missing two bits a sibling section had since traced. Before
"fixing" it, checking the sibling file's own most recent section (dated
the same day, in a dense run of "Round N: ... CLOSED" headers) showed that
section had *already* run the exact same kind of self-audit that same day
and declared the item's whole open-question list empty. **Fix, on top of
the base lesson:** (1) the token-extraction sweep generalizes past a single
flagged item — run it proactively on any two docs that describe the same
underlying struct/table/mechanism, even with no open item to start from;
(2) before editing a match, check whether the file is under dense, same-day
"Round N" (or equivalent) activity — a hit inside an actively-being-audited
section is more likely something that audit already covered than something
it missed, so verify against that section's own latest text before treating
the match as a fresh finding.

**An eighteenth confirmed instance completed the sweep started in the
seventeenth (the remaining 6 of 9 total doc-pair combinations across a
7-doc set) and found a second, distinct false-positive shape worth naming
alongside the "already-audited section" one above: a doc can already
self-flag its own apparent inconsistency, and a diff that reads only the
matching line rather than the surrounding paragraph will miss the flag.**
Valkyrie Profile (PSX, `valkyrie`), round 171: a token match surfaced two
docs stating the same equipment-stat formula differently — one wrote
`itemTable32[weaponId − 1]`, the other `itemTable32[weaponId]` — which
looked like exactly the kind of formula drift the seventeenth instance's
sweep is built to catch. Before writing a Correction, reading a wider
window around the second doc's occurrence (not just the matching line)
found an explicit disclaimer a few lines later: "(All four `itemTable32[...]`
reads in this section use the same confirmed `recordIndex = itemId − 1`
indexing as ATK/DEF... even though the pseudocode here doesn't spell it
out.)" The doc already knew about and pre-explained its own abbreviation;
there was no bug. (The sweep's real hit that round was a fifteenth-instance
repeat — a `data-structure.md` field-table row never backported from an
already-landed `battle-logic.md`/`battle-engine-spec.md` correction — not
a new pattern, just the same backport-miss caught on a different offset.)
**Fix, layered on the seventeenth instance's false-positive trap:** before
treating a token-sweep hit as a real formula/field discrepancy, read a
paragraph-wide window around BOTH occurrences, not just the matching
line — a doc author who abbreviates a repeated formula for brevity often
adds a short disclaimer nearby ("even though X doesn't spell it out",
"read as if Y") that a line-level diff will walk right past.

**A nineteenth confirmed instance: a round's own claim to have fully fixed a
sweep of stale restatements is not itself evidence the sweep was complete —
and the missed copies were on the OTHER SIDE of the correction, not
downstream of it.** Valkyrie Profile (PSX, `valkyrie`), round 179: the
fifteenth instance's third bullet records that round 165 fixed "a trailing
paragraph in that same section, a second doc's inline correction note, and a
`TODO.md` row" that all still asserted a refuted "the master dispatcher is
statically unreachable" claim, and closed with "Two further stale copies of
the pre-correction claim... are now fixed in place." Round 179 re-audited the
same claim on a routine cluster sweep and found TWO MORE surviving copies —
one a section's own heading-paragraph, one a numbered sub-section's
disposition paragraph — both sitting in file positions *earlier* than the
section carrying the actual correction block, not later. Every prior
instance in this file frames the trap as "a later/downstream section knows
something an earlier one doesn't yet" — which quietly trained the fix to
sweep forward from a correction site. But a section written *before* a fix
landed can independently preview, summarize, or restate the same conclusion
(a heading, an introductory paragraph, an earlier disposition note) and go
stale exactly the same way a downstream section does; nothing about file
order determines which direction the restatements will be found in. The
identical claim was also live a third time, in a completely different file
kind: a TypeScript verify-script's own top-of-file JSDoc comment (not a
`docs/*.md` file — the fourteenth instance's point, reconfirmed) restated
the refuted framing in two separate paragraphs, one of them mischaracterizing
the very address that turned out to be the real fix (calling a genuine vtable
call site "a debug-print support table coincidence, not a functional call
site"). **Fix, layered on the fifteenth and sixteenth instances:** when
re-auditing a topic this lesson has already caught once, don't trust a prior
round's "N further stale copies, now fixed" tally at face value and don't
scope the re-check to sections downstream of the correction — grep the exact
refuted phrase/claim across the WHOLE doc (both directions in file order) AND
across source-code doc comments in the same pass, treating a previous
session's own completion claim as just another assertion to verify against
the file's current text, not as ground truth that the sweep is done.

**A twentieth confirmed instance: a `> Correction` block can fix one bug
while introducing a NEW same-offset-different-struct conflation, catchable
only by re-disassembling the exact addresses the correction itself cites.**
Valkyrie Profile (PSX, `valkyrie`), round 180: a `data-structure.md`
correction had refuted an earlier "0 writers" negative for `globalCtx+0x56c`
by re-framing it as "not a field of a global context... a per-entity
struct... an entity type ID" — but fresh disassembly of the exact two read
addresses it cited (`0x8005f488`, `0x8006c66c`) showed the base register at
both is built by `lui $r,0x8008 ; lw $r,-0x3bf4($r)` = `*(0x8007c40c)`, the
project's own already-confirmed global battle context, not a per-entity
pointer — matching an EARLIER, already-correctly-hedged hypothesis
("battle scene / encounter id... not confirmed") sitting a few thousand
lines earlier in the very same file, and later independently re-derived and
fully confirmed in a sibling doc's own disassembly. The correction's
"per-entity struct, entity type ID" framing turned out to be true of a
*third* citation it had folded into the same claim (`0x80037b10`, base
register in a context reading already-named per-actor fields a few
instructions earlier) — a real, separate byte-wide actor field that
happens to share the numeric offset `0x56c` with the word-wide global
context field, conflated into one claim because both were reachable from
the same investigation thread. **Fix:** when auditing a `> Correction`
block for staleness, don't stop at checking whether ANOTHER section
contradicts it (the sixteenth instance's check) — also re-disassemble the
correction's OWN cited addresses fresh, specifically checking each one's
base-register provenance, whenever the correction asserts a struct-identity
claim ("this is/isn't a field of struct X") over more than one citation;
a correction that lumps several addresses together as evidence for one
struct-identity verdict is exactly where a same-offset-different-struct
mixup hides, and the doc's own earlier, more cautiously-hedged text is
often the tell that the later, more confident-sounding correction overreached.

**A twenty-first confirmed instance: the canonical "record summary" text a
`.md` opcode/format table is generated from (or mirrors by hand) can itself
be a stale copy, hiding in a source-code data array rather than a doc
comment or a `.md` file.** Valkyrie Profile (PSX, `valkyrie`), round 181:
`battle-engine-spec.md` §12.16b.D completed opcode 204 (`PLACE_CONTAINER`)'s
full 6-operand map, naming a previously-unlabelled byte (`task+0x44`, the
"engagement-effect kind") that drives the "chest that fights back" ambush
mechanic central to that section's own headline finding. Three other
locations describing the identical opcode still carried the older, vaguer
wording ("two further halves fill `task+0x38`/`0x3a`/`0x3e`", no effect-kind
byte named at all): `dungeon-field-mechanics.md`'s own primary opcode-204
section, `scene-script-vm.md`'s opcode-204 table row, and —
the one novel wrinkle — `tools/shared/psx-vp-scene-script.ts`'s hardcoded
`summary: '...'` string literal for that same opcode table entry, a plain
data field (not a `/** JSDoc */` block) that exists purely to carry
human-readable documentation alongside the byte-exact opcode metadata. All
three were fixed the same way: re-derive the fuller table from the section
that actually completed it, then propagate the exact same wording to every
copy. **Fix:** when a decode/format-table entry's semantics get refined or
completed in a `.md` doc, grep for every OTHER place that same entry's
description exists — including `tools/shared/*.ts`/`tools/<game>/*.ts`
source files that keep a per-record/per-opcode array with a `summary`,
`description`, `notes`, or similarly-named string field, since a project can
easily have three or four independent English-prose copies of "what does
this record/opcode mean" (an `.md` table row, a source doc comment, AND a
source data-array string) with no single generator keeping them in sync,
and a staleness sweep that only checks `docs/**/*.md` will structurally
miss the source-code copy every time.

This round also sharpened *triage*, not just detection, for audits working
under a time/row budget: not every restatement found is equally worth
fixing first. The SAME "426 sites, untraced, deliberately left open"
overcount-and-negative claim existed in two places — `battle-logic.md`
§60.8 (immediately followed, one section later in the SAME file, by §60.9's
own correction to 471 sites) and `battle-engine-spec.md`'s own independent
copy (in a DIFFERENT file, with no correction anywhere nearby). The
same-file case is the kind of forward-pointing this campaign's own
convention already tolerates (a reader hitting §60.8 finds the fix one
section later); the cross-file case had no such safety net and was the
real, actionable miss. **Fix:** when several copies of a stale claim exist
and only some can be fixed this round, fix the cross-file copies first —
a same-file, same-or-next-section restatement is lower-risk (the doc's own
later text usually self-corrects a linear reader) than a copy sitting in a
sibling doc with no correction of its own.

**A twenty-second confirmed instance: the stale source-code copy can be a
machine-readable status ENUM, not just prose — and it can go stale even
when every `.md` copy is already fully synced.** Valkyrie Profile (PSX,
`valkyrie`), round 183: `tools/shared/psx-vp-scene-script.ts`'s opcode table
carries both a `summary` string (the twenty-first instance's subject) AND a
separate `confidence: 'hypothesis' | 'confirmed' | 'unknown'` field per
entry. Two opcodes (135 `MSG_STATE`, 231 `POSITIONAL_SFX_231`) had already
been fully disassembly-confirmed and correctly promoted to `confirmed` in
`scene-script-vm.md`'s own opcode table — that closure session updated the
`.md` row's confidence letter, the `.md` prose, AND (implicitly, per the
twenty-first instance's own fix) should have updated the `.ts` copy too, but
didn't: the `.ts` entry was left at `confidence: 'hypothesis'` with the
pre-closure summary. Unlike the twenty-first instance (where the `.md` doc
itself still needed fixing in 3 places, and the `.ts` string was a 4th,
"novel" straggler), here **every `.md` copy was already correct** — the
mismatch existed ONLY between the doc and the code, which means "grep every
`.md` file for the stale phrase" (the normal sweep technique) finds nothing
odd, because nothing in any doc is wrong. **Fix:** whenever a project's own
per-item classification data lives in a committed source file (a `.ts`/
`.json`/`.py` array with a `confidence`/`status`/`kind`-style enum field
alongside its prose field), treat that field as an independent second
copy of "is this item closed" — don't infer it's in sync just because
every doc-side copy already agrees with each other. A cheap, generalizable
check: grep the source file for its lowest-confidence/least-certain enum
value (`'hypothesis'`, `'unknown'`, `TODO`, `0` for an "unresolved" sentinel,
etc.) and cross-check each hit's own address/id against whatever doc
sections later touched that same address — not just against the doc's OWN
table row for that same id, since (as here) the doc's own row can already
be correct while the code enum lags behind it specifically. Also: running a
scheduled/periodic "second-pass audit" over a mature doc tree with no
specific flagged item yet — see the twenty-fourth instance below for a
cheap, mechanical sweep that surfaces exactly this class of staleness
without needing to already suspect a specific address or field.

**A twenty-third confirmed instance sharpens the detection mechanism itself:
the project's own passing test suite can catch a duplicate finding that a
doc grep either wouldn't have been run for, or might have missed.** Valkyrie
Profile (PSX, `valkyrie`), round 191: a fresh disassembly traced a
`StatusResistance` field's writer (`fcn.8005b7f4`, the `+0x6a3` "Check charm"
recompute) and wrote it up across five files (`battle-logic.md`,
`src/engine/types.ts`, `constants.ts`, `damage.ts`, a new test describe-block)
as a brand-new discovery. Only running the project's ordinary regression-
check triad (`npx tsc`/`eslint`/**`npx vitest run`** — not a targeted search
for this specific mechanism) surfaced pre-existing PASSING tests in
`support-buff-consumers.test.ts` explicitly exercising this exact writer by
name, which led straight to `battle-logic.md § 64.9.3` (`RESIST_CHECK_WRITER`)
already documenting it byte-for-byte identically — the very citation a doc
grep *would* have found, but only if grepped for the right string; the round
had in fact grepped `TODO.md` for related terms and come up empty, since the
duplication lived in prose section content, not a tracked row. **Fix, adding
a new checkpoint to the existing ones:** run the project's full test suite
**before** finalizing any "this is new" writeup for a fresh disassembly
finding, not only as a post-hoc regression check — an existing passing test's
describe-block name and assertions naming the same field/function/mechanism
is a direct, load-bearing tell that prior work already covers it, and it
requires no guess at which string to grep for (it fires automatically as
part of the ordinary verification pass this campaign already runs every
round). This doesn't replace the doc-grep discipline the rest of this file
teaches — it's a second, independent detector that catches what a grep with
the wrong query would miss, and it's already "free" since the verification
triad runs every round regardless.

**A twenty-fourth confirmed instance gives a cheap, proactive sweep
technique for a project whose `TODO.md` follows the "delete a row once it's
resolved" convention** (this account's own house style, see `game-re.md`'s
Documentation conventions): Valkyrie Profile (PSX, `valkyrie`), round 195.
With every currently-open TODO row already re-examined and none yielding a
fresh angle, the round instead audited the *doc tree's own internal
consistency*: extract every `<project>-<slug>`-shaped id mentioned anywhere
under `docs/<game>/**/*.md`, diff against the id set of TODO.md's current
rows, and for every id that's mentioned but no longer a row, `grep` the
*same file* forward (later line numbers / later section numbers) for a
closure before assuming it's a bug. Running this over `valkyrie`'s ~150
"mentioned but not a current row" ids found that the overwhelming majority
are exactly what the convention predicts — a resolved row's id lives on in
old prose, and a later section in the same doc already closed the thread
cleanly (spot-checked 7 of them by hand, all clean). But it also surfaced
two real, previously-unflagged instances of this file's core pattern that
none of the prior 23 had caught, because nobody had gone looking for THIS
specific id: four separate "**still genuinely open** ... see
`vp1psx-3d-spell-effect-representation` in `TODO.md`" citations
(`data-structure.md` §§9.6.6/9.6.7 ×2/9.6.9, all written 2026-08-09) that
each predate the row's real closure at §9.6.21 (2026-09-04, in the SAME
file, ~4,200 lines later) with no forward pointer ever added; and one
"See `vp1psx-code1-auto-item-effect` in `TODO.md`" citation
(`battle-engine-spec.md`) that predates its own closure by only 37 lines in
the identical document — the narrowest-possible miss, and a reminder that
"the fix is a few paragraphs down" is not a reason to skip adding the
pointer, since a reader stopping at the stale sentence has no way to know
that. **Fix, as a distinct technique from the reactive single-item grep the
rest of this file teaches:** when a mature project's open-row list has run
dry of fresh angles, spend a cheap pass doing the id-extraction-and-diff
sweep above rather than re-trying exhausted rows — it costs one `grep -oE`
pipeline and a handful of spot-checks, needs no prior suspicion of which
address or field is stale, and reliably turns up a small number of exactly
this pattern's genuine misses even in a doc tree that's already been
through 20+ rounds of similar audits.

**A twenty-fifth confirmed instance finishes the twenty-fourth's sweep at
full scale and finds two real bugs in the sweep TECHNIQUE itself.**
Valkyrie Profile (PSX, `valkyrie`), round 196. The brief was to go back and
review ALL ~150 candidates the twenty-fourth instance's spot-check of 7 had
left unexamined, not just take another small sample. Two things fell out:

1. **The naive per-line extraction was itself undercounting.** A
   hyphenated slug-style id (`vp1psx-battle-anim-unknown-fields`) that
   happens to word-wrap across a markdown line break — common in this
   account's own long, hard-wrapped prose style — gets truncated by a
   plain per-line `grep -oE 'prefix-[a-z0-9-]+'`, because the regex stops
   at the line's own end. Worse, a *blockquote* continuation
   (`> ` prefix) or a numbered-list continuation's leading indentation
   breaks a naive "just strip newlines and re-join" fix too, since the
   quote marker or whitespace sits between the trailing hyphen and the
   word that completes it. **Fix:** strip every line's leading blockquote
   markers (`^\s*(>\s*)*\s*`) before joining consecutive lines with an
   EMPTY separator (not a space) for the regex pass — the hyphen already
   present at the wrap point is what makes the join correct, and stripping
   only the leading markers (not all whitespace) avoids accidentally
   merging two unrelated words that just happen to sit across a
   line/paragraph boundary. Symptom that something is still wrong even
   after this fix: any surviving trailing-hyphen entry in the extracted id
   list (`grep -- '-$'`) is either a genuine remaining line-wrap case or a
   deliberate wildcard reference in the prose itself (this project uses
   `` `vp1psx-battle-*` `` to mean "every row with this prefix," which a
   slug-id regex will also capture and which is not a real id at all —
   both need manual disambiguation, not blanket exclusion).
2. **The full-scale sweep (147/147 candidates individually reviewed, not
   spot-checked) found 3 more real, previously-unflagged instances of this
   file's core pattern beyond the twenty-fourth instance's 2** — including
   one where the ANSWER itself was stale, not just the pointer to it: a
   "sfx clip groups... per-bank role split is unconfirmed" note (written
   2026-08-17) sat unreconciled against a full closure of that exact split
   four sections later in the SAME document (2026-09-24, "25/25 bands
   confirmed") — the closure never linked back, so the note kept asserting
   a negative the doc's own later text had already overturned. Another
   was in a **committed reference-implementation table** ("Extractors and
   assets"), not investigation prose: a shared decoder's row said "Not
   wired into Stage 1/2 yet ... still open" for a mechanism (`vp1psx-room-
   layer-placement`) that had been fully wired into the real pipeline
   (`collectRooms` calling `composeRoom`) and closed 5+ weeks and dozens of
   sub-rounds earlier — a reminder that a doc's own "what's implemented"
   reference tables are exactly as vulnerable to going stale as its
   investigation narrative, and belong in the same sweep.
3. **The same convention violation this account's own `game-re.md` already
   names in prose** ("`plan.md`'s 'Open Questions' section ... must not
   carry item status") **can go undetected for a very long time simply
   because nobody re-reads an old, dormant section of a long-running
   `plan.md`.** This project's `plan.md` had a "Next steps (not started)"
   checklist, numbered 1-13, written before most of the project's later
   work began; 11 of the 13 items' own cited ids had since closed (most
   findable by the very same id-diff sweep this file already teaches),
   one more was done under a different id, and the last was substantially
   superseded — i.e. the entire section was stale, not just a couple of
   its lines. **Fix, generalizing past `TODO.md`-row prose:** when a
   project has a `plan.md` (or equivalent) with any numbered/bulleted
   "next steps"/"remaining work" checklist section, run the same id-diff
   sweep against it specifically, even if (especially if) it looks
   old/dormant and nobody has touched it in dozens of rounds — that
   dormancy is exactly why nobody already caught the violation, not a
   reason to skip it. Per the project's own migration instruction, replace
   a wholesale-stale section with a pointer to `TODO.md` rather than
   patching individual lines.

**A twenty-sixth confirmed instance moves the trap one hop earlier: the
citation was never true in the first place, not just stale.** Every prior
instance in this file is about a doc claim that WAS once accurate going
stale as the project moved on. This one is a citation that never matched
its target at all. A pipeline helper (`readDisc1TocSlot()` in
`build-assets.ts`, Valkyrie Profile PSX) carried a doc comment: "every
resource the battle-data collectors below touch is byte-identical on
Disc 2 ... battle-logic § 23.1 for the code overlays." Reading § 23.1 end
to end found it is entirely about a *different* claim — TOC slot 1989's
correct load base (`0x80099800`, refuting an earlier `0x800A0000`
misread) — and never states or checks Disc-2 byte-identity for that slot
anywhere in its text. The two topics are genuinely adjacent (both are
about the same TOC slot, in the same investigation arc, written by the
same session) which is exactly why the miscitation was never caught: a
reader skimming for "is slot 1989 covered somewhere near here" would see
§ 23.1's heading and address and reasonably assume yes, without checking
which specific fact it established. **Fix:** re-derived the real claim
fresh instead of trusting the pointer — decoded TOC slot 1989 (and the
sibling slot 1490 the same helper also serves) from both discs
independently and diffed the two byte-for-byte, confirming the citation's
*conclusion* was actually correct even though its *reasoning* pointed at
the wrong section. A citation landing on the right neighbourhood but the
wrong specific fact is not self-evidently wrong just because it's
mis-targeted — but it earns zero trust until re-checked, since nothing
about a plausible-sounding section number distinguishes "this really was
verified two sections over" from "someone conflated two adjacent findings
while writing the comment."

**A twenty-seventh confirmed instance moves the trigger from "about to
disassemble" to "about to declare the question unanswerable without live
capture" — and it is the same project's sharpest version of the failure
yet, because the mistaken conclusion had already been written down as the
final word on the item.** Valkyrie Profile (PSX, `valkyrie`), round
212→213: round 212 fully disassembled a field-sprite general-path
renderer's caller-side "which render mode fires" formula down to the
exact byte, naming three caller-supplied fields (`actor+0xee`,
`actor+0xb8`, and a resolved struct's `+0x28`) as the gates, then closed
the item with "whether real gameplay ever drives these away from their
inert defaults is a runtime-value question this project's standing rule 1
(no live capture without sign-off) cannot answer statically" — and left it
open in `TODO.md` on that basis. It could: `scene-script-vm.md` §12.2, in
the SAME project's docs, had already enumerated `ACTCMD_SETPROP` sub-
property 22 as `half[obj+0xee] = value` (43 real corpus occurrences) and
sub-property 36 as `word[obj+0xb8] = value` (60 occurrences) — literal
script bytecode operands, i.e. static disc data, not runtime state. A
fresh corpus census (no emulation, no live capture) found 39/43 and 55/60
of those real operands away from the inert default, settling the question
outright. The third field was a second, compounding miss of this exact
lesson: round 212 labelled the `+0x28` struct a "per-character tile-bank
entry" and cited `fcn.80039ae8`/"§9.6.19's own tile-bank installer
family" — but `fcn.80039ae8` was already named and disassembled 8 days
earlier in the SAME document's own §9.6.13 as the **room-layer/camera
resolver** (a different mechanism, no "tile-bank installer" exists at
that address), and the exact call-site address round 212's own trace
passed through (`0x80036898`) was already a row in that section's own
call-site table — never cross-linked. **Fix, generalized:** "this needs
live capture" (or "this needs `re-oracle`") is exactly as much a
conclusion as any other doc claim, and earns the same mandatory grep this
whole file has argued for since instance one — before writing it, grep
the doc for the specific field offsets/addresses the open question names,
including any already-enumerated property/opcode table that might
independently supply, set, or read those exact bytes from static content.
A "static analysis cannot answer this" verdict that skips that grep is
not more trustworthy than a "still open" row that skips it, and the
routine escalation ladder (try `re-oracle` before accepting "needs live
capture") does not substitute for it — `re-oracle` would have hit the same
grep eventually, at far higher cost than doing it first.

**A twenty-eighth confirmed instance sharpens the twenty-second's theme
(a stale non-`.md` copy surviving a doc correction) to the loudest,
highest-stakes case: a committed VERIFY SCRIPT's own hard-coded PASS/FAIL
assertions, not a silent confidence label.** Valkyrie Profile (PSX,
`valkyrie`), round 216→217: round 216's rigor spot-audit of a camera-
instance-field census found two mislabeled sites and a genuinely new
out-of-function read, and wrote an accurate `> Correction` block
superseding the earlier round's "every one of them falls inside this one
function" / "sits near one of the doc's 6 cited landmarks" completeness
claims. Round 216's OWN committed script,
`verify-camera-instance-field-census-round216.ts` — written the same
round, to PRODUCE that very correction — still contained two `check(...)`
calls asserting the pre-correction blanket claim verbatim
(`readSites.every(nearAnyLandmark)`, `readSites.every(inFcnCd04)`). Since
the correction's own new exception (`0x8009c19c`) is real, both checks
now fail on every re-run, forever, despite the doc text already being
correct — a violation of this campaign's own hard rule that every
committed script must exit 0. Unlike the twenty-second instance (silent
staleness, no doc disagreement, no crash), this is LOUD — a red script —
but that loudness is easy to misdiagnose as "a known, accepted red script"
rather than "the doc moved out from under this specific assertion,"
especially in a project with hundreds of committed verify scripts and no
single dashboard distinguishing the two. **Fix:** writing a `>
Correction` block that supersedes an earlier "exhaustive"/"every one of
them"/"all N" claim is not finished until you've also re-run that finding's
own committed script — if it was produced by one — and confirmed it still
exits 0. If it now fails, rewrite the failing assertion to state the
EXACT corrected invariant (here: "5 of 6 near/inside, with exactly one
confirmed exception at address X") rather than weakening it into a
tautology or deleting it — the fix must still be capable of failing again
if a future round finds yet another exception. Treat this as one
required step of finishing the correction itself, in the same commit,
not a separate follow-up.

**A twenty-ninth confirmed instance moves the trap from a single stale FACT
to a running numeric TALLY maintained across two SIBLING doc files
describing the same underlying mechanism.** Valkyrie Profile (PSX,
`valkyrie`), round 224: `scene-script-vm.md` keeps an incrementally-updated
running count of a specific struct bit's WRITER sites (as opposed to its
already-exhaustive reader census) — "the two inside `FUN_8002fee4`;
opcode 119's clearer; and now this setter" = "a fourth writer," as of that
document's round 38. A from-scratch rigor-audit of an unrelated table in
`dungeon-field-mechanics.md` (a collision-primitive type dispatcher's
per-type handler bodies) found that ONE of that table's own already-
published rows — sitting in this project's docs since that section's
earliest pass, describing a completely different mechanic (a ladder-engage
handler) — was itself a fifth writer of the exact same bit, structurally
identical to a brand-new sixth one the fresh disassembly surfaced in a
sibling handler (a ledge-engage commit) a few dozen bytes away in the same
function. Neither of the tally's maintainers had ever cross-referenced the
OTHER document's own type-dispatcher table against the bit they were
counting writers for, despite both documents describing call sites inside
the identical function (`FUN_80031194`) and despite the ladder-engage row's
own text explicitly stating the clear-then-set idiom in prose the whole
time. The base lesson's usual shape is "the answer already exists, just
never linked to the question" — this is a narrower variant specific to
running COUNTS: a tally that only ever increments when its own maintaining
document's *own* investigation finds a new instance can go stale not
because the count-taker missed a search angle, but because the mechanism
it's counting has OTHER real instances living entirely inside a *different*
document's table, describing a different feature, that nobody ever thought
to check against this specific tally. **Fix, specific to running-count
claims:** when a doc states "N writers/setters/producers of X, as of round
M" (or any other incrementally-maintained enumerated-site count), don't
just grep the SAME doc for the field/bit/offset under count — also grep
EVERY sibling doc describing the same underlying code region (same base
overlay, same load address range, same named function) for any table row
that independently documents a SET/CLEAR/write to that same field, even
under a totally different section heading describing a different game
mechanic entirely. A tally is exactly as vulnerable to this file's core
failure as a single stale fact is, just distributed across more citations
than a single-fact grep would think to check.

**A thirtieth confirmed instance flips the polarity: instead of a sibling
doc's table holding a missed POSITIVE instance (an uncounted writer), it
holds an already-published NEGATIVE enumeration that flatly contradicts a
different section's unqualified positive claim.** Valkyrie Profile (PSX,
`valkyrie`), round 225: `scene-script-vm.md` § 1's headline table has long
published a corpus-wide census — "opcodes that never occur in the corpus:
52 (43 null + 9 live: 47, 55, 59, 155, 164, 167, 213, 223, 232)" — meaning
those 9 numbered opcodes, though implemented, are provably invoked zero
times by any real script on either disc. Three separate sections of
`data-structure.md` (§§ 20.10, 20.28, 20.29, all part of an already-
`resolved` TODO row) stated as flat, unhedged fact that a persistent
counter (the "Seal Rating") "is also written from the field... by a
dedicated scene-script opcode" — that opcode being, by address, exactly
opcode 232 from the 9-item dead list. Nobody had ever checked the two
claims against each other: the Seal-Rating sections never named the opcode
NUMBER (only its handler address, in a different numeric base than the
census table used), and the census table's own "never occurs" list carries
no forward pointer to every place elsewhere in the doc tree that might
later assume liveness for one of its members. Re-derived fresh (both a
byte-exact disassembly proving the two docs' two different cited addresses
name the SAME handler, and an independently-reimplemented full-corpus
occurrence tally, not a re-run of the census's own script) confirmed the
census was right and the Seal-Rating claim was the one to correct — the
opcode is real, well-formed, and dead. **Fix, specific to a "these N never
occur/are never reached" NEGATIVE census:** treat it as a standing,
free falsifier for every OTHER claim anywhere in the doc tree asserting
that one of its specific enumerated members is exercised, live, or
"written from" some runtime path — and check by the census's own KEY (an
opcode number, a state id, an enum value), not by prose vocabulary, since
the two claims will almost never share wording ("never occurs in the
corpus" vs. "written from the field") despite being about the identical
mechanism. This is the mirror image of the running-tally trap above: there
a sibling doc was missing a positive fact the tally should have counted;
here a sibling doc already published the decisive negative fact and nobody
thought to check a later positive claim against it.
