# A Musashi 68000 harness silently no-ops a trace-vector-driven self-decrypting loop unless `M68K_EMULATE_TRACE` is explicitly turned on

**When it bites:** a Musashi (or similar 68000) harness runs a protection or loader routine that sets the T-bit and hooks `$24.l` (Trace, vector 9) to decrypt code one step at a time. The output turns to garbage after a few instructions, with no error. Also: you need to prove there's no hidden caller inside self-decrypting code, which static scans can't reach.

The routine sets the CPU's T-bit, installs a handler on `$24.l`, and lets
each single-stepped instruction trigger a trace exception whose handler
decrypts the next few bytes before returning — common in trace-vector-hijack
anti-debug/copy-protection schemes (see
`illegal-vector-hijack-anti-debug-desyncs-disasm.md` for the sibling
illegal-instruction-vector variant). Musashi ships `M68K_EMULATE_TRACE`
**disabled by default** (`M68K_OPT_OFF` in `m68kconf.h`) — with it off, the
core silently never raises trace exceptions at all. The harness still runs,
still executes some real instructions, produces no crash and no error, but
the self-decrypting loop's handler is simply never invoked: the CPU runs
straight into the still-encrypted bytes as if they were plain opcodes,
producing garbage output (or a quick, confusing crash a few instructions in)
with nothing in the harness's own behavior pointing at the real cause.

Confirmed on Deuteros (Amiga, `methanoid`): a `re-codebreaker` escalation's
first harness attempt looked coherent for roughly ten instructions, then
silently began executing encrypted bytes as instructions — no exception, no
error, just wrong output. The fix was to enable `M68K_EMULATE_TRACE`
alongside `M68K_INSTRUCTION_HOOK` (needed for the per-instruction PC trace
that made the loop's shape visible at all) and `M68K_EMULATE_ADDRESS_ERROR`
(needed so a genuinely-bad decrypt shows up as a real address-error
exception instead of reading garbage memory silently) in the vendored
`musashi/m68kconf.h`. All three default to `M68K_OPT_OFF` in a stock
Musashi checkout.

**Fix:** before trusting *any* Musashi-harness output for code suspected of
using the Trace exception as part of its control flow (not just plain
`bsr`/`jmp`), grep the vendored `m68kconf.h` for
`M68K_EMULATE_TRACE`/`M68K_INSTRUCTION_HOOK`/`M68K_EMULATE_ADDRESS_ERROR`
and confirm all three are `M68K_OPT_ON`, not just present in the file. A
harness that "runs fine" with no crashes is not evidence these are
configured correctly — the failure mode here is silent divergence, not an
error. If the target routine only uses the Illegal Instruction vector
(`$10.l`, vector 4) rather than Trace, `M68K_EMULATE_TRACE` isn't needed for
that specific hijack, but check for both since a single protection scheme
can use one, the other, or several vectors in the same routine — **confirmed
on Millennium 2.2** (`methanoid`), whose mini-loader's illegal-vector
installer turned out (only visible once traced dynamically) to cover *all*
of vectors 2-9 (bus error through trace), not just the `$10`/`$20`/`$24`
subset a static disassembly pass had documented.

**Once the trace fires, the same harness answers "is there a hidden caller
inside this encrypted code" — a question pure static analysis structurally
cannot close.** A self-decrypting loop's transform is deterministic (same
address always XORs/adds the same value against the always-restored
original encrypted bytes), so hooking the decrypt-write instruction itself
and recording each address's *first* decrypted value reconstructs the
routine's full plaintext from inside the running harness — then that
plaintext can be disassembled and searched directly for a `JSR`/literal
reference a static scan of the still-encrypted on-disk bytes could never
find. Confirmed on Millennium 2.2: after 3+ billion real emulated
instructions never once reached a long-suspected-uncalled candidate
routine (`$6628C`, a track-copy utility structurally shaped for the
project's still-open "TDIC signature track" question), the harness's own
trace-vector handler turned out to be running exactly this kind of
self-decrypting loop (mem `$0410FE`-`$0415A6`, same structural technique
as Deuteros' already-documented "DISC COMPANY" protection) — reconstructing
its plaintext (a stable, converged 588 of 1196 bytes, confirmed by
comparing the capture at two very different total decrypt-cycle counts and
finding the identical footprint) and searching it found zero `JSR` opcodes
and zero references to the candidate address, closing the one gap the
project's otherwise-exhaustive static byte-pattern search could never rule
out on its own. **Convergence check, not instruction-count alone, proves
the capture is complete**: track both a hit counter (how many times the
decrypt instruction fired) and a captured-footprint size: if the footprint
stops growing while the hit counter keeps climbing, the region is fully
recovered, not partially sampled.