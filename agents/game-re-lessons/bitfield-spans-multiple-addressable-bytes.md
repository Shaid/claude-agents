# A multi-byte flag field is N independently addressable bytes — a bit-N search must cover every one

**When it bites:** you're searching a disassembly for "what tests bit N of this
flags field", the field is a `u16`/`u32` rather than a single byte, and the
search comes back empty — or worse, comes back with exactly one hit that you're
about to attribute to the wrong bit.

A `BTST #n` (or `TST`/`AND`/`BSET`) against a big-endian `u16` at offset `X`
does **not** carry `#n` for n >= 8. The compiler addresses the byte the bit
lives in and uses `#(n mod 8)`. So word bit 8 is emitted as `BTST #0` against
offset `X` (the **high** byte on a big-endian target), and word bit 0 is `BTST
#0` against offset `X+1` (the low byte). Both instructions carry the immediate
`#0`. They differ by a single byte in the operand, and nothing else.

Worked example (War in Middle Earth, Amiga, `middilgard` project): the entity
item bitmask is a big-endian `u16` at `entity+0x10`. Two instructions:

```
CODE+0x0F41C:  08 30 00 00 08 00   BTST #0, entity+0x10  (high byte) = word bit 8  = Elven cloak
CODE+0x1092C:  08 30 00 00 08 01   BTST #0, entity+0x11  (low byte)  = word bit 0  = the Ring
```

The cloak's effect (+20 to the party's encounter evasion score) went unfound
across **multiple sessions and three separate searches** — two searches for the
bit number `#8`, and one census enumerating operand shapes around the field's
own offset `0x10`. All three were structurally incapable of finding it: there is
no `#8` immediate anywhere, and the instruction's operand is a base displacement
of `0x00` inside an indexed mode, not a `16(An)` form.

Worse than the miss: the *other* instruction — the genuine Ring test — was
pattern-matched to the `ADDI.W #$0014` sitting near it and written up as "the
confirmed source of the +20 Ring Bearer bonus". That bonus never existed. The
`ADDI.W #$0014` occurs exactly once in the whole encounter block and belongs to
the cloak. A phantom mechanic sat in the project docs for a long time because
two instructions differing by one byte were assumed to be the same one.

**Fix:** before searching for bit N of a multi-byte field, compute which byte it
lives in for the target's endianness, and search `BTST #(n mod 8)` against
**every** byte offset the field spans — not just the field's own offset.
Searching offset `X` alone only ever finds bits 0-7 (little-endian) or the top
byte's bits (big-endian). When you do find a candidate, confirm *which* bit it
is from the operand byte, not from what happens to be nearby in the code.

Sibling lessons on the same family of census failure:
`narrow-opcode-form-census-false-negative.md` (missing a register-class variant
of the addressing mode) and `lvo-byte-pattern-false-positive.md` (a byte match
that isn't the call you think). Together: a raw-opcode census needs coverage
across opcode forms, across register classes, **and across every byte a
multi-byte operand spans**, before either a hit or a miss can be trusted.
