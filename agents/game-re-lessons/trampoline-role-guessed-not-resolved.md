# A prior session's cited role for an indirect/trampoline call is unverified until you've actually read its target function body

**When it bites:** you're about to reuse a doc's claim about what an
A4-relative (SAS/C small-data trampoline), A6-relative LVO, or other
indirect call "does" — especially a claim justified only by the call's
*argument shape* (an operand that happens to look like a familiar size/
count) or by a *nearby comparison constant*, with no citation of the
target function's own disassembled body.

An indirect call's real behaviour can only be confirmed by resolving the
trampoline/vector to its concrete target address and reading what that
target function actually does — argument shape and surrounding context are
suggestive, not proof, and can point to a completely wrong conclusion that
still "reads" as plausible. Confirmed on Wings (Amiga): a prior session
described an A4-relative call (`JSR -32616(A4)`) as "going through what
looks like DOS `Read()`/`Write()` LVOs" with "an 8-byte transfer size"
argument — a reasonable-sounding guess given the call sat inside a
file-load routine and pushed a `#$0008` immediate. Actually resolving the
SAS/C trampoline (`hunk1_offset = (N + 0x7FFE) & 0xFFFF`, then reading the
6-byte `4EF9`-prefixed stub's 4-byte target as a hunk0 CODE offset) and
disassembling the target function showed it was a `TestBit(buffer,
bitIndex)` helper (`DIVS #8` / `SWAP` byte-bit split, then `AND` against
`1<<bitRem`) — completely unrelated to file I/O, and the `#$0008` was a
bit index (bit 0 of the buffer's 2nd byte), not a transfer size. The
*real* bulk-read/write calls turned out to be two entirely different
trampolines nearby, distinguishable by their own target functions' bodies
having the genuine `fread`/`fwrite`-equivalent shape (`buffer, elemSize,
count, fh` argument reads plus a byte-copy loop). The wrong guess survived
an entire prior session uncorrected because nothing forced anyone to
actually open the target function and read it.

**Fix:** before reusing or extending any doc's claim about what an
indirect call does, check whether the doc's own evidence includes the
target function's resolved address *and* a citation into its disassembled
body (not just the call site's argument shape or a nearby constant). If
it doesn't, re-resolve the trampoline/vector yourself and read the target
before trusting or building on the claim — this is cheap (one arithmetic
formula plus a short disassembly read) relative to the cost of an entire
session's tracing built on a wrong premise.

**Not Amiga-specific — the same trap fires for a plain `jal`/`bl`/`call`
on any platform when a doc names a specific call as "the mechanism to
trace" on the strength of the call *site's* location alone, without
having read the callee's body.** Confirmed on Valkyrie Profile (PSX,
MIPS): a project doc recorded "recovering overlay X's runtime load base
via the installer's `jal 0x8001fd80`" as the concrete next step for a
stalled item. Disassembling `0x8001fd80`'s target showed it was a generic
wait/poll primitive (loops calling one helper until it returns nonzero,
polling a callback pointer along the way) — called all over the same
binary with unrelated arguments (a raw byte-size value in this instance),
with no connection to overlay loading at all. The real relocation
mechanism was a *different*, later call site in the same function, whose
target's body contained a literal hardcoded `jal <fixed base address>` —
recognizable specifically by reading what the callee *does with its
arguments and where it ultimately transfers control*, not by the call
site's position in the doc's narrative. A fast discriminator once you
have two candidate calls: does the callee's return value get used by the
caller (real logic) or discarded (generic side-effect/wait utility), and
is the callee's own body's control-transfer target a literal fixed
address (loader-shaped) or itself another indirection (utility-shaped)?

**A second, narrower shape of the same trap: two *already fully known*
targets can be visually indistinguishable at a single call site.** This
isn't about an unresolved trampoline at all — both candidate functions
were independently confirmed elsewhere in the same session — but a raw
disassembly's `JSR $0.L` (an absolute-long operand whose pre-relocation
stored value is `0`) looks identical at every call site where it appears,
because **more than one already-confirmed helper can each sit at
hunk-relative offset `0` within its own hunk**. Confirmed on nicodemus/
Phantasie I's combat-formula trace: both the confirmed 32-bit multiply
helper (hunk 206) and the confirmed 32-bit divide helper (hunk 203) begin
at their own hunk's offset `0`, so every call to either shows as the
byte-identical `4EB9 00000000` — reading the mnemonic text alone very
nearly caused one specific call site to be documented as a divide when
`HUNK_RELOC32` resolution (per `game-re-tooling/amiga.md`'s reverse-
lookup technique) showed it was actually the multiply helper, which would
have inverted an operator in a combat formula written up as "confirmed."
**Fix:** never infer which of two-or-more already-known targets a `JSR
$0.L`/similar zero-or-shared-offset call site reaches from mnemonic text
or surrounding arithmetic shape alone — resolve every such call site's
`HUNK_RELOC32` entry individually, even when both candidates are already
fully understood, and even mid-trace through a long formula where most of
the preceding calls turned out to resolve "as expected."
