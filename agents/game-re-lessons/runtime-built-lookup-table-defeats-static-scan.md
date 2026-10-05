# A table built by a loop at runtime has no static bytes for a byte-pattern scan to find

**When it bites:** repeated, well-designed static byte-pattern scans for a
known-shape lookup table (a palette, a copper list, a jump table, a
register/data pair list) all come back empty or find only false positives
(ordinary code that coincidentally matches the shape, or an unrelated data
table), even though the game visibly *has* the effect that table should
produce (colours change, a jump dispatches correctly, etc). Each individual
scan is well-motivated and its negative result looks like proof the table
"isn't there as static data" — but the conclusion drawn is usually "must be
elsewhere" rather than "may not exist as data at all."

Confirmed on Powermonger (Amiga): the OCS colour palette was invisible to
three independently well-reasoned static scans — (1) runs of 16+ consecutive
`$0RGB`-shaped words (found only ordinary 68k code whose opcodes/
displacements coincidentally have a zero top nibble), (2) a copper-list-style
table of `(register, data)` word pairs walking `$180..$1BE` (found only
partial 3-of-16-register coincidences inside unrelated jump tables), (3) the
literal 32-bit hardware register address `$dff180` (found exactly one hit —
a boot-time "blank every colour register to 0" loop, not a palette load).
The real mechanism: the game's copper list is **built by a loop at runtime**
— register numbers generated arithmetically (`move.w #$180,d0; …; addq.w
#2,d0`, 32 iterations) rather than stored as a static table anywhere in the
binary. No static-data byte scan could ever find this, because the table it
was looking for is a temporary artifact of code execution, not a resource
sitting in the file. The actual palette *values* (plain, plausible-looking
`$0RGB` words) did exist statically nearby, but were indistinguishable from
false positives by pattern alone — they were only confirmed by tracing real
`lea $XXXX,aN` disassembly cross-references from the code that reads them.

**The fix:** after two or three differently-shaped static scans for a
known-effect lookup table all come back empty or noisy, treat "the table is
generated at runtime, not stored" as a live hypothesis — not a last resort,
a peer hypothesis to "I haven't found the right byte pattern yet." The
signature to look for in disassembly is a **small loop that computes a
register/address argument arithmetically** (an increasing/decreasing
immediate, or an indexed address building up an offset) rather than reading
one from a fixed table. Once such a loop is found, the *values* it consumes
(not the registers it writes to) are the real static data worth treating as
a palette/table candidate — cross-reference via real code xrefs (`lea`,
`movea.l #imm`) into that region, not another blind byte-pattern sweep.
