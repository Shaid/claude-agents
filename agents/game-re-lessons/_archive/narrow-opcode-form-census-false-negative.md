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

**This also applies to encoding-*width* variants, not just addressing-mode/
register-class variants — and can produce an under*count* rather than a
clean zero.** Censusing "how many trampoline stubs branch to routine X"
(Knights of the Round, CPS1: a scan for `moveq #N,d0` immediately followed
by `bra.w TARGET` to count distinct sound-command IDs) initially missed
real hits at both ends of the count: short-branch encodings (`bra.b`, a
1-byte displacement, emitted whenever the target is close enough) alongside
the long-branch (`bra.w`, 2-byte displacement) form the census only checked
for, *and* a second, sibling entry point (a few bytes past `TARGET`, an
unconditional version of the same push routine that some call sites branch
to directly, bypassing a conditional wrapper) that a single-target scan
never covers. Widening to both branch-displacement widths and both real
entry points raised the confirmed count from under 20 to 125. The general
form: a compiler/assembler picks the shortest sufficient encoding for a
given operand (an 8-bit branch displacement, a `moveq`-sized immediate) and
falls back to a wider form only when it doesn't fit — a census for "every
call site of X" must cover every width variant the assembler could have
chosen, not just the one in the first example inspected, and every
semantically-equivalent entry point, not just the one most obviously named.

**A whole-image "does anything reference table X" xref scan is exactly
this same trap, one addressing-mode layer up.** D&D: Shadows over Mystara
(CPS2, `kolbold`)'s monster-name table (`data+0xd6232`, a 21-entry pointer
array) was declared to have "zero runtime references anywhere in the
image" after a whole-4MB xref scan that searched only **PC-relative**
loads (`LEA (d16,PC),An`/`MOVE (d8,PC,Xn)`-shaped instructions) — the form
every *other* text/data table in this game happened to be referenced by.
The real consumer (a boss health-bar-and-name UI object's draw routine)
reached the table through a plain **absolute long constant**
(`MOVEA.L #imm.L,An`), a load form the PC-relative-only scan structurally
could not match, so "zero hits" measured the scan's own addressing-mode
coverage, not the table's actual reference count. The follow-up fix used a
different technique entirely, worth calling out on its own: instead of
widening the xref scan to also cover absolute-long forms (viable, but
still an xref search anchored on the *table's own address*, which varies
per table), a short literal byte-pattern census for an unrelated, already-
confirmed **marker instruction** a few bytes downstream of every real
consumer (here: `cmpi.b #$40,d0`, the byte-exact opcode encoding of the
game's confirmed string-terminator compare) found the real routine
directly, at a small fixed cost (7 hits total across the whole image, one
of them real) — because a short fixed-byte-sequence scan doesn't depend on
correct instruction-boundary alignment surviving a long linear
disassembly the way an operand-address xref scan does. When a table-
consumer search comes back empty, consider both fixes: widen the
addressing-mode coverage of the same xref search, *and* separately try a
marker-byte census anchored on something the consumer's *body* must
contain (a terminator check, a known register-write idiom) rather than on
a reference to the table's own address.

**The same trap applies to *write* sites, not just reads/references, and one
level below "addressing mode" — a census over one instruction *shape* misses
a semantically-identical write done through a different sequence of
instructions entirely.** D&D: Tower of Doom (CPS2, `kolbold`)'s monster/
player HP-init writes three consecutive fields (`$60`/`$62`/`$64`, max/
current/latch HP) via `lea $60(a0),a4 / move.w dN,(a4)+ / move.w dN,(a4)+ /
move.w dN,(a4)` — a post-increment write *through a scratch address
register*. A whole-4MB census for `move.w X,$60(An)` (the direct
`(d16,An)`-displacement instruction form, checked at every 2-byte-aligned
address — genuinely exhaustive for that one instruction shape) found only 6
hits, all unrelated, because the displacement `0x60` appears exactly *once*
in the whole idiom — inside the `lea` — and the three actual store
instructions that follow carry no displacement operand at all. The
project's own prior sibling game (ddsom) writes the identical three fields
with three separate `move.w d0,(d16,a0)` instructions, each carrying the
displacement directly — so the same search technique that had just worked
on one game silently failed on its prequel, for a reason invisible from the
search's own zero-hit result. The fix that found it: census the write
*idiom* instead of the write *operand* — search for `lea $60(aN),aM`
(anchored on the same numeric field offset, but as a *load-address*
operand, not a store-displacement operand) — which returned 26 whole-image
hits, 2 of which were the real HP-init routines. General shape: before
concluding "no code writes/reads field X" from a displacement-operand
census, ask whether a compiler/hand-coder could plausibly reach the same
field through an *address computed once and then walked* (post-increment,
pre-decrement, or a cached pointer field) rather than a fresh displaced
access every time — and if so, census the address-computation instruction
too, not just the direct-access one.

**A cheap, mechanical way to actually earn "this census found everything":**
once a single-register/single-form census has found a real consumer, widen
it to every register-class variant before treating the result as final —
don't wait for a specific reason to suspect a miss. A follow-up ddsom
session re-ran the exact terminator census above (`cmpi.b #$40,Dn`) against
all 8 data registers, not just D0. It found nothing new (the extra hits
were either already-known or genuine misaligned-data noise) — but that
negative result is only trustworthy *because* the wider sweep was run; the
original D0-only census could not have distinguished "no other consumer
exists" from "no other consumer happens to use D0." Running the full
register sweep routinely, immediately after the first hit, turns "we found
the consumer" into "we found every consumer this addressing mode could
produce" at negligible extra cost (7 registers x one pass over a 4 MB
image is seconds of work).

**Not just addressing-mode/idiom coverage — the operation itself can be
entirely absent as an opcode.** A whole-file `MULT`/`MULTU` opcode census
(R5900/PS2 EE, hunting for a claimed `seed * 1664525` LCG PRNG
multiply-by-constant) found **zero** instructions of either opcode
anywhere in an 18,432-byte overlay, and a follow-up search for the
literal constant bytes (`0x0019660D` as a raw 4-byte value, or as a
`lui`+`ori`/`addiu` immediate pair) also found zero — a result that
looked like solid, well-scoped grounds to flag the whole claim as wrong
(Valkyrie Profile 2, PS2, `valkyrie`). It wasn't: the compiler had
replaced the multiply with a **strength-reduced shift/add instruction
chain** (`dsll`/`daddu` pairs) instead of emitting any multiply opcode
at all — common when a compiler's cost model rates the target CPU's
integer multiply as more expensive than a handful of shifts and adds.
Hand-tracing the real `dsll`/`daddu` sequence symbolically against a
seed variable `S` (`S<<6=64S`, `64S+S=65S`, `65S<<6=4160S`, …) resolved
to *exactly* `1664525*S` at one specific instruction — proving the
multiply really was there, just not as a `MULT`/`MULTU` opcode. **Fix:**
before concluding a claimed multiply-by-constant is absent because no
multiply-family opcode exists in a search, check whether the constant
could be reached via strength reduction — symbolically trace nearby
shift/add (or `LEA`-chain, on x86; `LSL`/`ADD` combos, on ARM) sequences
against a symbolic input and see if they resolve to the claimed
constant before writing the claim off. This is the false-negative
counterpart to trusting a multiply opcode census at face value: the
opcode-shape being entirely absent doesn't mean the *operation* is
absent, only that the compiler chose a different encoding for it.

**Generalizing an already-confirmed per-type dispatch mechanism from one
object pool to a second, separate pool in the same engine hits this same
trap twice over, in a way that isn't obvious until the second pool's
numbers come up short.** D&D: Shadows over Mystara (CPS2, `kolbold`)'s
sprite-animation VM has one confirmed literal entry point (`jsr $1a32.l`)
plus a separately-confirmed shared trampoline (`opcodes+0x103d6`) that the
*first* pool (23 large/boss types) only ever reached via a 2-3-instruction
"pose-table triple" pattern converging on a shared tail. Reusing the
jsr-only literal-`$1a32` census (already proven on that first pool)
against a second, previously-untouched pool (the 28-type regular/22-slot
enemy pool) resolved only 18/28 types. The other 10 broke down into two
independent gaps, both invisible from the zero/low hit counts alone: (1)
several call sites used `jmp $1a32.l` (`4E F9`) instead of `jsr` (`4E B9`)
to the *identical* literal target — the same width/form-variant trap as
above, just for a call instruction instead of a data load; and (2) four
types reached the shared trampoline via a **third, previously-unseen
shape** — the exact same `moveq #ANIM,d0` / `movea.l #TABLE,a4` /
`jsr`-or-`jmp $103d6.l` operand pattern as the literal-`$1a32` direct call,
just targeting the trampoline address directly, with no pose-table triple
involved at all. Widening the census to cover both jsr and jmp, against
*both* the literal entry point and the trampoline, using the existing
direct-call lookback logic unmodified, closed 7 of the 10 gaps (25/28
total). **Fix, two-part:** (a) when censusing "does this pool/object
family call subroutine X," check both `jsr` and `jmp` forms to the exact
same target address, not just whichever one the first example used — a
tail-call convention is a per-call-site stylistic choice, not a
per-engine constant; (b) when a shared subroutine has more than one
confirmed *entry path* in one pool (a literal direct call and a
convergent-tail pattern, here), don't assume a second pool reusing that
subroutine reuses the same entry-path mix — check whether the second
pool also reaches it via the *other* already-known entry path used in a
shape you haven't yet checked (here: the trampoline address reached
through the *first* pool's own "direct call" shape, not its own
"pose-table" shape).

**Not just opcode/addressing-mode coverage — a control-flow-*shape* census
can be structurally blind to a semantically-equivalent implementation
using a different shape entirely.** Confirmed on Midwinter (1) (Amiga,
`hunter`): hunting for the game's terrain-fractal generator, a
self-recursive-function census (flag any function containing a `JSR`/
`BSR` whose target equals its own entry point — a natural signature for
midpoint-displacement/subdivision algorithms) found zero candidates among
~1046 functions, and that negative was reported as real evidence against
"stored seed, generated via recursive subdivision." It was a false
negative: the game's actual generator (`FUN_00002B8A`/`FUN_00002726`)
subdivides the same way conceptually but **iteratively** — a fixed
50-iteration loop (`DBF`) over grid rows, calling a shared kernel routine
from inside that loop rather than recursing into itself. A census scoped
to "does this function call itself" cannot see an iterative loop calling
a *different*, shared kernel function no matter how many times, because
no instruction anywhere targets its own containing function's entry
point. **Fix:** when hunting for a fractal/subdivision/tree-walk algorithm
by control-flow shape, don't rely on a self-recursion census alone —
independently look for a bounded counted loop (`DBF`/`decrement-branch`
or equivalent) whose body calls a small kernel function repeatedly, which
is exactly as good a signature and isn't defeated by the compiler/author
choosing iteration over recursion for the same algorithm.

**Mask-*construction* idiom diversity is the same trap one level below
opcode/addressing-mode form — a search for how a 32-bit inverse-mask
constant gets built can miss a real bit-clear site because the compiler
chose a cheaper single-instruction encoding for that specific mask.**
Confirmed on Valkyrie Profile (PSX, `valkyrie`): closing `obj+0xe8` bits 6
and 7 required finding where each got CLEARED, and every clear-mask search
run (across two full prior rounds, plus a `re-oracle` escalation for a
different bit pair in the same word) scanned only for the standard
`lui $r,0xffff; ori $r,$r,MASK` two-instruction idiom for building a
32-bit "clear these low bits" constant. The real clears used
`addiu $v1,$zero,-0x41` / `-0x81` — a **single sign-extended 16-bit
immediate** that produces `0xffffffbf`/`0xffffff7f` directly, because the
low byte's two's-complement negation (`-65`, `-129`) fits `addiu`'s signed
16-bit range whenever the mask only needs to clear a small number of bits
near the bottom of the word. Because no clear was found under the
`lui+ori` idiom, the bits looked like a one-way latch (set every frame,
never cleared) for most of a multi-round investigation, when they were
actually a genuine per-frame refresh with the clear hiding under an
untested encoding. **Fix:** when hunting for where a bitmask constant gets
built — to set OR to clear a bit — check both the `lui+ori`/`lui+addiu`
two-instruction form AND the single `addiu $r,$zero,±N` sign-extended-
immediate form (viable whenever the target constant, read as a signed
16-bit value, is in `[-32768, 32767]` — which includes every mask that
only touches the low ~15 bits from either direction) before concluding a
mask-construction site doesn't exist. The same idiom-choice logic applies
to any fixed-width-immediate ISA (ARM's `MVN`+shifted-immediate vs a
literal pool load, x86's sign-extended 8-bit immediate forms of `AND`/`OR`
vs a full 32-bit immediate) — a compiler/hand-coder picks the shortest
encoding that reaches the needed constant, and a search for "how is this
mask built" that only knows one encoding will silently miss every site
that used the other.

**A generic property-table/API dispatcher's own "boolean read" idiom is a
distinct test SHAPE from the idiom ordinary engine code uses to test the
identical bit — not a rare edge case worth excluding, a routine second
form to always check.** Confirmed on Valkyrie Profile (PSX, `valkyrie`):
`obj+0xe4` bit 3's reader-site census used `LW $r,0xe4($base)` immediately
followed by `ANDI $r2,$r,8` — the idiom ~50 of its 51 published sites
share. The one deliberately-excluded site, the script-facing `GETPROP 46`
property-read dispatcher, tests the SAME bit via `SRL $r,3` (shift the
target bit down to bit 0) then `XORI $r,1` then `ANDI $r,1` — the generic
"shift-and-return-a-boolean" shape EVERY ONE of that dispatch table's 42
read-property handlers uses for its OWN bit, not a quirk specific to
property 46. It had been correctly excluded from the original count with a
note that it used "a different idiom," but a later reproduction attempt
almost re-derived the same undercount from scratch before realizing the
excluded site needed its own detection branch, not just a wider window on
the `ANDI` scan. **Fix:** whenever a bit/field is tested by both ordinary
inline engine code AND read through a generic property-table/API/RPC
dispatcher that resolves "which field, which bit" from a runtime id, expect
the dispatcher's own handler to use a DIFFERENT, more mechanical idiom
(shift-then-mask, or a jump-table of pre-built mask constants) than the
bespoke idiom a human wrote inline elsewhere for the same bit — census both
shapes from the start, rather than treating the dispatcher's one entry as
an excluded special case to fold in "later."

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
