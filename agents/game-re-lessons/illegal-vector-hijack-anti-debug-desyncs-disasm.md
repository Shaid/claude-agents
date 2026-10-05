# A self-installed illegal-instruction-vector handler is anti-debug armor, and its resume point defeats linear disassembly

**When it bites:** disassembling Amiga (or any 68k-family) protection/loader
code and you find the shape `moveq #0,dN... ; pea <label>(pc) ; move.l
(a7)+,$10.l ; illegal` — computing a PC-relative address, storing it into
the absolute CPU exception-vector slot for Illegal Instruction (`$10.l`,
vector 4), then immediately executing the `illegal` opcode (`0x4AFC`) to
deliberately trigger it. From `<label>` onward, straight-line disassembly
desyncs almost immediately into a run of `invalid` opcodes interleaved with
what look like `move.l #<pseudo-random 32-bit constant>,-(a7)` pushes.

This is a deliberate, self-installed anti-debug/anti-trace technique, not a
disassembler bug or a misidentified load base. The code intentionally
routes control through the CPU's own exception mechanism (`illegal` →
vector fetch → handler entry) rather than a plain `bsr`/`jmp`, and the
bytes right after the resume label are commonly further obfuscated
(self-modifying, a second nested vector hijack, or plain disassembler-
hostile junk-byte interleaving) specifically so that anyone reading the
file linearly — a cracker or an RE tool alike — gets garbage the instant
they try to read past the `illegal` opcode by eye. Confirmed independently
on **two unrelated commercial Amiga games sharing this account's corpus**:
Millennium 2.2's mini-loader (multi-vector: also hijacks `$20.l`/`$24.l`,
privilege-violation/trace) and Deuteros's mini-loader (single-vector,
`$10.l` only, at file offset `0x9AE` within the loaded blob) — both
protected by the same undocumented "Disc Company" scheme (see
`game-re-corpora/methanoid.md`), suggesting this is a stock technique from
that toolkit rather than bespoke-per-game code, and worth watching for on
any other title using the same or a similar licensed protection product.

**Fix:** don't keep hand-disassembling past the resume point hoping the
bytes resynchronize — they may never cleanly do so under a straight-line
read, by design. This is exactly the class of problem Method §5 (`Read
~/.claude/agents/game-re.md`) calls for emulation on: run the game's own
code under a headless CPU-core harness (musashi or similar — see
`~/.claude/agents/game-re-method/cpu-emulation-boot-harness.md` and
crawl's `tools/bcdft_decompress/` worked example) that boots straight into
the hijack sequence, lets the real hardware exception mechanism dispatch
to the handler, and traces/dumps what it actually does (PC trace, absolute
writes, and where it eventually `RTE`s back to) — rather than trying to
statically resolve the desync by eye or by pattern-matching junk bytes.

**Worked example — the fix applied end to end:** Deuteros's instance was
fully solved (not just structurally confirmed) by a `re-codebreaker`
escalation that built exactly the harness this lesson recommends —
`tools/deuteros/emu/`, a vendored Musashi core, executes the real routine
at `Disk.1+0x131AE` and dumps a 2,094-line decrypted disassembly. The
routine turned out to be a 3-layer CPU-probe → self-decrypting
trace-vector loop → CIA hardware-timing check against a magic constant
(independently spot-verified byte-exact on Disk.1, absent from Disk.2).
Getting the harness to actually decrypt the loop needed one further,
non-obvious Musashi configuration fix — see
`m68k-trace-vector-decrypt-needs-emulate-trace-on.md`.