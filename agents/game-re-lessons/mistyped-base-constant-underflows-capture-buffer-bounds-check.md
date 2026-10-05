# A capture buffer's own "hits happened" counter can be nonzero while its "data captured" counter stays zero — one mistyped hex digit in the base constant, not a logic bug

**When it bites:** writing instrumentation into a CPU-emulation harness (or
any hook-driven capture: a memory-write watcher, a per-address sample
recorder) that computes `offset = address - REGION_BASE` before writing
into a small fixed-size buffer guarded by `if (offset + width <=
BUFFER_SIZE)`. If a report/trace log shows the *hook itself* firing many
times (a hit counter climbing into the millions) while the *captured data*
stays completely empty (a "bytes actually recorded" counter reads zero, or
a reconstructed dump file is 0 bytes), don't start debugging the hook's
trigger condition or the surrounding control flow — the hook is working
fine; the bounds check silently rejecting every single write is the bug.

Confirmed on Millennium 2.2 (`methanoid`, `tools/millenium22/emu/emu.c`): a
self-decrypting-code plaintext-reconstruction capture (see
`m68k-trace-vector-decrypt-needs-emulate-trace-on.md`) defined its capture
region as `#define PLAINTEXT_LO 0x410000u` — one extra zero digit versus
the real mini-loader base address `0x41000` used correctly everywhere else
in the same file. Every real decrypt address (e.g. `$0410FE`) is *smaller*
than `0x410000`, so `unsigned off = a0 - PLAINTEXT_LO` wrapped around to a
huge unsigned value on every single call, and `off + 4 <= PLAINTEXT_SZ`
was therefore always false — silently skipping the capture write every
time, for tens of millions of real, correctly-detected decrypt events, with
no crash, no warning, and a perfectly plausible-looking non-zero
`decrypt_hits` counter in the trace output. The bug was caught only by
adding a second, independent counter (`seen_sum`, a straight sum over the
"was this byte ever written" mask) and finding it stayed at exactly 0 while
`decrypt_hits` read in the tens of millions — a stark, immediate signal
once checked, invisible until then.

**Fix:** whenever a capture/instrumentation path reports "N events
happened" but the resulting captured artifact is empty (an all-zero buffer,
a 0-byte output file, an empty reconstructed range), first suspect
address-window arithmetic — recompute the base constant against a value
already confirmed correct elsewhere in the same file (grep for the same
region's other, already-working use, e.g. a PC-range check using the
correct `0x41000u`) rather than re-deriving it from scratch a second time.
Cheap general habit: track an activity counter (hook fired) and a distinct
capture counter (bytes/records actually written) as two separate numbers
in every such instrumentation path, and treat any run where one is nonzero
and the other is zero as a bounds/offset bug, not a "nothing interesting
happened here" negative result.
