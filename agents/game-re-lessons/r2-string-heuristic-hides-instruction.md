# radare2's inline-string heuristic can hide a real instruction inside a disassembly listing

**When it bites:** a register-flow narrative you're building from an r2
disassembly listing doesn't add up (a call argument would have to hold an
implausible/impossible value — e.g. a memcpy destination that's a tiny
allocator-internal scratch constant, not a real pointer), and somewhere in
the instructions you skipped over, r2 printed a short `.string "..."`
literal immediately after a `jal`/`bl`/`call` or right before a small
aligned boundary, inside a function body that's otherwise all code.

r2's linear disassembler runs its own data-vs-code heuristic per address,
and a short run of printable ASCII bytes can outvote "this is inside a
function, decode it as an instruction" — even when the bytes are a real
instruction whose encoding just happens to look like text. Confirmed twice
in the same MIPS (PSX) function: bytes `21 20 40 00` were shown as
`.string "! @"` but decode as `addu a0, v0, zero` (`move a0, v0`), and
bytes `53 41 00 0c` were shown as `.string "SA"` but are the first two
bytes of a real `jal 0x8001054c`. Both were caught only because the
surrounding trace produced a nonsensical register value if the flagged
bytes really were dead data — the "string" sat exactly at the address a
preceding `jal`'s return would land on, which is a strong tell that
something is being skipped over.

**Fix:** don't trust the wider listing's data/code split at a suspicious
boundary. Call the disassemble-at-address tool starting **exactly** at the
flagged offset (not a few bytes before) — this forces a fresh per-address
decode that bypasses the heuristic and will show the real instruction if
there is one. Cheaper still as a cross-check: hex-dump the same bytes and
hand-decode the opcode fields (MIPS: 6/5/5/16 or 6/5/5/5/5/6 bit split)
against what the tool claims — a real instruction's fields will make sense
(valid register numbers, a plausible immediate/target) where genuine string
data won't decode to anything coherent as an opcode. This is a general r2
quirk, not architecture-specific — the same "printable bytes look like a
string more than an instruction" ambiguity can occur on any ISA r2
disassembles linearly.
