# A hardware/MCU protection check's "expected value" table can be the literal opcode bytes of the very next real instructions, not a separate data label

**When it bites:** disassembling a copy-protection handshake (a main CPU
checking a reply from a dedicated protection MCU/ASIC, or any "read a
value, compare against an expected constant" check) where a `LD reg,
addr` / `LEA` / equivalent loads a pointer that turns out to equal
"the address of the instruction immediately following this load" — before
concluding that's dead code, a disassembly desync, or an unrelated
pointer, check whether it's a deliberate self-referential lookup table.

Confirmed on Black Tiger (Capcom, 1987, arcade — `kolbold` project): the
Z80 main CPU's protection-check routine does `LD HL, <addr>` where
`<addr>` is exactly the address of the very next opcode byte (the `PUSH
DE` immediately following), then indexes `HL + maskedCommandByte` and
reads a byte from there to compare against the MCU's actual reply. The
CPU is NOT jumping there or treating it as data at runtime — it falls
through and executes those exact same bytes as real instructions a few
lines later, in the ordinary control-flow sequence. The 16 bytes at that
address, read as data by the check and executed as code moments later,
are simultaneously a valid opcode sequence AND (by construction) the
"expected reply" table — confirmed byte-identical, at two independent
call sites, to the actual lookup table baked into the protection MCU's
own internal ROM.

This is a distinct trick from `self-modifying-code-parameter-passing.md`
(a code-stream literal used as a *writable* parameter slot poked before a
call) and from ordinary self-modifying-code patching
(`crack-redirects-io-to-resident-loader-stub.md`) — here nothing is ever
written; the same static bytes serve two roles (data table when read
in-place, instruction stream when executed) by design, likely specifically
to make the "expected" values harder to spot with a naive strings/data
scan (they're indistinguishable from ordinary code until you notice the
pointer arithmetic).

**Fix:** when a loaded pointer's value equals "this instruction's own end
address" or "the address of the next instruction" with no intervening
label, don't dismiss it as unreachable/dead — dump the raw bytes at that
address and check whether they (a) decode as plausible real code AND (b)
also read sensibly as a data table for the surrounding check's own logic
(a small fixed-size array, indexed by a value already computed nearby).
If a second independent copy of the same table exists elsewhere (another
call site, or the compared-against device's own ROM), a byte-exact match
across all copies is decisive confirmation, not a coincidence.
