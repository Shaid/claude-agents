# A doc's own already-solved section can silently answer a different section's "still open" row

**When it bites:** about to start fresh disassembly tracing on an item a
project's spec doc lists as open/unresolved (a "still open" table row, a
`TODO.md` residual) — especially when the item names a specific address,
table, global variable, or field that sounds like it could be shared
infrastructure (a per-level lookup table, a shared A5/frame-relative
pointer, a shared dispatch helper) rather than something unique to the
open item's own feature area. Also: about to trust (or about to write) a
dated status-update/"done" block's characterization of a specific asset —
see the addendum below.

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
