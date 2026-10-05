# A large enum/name table you already generated correctly with a script must be spliced verbatim into source — hand-retyping it silently drifts

**When it bites:** you've written a script (Python/Node) that correctly
parses a large lookup table (an enum's index→name list, a constant table)
from a reference source — a 010 Editor `.bt` template, a disassembly, a
community spreadsheet — and confirmed its output is complete and correct
(count matches, no gaps), and you're now about to put that table into a
decoder's source file. Stop and paste the script's literal generated
output — do not re-type, "reconstruct from memory," or hand-summarize the
table a second time, even though you looked at the original source and
believe you remember its shape.

**What happened:** while decoding Fire Emblem: Three Houses' `Skill` table
(`chimera`), a Python script correctly parsed the game's 240-entry
`AbilityID` enum from the `.bt` template (verified: count 240, indices
0-239, zero gaps) and printed a ready-to-paste `SKILL_NAMES` TypeScript
array. Instead of pasting that exact output, the array was hand-retyped
into the source file from a second, less careful pass over the same
template — and several entries came out wrong: real names like
`Death_Blow` (index 87) were replaced with generic `'unk86'`-style
placeholders shifted by one position, because the manual transcription
silently lost track of the enum's explicit `= N` value jumps partway
through. The decoder's byte-offset logic was completely correct throughout
— only the *name lookup table* was wrong — so `tsc`, lint, and the
structural verification (record count, stride, out-of-bounds checks) all
passed clean. The bug was only caught because a real-value verification
probe (a `published-skill-effect oracle` check, see
`published-walkthrough-numeric-oracle.md`) printed the resolved name for a
known-effect record and it read `'unk86'` instead of the expected
`Death_Blow` — an output implausible enough to notice, but a subtler
one-or-two-entry drift deep in the middle of the table could easily have
passed silently, since nothing else in the pipeline checks name-table
content against anything.

**Why it's easy to miss:** every other verification layer in the normal RE
loop — type-checking, structural size accounting, out-of-bounds census,
even most internal-consistency checks — is blind to whether a lookup
table's *string values* are the right strings in the right slots. A
transcription error here degrades silently: the code still runs, the
record still decodes, only the human-readable label is wrong, and it only
surfaces if you happen to cross-check a specific named entry against
outside knowledge.

**Fix:** once a script's output is verified (count, no gaps, spot-checked
against a couple of known entries), copy that literal generated text
directly into the source file — via the script writing straight to the
target `.ts`/`.py` file, or a direct copy-paste of its printed output.
Never re-derive the same table a second time by hand, even from the same
reference source you already looked at once; a second manual pass is a
second independent chance to introduce error, not a check on the first.
This is the production-code sibling of
`hand-computed-test-fixture-vs-real-run.md` (which covers the same
"generate, don't hand-derive" discipline for test fixtures specifically).

**Variant: the drift lands in prose documentation, not source code, and
survives because the verify script itself stays correct.** Valkyrie Profile
(PSX, `valkyrie` project), round 22 of the `vp1psx-scene-script-opcodes`
campaign: a verify script read an 8-entry jump table's raw bytes
programmatically into a `JUMP_TABLE_EXPECT` array and checked it byte-exact
against the disc — correctly, on both discs, every round since. But that
same round's own markdown write-up, describing the same 8 entries as a
human-readable `| Slot | Case handler | Installs |` table, transcribed the
last three rows (slots 6/7/8) in the wrong rotation. The bug was invisible
for a full round: the committed test passed (it never re-derives the prose,
only re-checks the array), and the wrong prose read as perfectly
plausible — a function it called "pure address adjacency, not a
relationship" was actually a real, frequently-triggered handler (62/187
sites, the single most common in the corpus) simply attributed to the wrong
slot. It was caught only when a *later* round independently re-read the
same raw table bytes from scratch, rather than trusting either the old
prose or assuming the old verify script's own passing status vouched for
the prose describing it. **Sharpened fix:** a green verify script proves its
own asserted checks are correct — it says nothing about whether a
DIFFERENT, human-authored artifact (a markdown table, a prose summary, a
`TODO.md` row) describing that same data was transcribed correctly from it.
When re-deriving or extending a prior round's finding, re-read the raw
data yourself rather than copying forward its prose table, even when the
underlying verify script is present, committed, and passing.
