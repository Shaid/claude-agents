# An opcode census for "does any code reference this" is only as complete as its addressing-mode/register-class coverage

**When it bites:** a byte-pattern census across a whole binary for "does any
code load/reference constant X" (a fixed struct offset, an A5-relative
slot, an absolute address) comes back with zero hits, and you're about to
write that up as "no consumer exists" — especially when other, structurally
identical constants in the *same* family (siblings in an already-confirmed
directory/table) *did* get real hits from the same census.

Black Crypt Amiga's `bcdfa` container-directory slot `0xE8` produced zero
hits from a census that searched only `MOVEA.L (d16,A5),An` and
`ADDA.L (d16,A5),An` opcode forms (all 8 address-register variants) — the
same census that correctly found real, already-documented consumer code for
sibling slots `0xD4`, `0xDC`, `0xB4`, `0xE0` in the identical directory. The
zero-hit slot was written up as "no compile-time-constant consumer exists
anywhere in the traced corpus," a load-bearing wrong conclusion (it blocked
identifying the whole 20,195-byte bank). The real consumer used
`MOVE.L (d16,A5),Dn` — a **data-register** load, reading the slot as a plain
32-bit value rather than dereferencing it into an address register — a form
the census never covered. Widening the scan by one opcode-encoding family
(`0x2000|(n<<9)|0x6D` for An targets → also `0x2200|(n<<9)|0x2D`-style
forms for Dn targets) found the consumer immediately, plus two sibling
slots' consumers within 40 bytes of it.

**Fix:** treat a same-family census that hits on *most* members but misses
one or two as a signal to widen opcode-form coverage before concluding
absence, not as proof the miss is genuinely unreferenced. Before writing
"no consumer found" from any opcode-byte census, enumerate every
register-class variant of the relevant addressing mode that a compiler
could plausibly emit for "read this value" — at minimum address-register
loads (`MOVEA`/`ADDA`/`LEA`) *and* data-register loads (`MOVE.L …,Dn`) *and*
comparison/test forms (`CMPA`/`TST`) — not just whichever form happened to
work for the sibling constants already checked. This is the false-negative
counterpart to `lvo-byte-pattern-false-positive.md` (which covers the
opposite failure: an opcode match that looks like a hit but isn't the
function you think it is because of ambiguous LVO reuse) — together they
say a raw-opcode census needs both narrower filtering (reject false
positives by provenance) and broader coverage (avoid false negatives by
enumerating opcode forms) before its result can be trusted either way.

Not 68k-specific: the same trap hit a 65816/SNES hardware-register census
(Urban Strike SNES). A search for `STA $2121`/`STA $2122` (CGADD/CGDATA,
**absolute** 3-byte addressing) came back zero hits despite the game
genuinely writing those registers, because the actual code set the direct-
page register to `$2100` once and then addressed them as `$21`/`$22` via
**direct-page** 2-byte addressing — a totally different opcode family, not
just a different register-class variant of the same mode. The fix
generalizes across CPUs: when a hardware/memory-mapped register can be
reached through more than one addressing mode (absolute, direct-page/zero-
page, indexed, indirect), a census restricted to one mode can find *real,
working code* for some registers (e.g. a sibling VRAM DMA setup a few
functions away, which happened to use absolute addressing) while showing
zero hits for a register genuinely written elsewhere via a different mode
— don't read that contrast as "this register is unused," read it as "widen
the addressing-mode coverage."
