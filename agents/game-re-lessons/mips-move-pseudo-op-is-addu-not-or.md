# A hand-rolled MIPS decoder's "move" detector must accept ADDU, not just OR

**When it bites:** writing (or reusing) a hand-rolled MIPS bitfield decoder
for a verify script or disassembly helper, and it recognizes the `move
rd,rs` pseudo-instruction only as `or rd,rs,$zero` (SPECIAL funct `0x25`
with `rt==0`) — a check that looks textbook-correct (`or x,y,0 == x=y`) but
silently fails to match real compiled code.

Confirmed on Valkyrie Profile (PSX, `valkyrie`): a verify script's
instruction-level assertions for several `move $reg,$reg` sites (e.g.
`move $a3,$a0` at a function's own entry) all failed even though the raw
bytes were correct and a separate hand-mnemonic-izer printed `move`
correctly for the same address. The decoder's `move` check tested
`funct === 0x25` (OR); the actual compiled encoding was `funct === 0x21`
(ADDU) with `rt` forced to `$zero`. Both `or rd,rs,$zero` and `addu
rd,rs,$zero` are architecturally valid ways to implement "copy register,"
but the real toolchain that built this game's executable (and, by
extension, most PSX-era MIPS compilers) overwhelmingly emits **ADDU**, not
OR, for the `move` pseudo-op. 18 assertions failed in one pass, every one
traced back to this single wrong assumption.

**Fix:** a "move" detector must accept **both** `funct 0x21` (ADDU) and
`funct 0x25` (OR) with the appropriate zero operand (rt==0 for `rd,rs,rt`
encodings), or — better — check the real emitted encoding at one known-good
address before hard-coding either. Don't assume a pseudo-instruction's
"canonical" textbook encoding is what a specific compiler actually emits;
verify it against real disassembled bytes first, the same discipline this
project already applies to sign-extension tricks and branch polarity.
