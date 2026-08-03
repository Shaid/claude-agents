# A ROM-address-validity filter on a long-addressing census can silently discard the one real DBR-relative hit

**When it bites:** about to filter/validate a long-addressing-instruction
(`LDA long`/`LDA long,X`/`JSL`) census by requiring the operand's 16-bit
address part to be a physically-valid ROM-window address (e.g. `>= 0x8000`
on LoROM), especially when the census is failing to find a known-to-exist
consumer for a data table.

An operand-validity filter built to cut false positives out of a raw
byte-pattern census (`LDA long`/`LDA long,X`/`JSL` opcodes, scanned without
instruction-boundary validation) is itself a *shape* — it only recognizes
one way of forming an address into a table: a literal 24-bit long operand.
It has no way to recognize the other common way: `DBR`-relative indexed
addressing, where the base is set once (`LDA #bank; PHA; PLB`) and every
subsequent access is a short `LDA table,X`/`LDY table,X` whose 16-bit
operand is the table's *raw* address, not a computed absolute pointer. If
the table's first meaningful index isn't `0` (e.g. entries start at index
`2` because index `0`/`1` are reserved, or the code pre-advances the index
before the first read), the encoded table-base operand can legitimately
sit *below* the addressable ROM window (`base - firstIndex*strideBytes <
0x8000`) — a real, working instruction, discarded by a filter built to
reject exactly that shape of "impossible" address.

Confirmed on Wizardry 6 (SNES): a census for long-addressing instructions
targeting a 139-record master directory (`LDA long`/`LDA long,X`/`JSL`)
produced 937 raw hits; filtering to `operand's 16-bit part >= 0x8000`
(this project's standard LoROM-validity check, effective at cutting noise
elsewhere) brought it down to 31 "high-confidence" hits — and the real
consumer wasn't among them. The actual read was `LDY $7ffe,X` with `DBR =
$b2` set separately a few instructions earlier via `PHB`/`PLB` — the
table's real base is `$8000`, but the index register is pre-scaled so the
encoded operand is `$7ffe`, just under the window. The filter discarded
the one true positive by both operand value *and* addressing-mode
mismatch (a `DBR`-relative short load was never going to match a
long-addressing opcode census in the first place, regardless of the
filter). Two full sessions were spent on this: one produced a plausible-
looking but ultimately illusory "4 identical `JSL` call sites, target byte
decodes as `BRK`" finding entirely from unfiltered noise reinterpreting
unrelated table data as code; a second, careful hand-verification
correctly debunked that finding but still didn't locate the real consumer
(the census methodology itself was structurally incapable of finding it).
A `re-codebreaker` escalation broke through only by abandoning the
long-addressing census entirely and censusing instead for the *bank-set*
idiom (`LDA #imm; STA dp` / `PHB`/`PLA`/`PLB`) that precedes `DBR`-relative
table reads — a completely different instruction shape.

**Fix:** an operand-validity filter narrows a census's *false-positive*
rate; it does nothing for the census's *false-negative* rate, which is
capped by what addressing modes the census's opcode selection covers in
the first place. Before trusting a "zero/few hits after filtering" result
as evidence the region has no real consumer, ask whether the census's
opcode list covers `DBR`-relative indexed addressing (short `LDA`/`LDY`/
`LDX table,X` preceded by an explicit bank-set) as well as long/absolute
forms — and if the table is suspected to be read this way, census for the
bank-set idiom instead of (or in addition to) the long-addressing operand
itself. This is a specific, verified manifestation of the general
completeness problem in
`negative-from-addressing-root-not-shapes.md` — the "root" being
enumerated (ways to form an address into the table) was itself an
incomplete shape enumeration, not a true root-based search.
