# An unreferenced ASCII table matching a live table's numbers is not evidence of the live table's semantic role

**When it bites:** a plain-ASCII, digit/number-shaped string is found near
real code (via a `strings`-style scan) and its shape/position suggests a
semantic role (a score table, a stat table, a level table) — before
writing that role into a doc, or before treating the string as proof of
what a nearby *code-referenced* binary table is for.

Confirmed on Black Tiger (arcade, `kolbold` project): a maximal-printable-
run scan over the unencrypted Z80 program ROM found two long space-
separated ASCII decimal-digit runs (`"100 1000 2400 9600 30 100 1200
2400 9600 30 ..."` and `" 80 300 800 1600 150 80 300 800 2400 150
..."`). Their shape (ascending numeric groups) and ROM-bank position led
a session to label them "almost certainly a bonus/extra-life score-
threshold table" and stop there. A later session ran an exhaustive
literal-address scan (every `LD reg,imm16` / `CALL` / `JP` opcode form,
across the whole 320 KB ROM) for either string's own address and found
**zero** references — a strong, cheap, exhaustive signal the string
itself is inert, never read by the CPU as data. Disassembling nearby code
that WAS confirmed to reference other real content in the same ROM bank
led to a completely different, code-traced binary table (16 records × 5
LE words, gated by a hardware Difficulty DIP switch, tested against the
player's currency stat, and wired to two already-decoded dialogue lines
— "Sorry, you don't have enough zenny for that item." / "You can't carry
it any more.") that is a real **shop price table**, not a score table.
The binary table's 4 escalating-price columns matched the ASCII strings'
4 non-constant columns byte-for-byte across all 16 records (a genuine
independent-copy cross-check) — but the ASCII strings' own trailing
constant (30 for one half, 150 for the other) never appears anywhere in
the binary table, which instead uses a uniform *leading* constant (50)
the ASCII strings never mention at all. The ASCII text turned out to be a
programmer's own human-readable tuning/documentation comment, compiled
into the ROM as dead data sitting next to the table it describes — real
in its numeric content, useless as a semantic-role oracle, and actively
misleading about the record layout (leading vs. trailing constant,
different value entirely).

**The fix:** two separable morals.

1. **A string's suggestive shape or position is not evidence of a live
   table's role.** Treat a numeric-shaped ASCII string the same as any
   other found-but-unverified content: identify what actually CONSUMES
   the matching binary data (the real disassembled/traced code path), and
   let that consumer's own logic (what it compares against, what RAM
   variable it reads, what UI text it triggers) name the semantic role —
   not the string's narrative plausibility.
2. **"Zero code references to this string's own address" is itself a
   strong, cheap, exhaustive-scannable result**, and it should raise
   suspicion the string is inert documentation/dead data rather than
   live-read content — even when (especially when) its numbers later
   turn out to be real and to matter. Run the literal-address scan before
   writing up a numeric string as a probable data table; a positive hit
   count is real evidence either way, and an exhaustive zero is not
   silence, it's a finding.

This generalizes past this one game: any commercial ROM/executable can
carry inert human-authored comments or tuning notes that happen to
compile in as string literals, especially adjacent to the exact system
they describe (a common authoring habit). Two independently-stored
copies of the same facts (Method §4's oracle) is real, strong evidence —
but only for the *numbers*, not automatically for which copy is the live
one or what either copy's role is.
