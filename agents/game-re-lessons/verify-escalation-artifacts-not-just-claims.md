# A specialist escalation's returned script can be stale even when its prose and renders are correct

**When it bites:** a `re-codebreaker`/`re-oracle` escalation returns a
"solved" verdict with convincing rendered evidence (legible text,
recognisable art) and a reference script/probe you're about to copy
into a committed extractor.

Wizardry 6 Amiga's `.PIC` escalation was genuinely correct — disassembly
of the cel drawer, byte-exact length-formula verification across 731
cels, and legible rendered credits text and monster portraits all held up
under independent re-derivation from the escalation's own prose (not its
code). But the escalation's own saved throwaway probe script had a
**stale palette array**: literally the standard EGA hardware colour order,
not the permuted order its own doc writeup and disassembly claimed. This
was only caught by sampling actual background pixel colours in the
escalation's *own rendered PNG output* and finding they matched the
*documented* palette table, not the *array literal sitting in the script
file* — proof the script on disk wasn't the version that actually
produced those renders (almost certainly edited further during
exploration after the images were generated).

The fix pattern: re-derive the decoder from the specialist's **prose
claims** (the struct layout, the formula, the disassembly citations) in a
fresh implementation, rather than copying its returned script verbatim —
then cross-check your fresh implementation's output against the
specialist's own rendered evidence (pixel-for-pixel where possible, e.g.
sampling a known background/foreground colour). A convincing final render
does not guarantee every intermediate artifact handed back with it is
still consistent with itself — treat the *claims* as the source of truth
to re-verify against, not the *code*.

Second confirmed instance, and it's cheap enough to do every time, not
just when something feels off: Black Crypt Amiga's `bcdfa` `BCSPEED.EFF`
escalation (a 20,195-byte particle-script bank, 95 sections) was
independently re-verified in well under 10 minutes — a fresh r2
disassembly of the two cited routines (matched the escalation's
transcription instruction-for-instruction), a from-scratch ~40-line blind
parser (written without reading the escalation's own probe script) that
reproduced its in-executable 95-entry offset table byte-exact and closed
the byte count with zero remainder, and a cross-platform oracle re-check
using the project's **own** existing parser (`extract_clipper.parse_clp`)
rather than the escalation's byte-compare. Nothing was wrong this time —
but the check was cheap precisely because it targeted the escalation's
*prose claims* (disassembly addresses, table sizes, the record schema)
with fresh code, not because the claims happened to be simple. Treat this
verification pass as a fixed, small cost of promoting *any* escalation
result to a committed extractor, not an optional step reserved for
suspicious-looking results.

Third instance, two more concrete techniques for when the escalation's
finding is a **program** (an interpreter/executor), not just a decoded
table: WIME's `SynthSceneObjects` escalation (a symbolic 68k executor
enumerating 276 branch paths of a 31-case switch — see
`~/.claude/skills/re-codebreaker/SKILL.md`'s "selective branch-forking"
technique) returned a scratchpad `.asm` listing it claimed to have parsed
its instruction stream from. (1) **Diff the escalation's own working file
against the real project disassembly for the same byte range** — a plain
`diff` after re-extracting the same range from the project's canonical
disassembly file confirmed the escalation's copy was byte-for-byte
identical, i.e. not silently hand-edited or hallucinated partway through
exploration (the failure mode the first instance above actually hit).
This is a two-line check and should be routine whenever an escalation
hands back a disassembly excerpt it worked from. (2) **Re-run the
escalation's own verification tool independently, with your own test,
not its reported summary number.** Re-executing the escalation's
symbolic executor from a fresh driver script (not reusing its harness
code) across 15,872 fully-concrete input combinations — rather than
trusting its "0 mismatches across 276 paths" claim — is what actually
constitutes verification here; reading the number in the report is not.
Both checks combined took under 20 minutes and also caught two of the
*reviewing* agent's own arithmetic mistakes when hand-deriving test
fixtures from the escalation's prose (see
`hand-computed-test-fixture-vs-real-run.md`) — a reminder that the
review pass itself needs the same "run it, don't compute it by hand"
discipline as the escalation being reviewed.

Fourth instance, and a clean example of the "re-derive from prose, not
code" fix paying off with zero findings to show for it (still worth
doing — the point is earned confidence, not always catching a bug):
Wizardry 6 SNES's opening-sequence escalation described an LZSS
decompressor (2 KB window, an 11-bit offset / length-3-34 match token)
purely in prose/pseudocode. The calling session re-implemented it from
scratch — never opened the escalation's own scratch script — and ran the
fresh implementation directly against the ROM. It reproduced two fully
legible renders (a publisher logo composing to an unmistakable wordmark,
a copyright screen composing to a full paragraph of correct English text)
plus a coherent non-noise tile render for an unrelated resource (a
spell-effect animation frame) found by a *second*, independent
escalation in the same session. Nothing was wrong in either escalation
this time, but the confidence is real because it came from running fresh
code against the ROM and getting a decisive render-level oracle (legible
text), not from trusting the escalations' own "0 overrun, byte-exact"
claims. The same session also independently re-verified a structural
claim from the second escalation (a 139-record master directory's
boundary, one record's frame-table parse) by re-deriving the parse from
the escalation's cited field offsets rather than importing its scratch
parser — cheap (a few dozen lines), and it's what makes "I checked this"
mean something more than "I read that someone else checked this."

Fifth instance, a genuine per-item error caught inside an otherwise-solid
finding: Wizardry 6 SNES's bulk-maze-table escalation (a 14-record
per-level table cross-checked against the Amiga port's independently-
confirmed `scenario.dbs` oracle) reported "levels 0, 3 and 6 are 768/768
exact on the feature plane" alongside a real, correct headline number
(~99% aggregate agreement). A from-scratch Python cross-checker,
written against the escalation's prose only, reproduced every other
number to the exact fraction (wall sub-fields, region origins) — strong
evidence the core finding was real — but found the "which levels are
exact" claim false: only one of the three named levels was actually
exact, and a fourth level the escalation hadn't flagged at all was the
worst-agreeing one. The aggregate percentage and the qualitative
conclusion both survived; only a specific, checkable per-item detail
was wrong. This is the sharpest argument yet for reproducing an
escalation's *specific* claims one at a time rather than spot-checking
only the headline number — a correct-sounding aggregate can still carry
a false, over-specific detail sitting right next to it, and the two
don't get caught by the same check.

Sixth instance, a variant worth its own note: the escalation's *own*
corpus-wide verification can have a real coverage gap disguised as a
clean percentage, when the check is implemented as a **manual per-
observed-kind branch list rather than generic/exhaustive code**. Valkyrie
Profile 2 (PS2)'s character-mesh escalation reported "778,245/778,461
(99.97%) unit-length normals" as if it were a corpus-wide check — but its
verifier's unit-length test only had explicit `if`/`elif` branches for 2
of the 4 real vertex-normal encodings actually present in the corpus
(`V4-16` and `V3-32`), silently skipping `V3-16` (the single *most
common* real encoding, ~84% of all normal-bearing batches) and a rare
`V1-8` outlier shape entirely — the reported percentage only ever
described the 2 branches someone thought to write, not the corpus. The
`V1-8` case turned out to be a genuine bug magnet: it's a 1-component
stream, not a real 3D normal, and reading it as 3 components produces
literal `NaN`. This was only caught because the downstream integrator
ported the escalation's reference decoder to a second language with
*generic* code (no per-kind branch list to inherit the blind spot from)
and ran it against the full real corpus — which naturally exercised every
encoding actually present, including the ones the original census's
if/elif chain never touched. The general check: when re-deriving an
escalation's verification independently (per the pattern above), don't
just re-run the same check shape on the same claimed inputs — ask whether
the check's own implementation enumerates cases exhaustively (a switch
over every value actually observed in the data) or by hand (branches for
whichever cases the person happened to write), since the latter can
report a seemingly-precise "N/M passed" number that quietly excludes
everything it didn't think to branch on.

Seventh instance, and a reminder this applies to any specialist subagent's
returned disassembly claims, not only formal `re-codebreaker`/`re-oracle`
escalations: on Phantasie I (Amiga, `nicodemus` project), two separate
`amiga-disasm` subagent traces (a `GetStat`/`SetStat` character-stat
routine, then a combat hit/miss/damage-application routine) each returned
~5-10 specific "file offset `0xNNNN` contains bytes `XX XX XX XX`,
disassembling to `INSTRUCTION`" claims. The cheapest possible check — read
the real target file directly at each claimed offset and byte-compare
against the claimed hex, in a few lines of Python, no re-disassembly
needed — caught zero errors across both traces (every claim matched
exactly), but took under a minute total and is what makes "the subagent
traced this" become "this is confirmed," the same distinction the
instances above draw for formal escalations. Do this before writing a
subagent's claimed addresses into project docs as confirmed, not only
when a claim feels suspicious — it's cheap enough to be routine, and a
byte-level disassembly claim is exactly the kind of thing that's trivial
to silently get wrong (an off-by-a-few-bytes offset, a transposed hex
digit) while still producing a plausible-reading final report.

Eighth instance, the *transposed keyed mapping*: a fork's otherwise-superb
battle-presentation trace (Spirit of Excalibur, 2026-08 — dozens of
byte-cited findings, all of which held) delivered a 9-case jump-table
"case → handler" map with **cases 6 and 8 swapped**. The integrating agent
caught it only because it had independently derived the same table earlier
and, on the conflict, hand-decoded the raw `DC.W` PC-relative displacements
from the disassembly to arbitrate — keeping its own mapping and folding the
fork's (correct) per-case content into the right slots. The general rule:
when integrating a specialist's **keyed mapping** (jump table, opcode→handler,
id→resource), re-derive the key column from the raw bytes even when every
individual entry's *content* is verifiably right — key↔value pairing errors
survive content-level verification, and a transposed pair poisons exactly two
entries while everything else checks out.

Ninth instance, and the cheapest tell to screen for: **a claim backed by a
list of confirming instances instead of a coverage fraction is hiding its
denominator.** Phantasie III (Amiga, `nicodemus` project): a stood-down
`re-codebreaker` volunteered two corroborating findings. One was a corpus
invariant stated with its denominator — "verified across 58 of 58 padded
files, zero deviations" — which re-ran at exactly 58/58 and was kept. The
other claimed a grid's cell value was "essentially a function of" its
4-neighbour occupancy mask, and evidenced it by *enumerating ~20 values that
each occurred at exactly one mask*. Re-running the same tabulation as a
census over the whole population gave **195 of 311 cells (62.7%)** — 116
cells break the rule, including every `0xF3`-`0xF8` variant, one of which
alone spans 8 different masks. The listed values were real; they were simply
the subset that worked, with the failures never counted. Note this is a
different failure from instance 6: there the denominator existed but silently
excluded cases, here there was no denominator at all. The screen is
mechanical — before documenting any "X is essentially/basically a function of
Y" or "X always corresponds to Y", check whether the evidence is a fraction
over the full population or a list of examples, and if it's a list, re-run it
as a census and write down the percentage. Anything at 62.7% is a signal
worth recording as a hypothesis, never a decode (see the verification bar in
`game-re.md`: a ~70% shape match is not decoded).
