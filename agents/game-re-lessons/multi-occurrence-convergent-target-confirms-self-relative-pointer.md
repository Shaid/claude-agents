# Several instances of a suspected self-relative pointer resolving to the identical target, from different raw values, confirms the formula cheaply — even in one file

**When it bites:** a format has an opcode/field suspected to be a
self-relative offset (`target = someBase + rawValue`) with an ambiguous or
unconfirmed base (the field's own position? a fixed header slot? the
enclosing record's start?), and more than one instance of that same
opcode/field occurs within a single record/resource at different byte
positions with different raw values. Don't reach straight for a corpus-wide
vote (`self-relative-offset-ambiguity-resolved-by-corpus-vote.md`) or an
emulator/disassembly trace before checking this first — it needs only the
one file already in hand.

Confirmed on Final Fantasy VII (PSX field-BGM `DRUM_ON` opcode, `siren`
project): `DRUM_ON`'s 2-byte param was suspected to be self-relative to the
opcode's own byte position (`target = opcodeOffset - resourceOffset +
rawParam`), a genuinely different base than any fixed header field (v1's
header has no dedicated instrument/drum pointer slot, unlike the sibling
"v3" format's own confirmed fixed-offset self-relative pointers). One real
resource (`5TOWER.DAT`'s first AKAO resource) has 3 `DRUM_ON` events at 3
different opcode byte offsets with 3 different raw param values
(`3072`/`2820`/`2520` at opcode-local offsets `3394`/`3646`/`3946`) — under
the candidate formula, **all three resolve to the exact same absolute
target** (local offset 6466, 66 bytes before the resource's own confirmed
end). This is decisive on its own: if the base were wrong, three
independently-varying `(offset, rawValue)` pairs converging on one exact
byte position by chance is implausible, and if the base were right by
coincidence for only one instance, the other two would land elsewhere.

**Why this is stronger than it looks:** a single instance validating "lands
in-bounds" only rules out gross errors (wrong sign, wrong scale). Multiple
instances *converging on the identical target from different starting
points and different raw values* is a much sharper test, because the
resolution formula must be exactly self-consistent across every instance
simultaneously — there is no free parameter left to tune per instance that
would make a wrong formula coincidentally agree more than once.

**Fix:** whenever a suspected self-relative pointer has 2+ real occurrences
within one record/resource (common for anything that toggles a mode or
re-asserts a reference — "turn on drum mode," "select this table," a
repeated `PROGCHANGE`-style opcode), compute the candidate resolution for
every occurrence and check whether they agree. Agreement across 2-3
instances in a single file is already strong evidence and costs nothing
extra once the resolution formula is written; disagreement is an immediate,
cheap falsification that saves a corpus-wide sweep or an escalation. This
complements (doesn't replace) the corpus-wide vote technique in
`self-relative-offset-ambiguity-resolved-by-corpus-vote.md`, which is the
right tool when only one instance exists per resource or the candidate
bases can't be told apart within a single file.
