# An "unexplained edge case" in a probe-derived header may be an artifact of the wrong header width

**When it bites:** a header layout was derived by structural probing (before
any disassembly/escalation gave ground truth), the docs flag one field's
behavior as a genuine unsolved anomaly (a "mystery byte," a sentinel value
whose meaning is unclear, an off-by-N padding gap) — and later, an
authoritative source (disassembly, a `re-codebreaker` escalation) gives the
*real* header layout for the same format, differing in width from the
original guess.

Don't just accept the new layout and move on — actively revisit every
"unexplained edge case" that was flagged against the *old* guess. It may
not be a real remaining puzzle at all, just an artifact of the wrong header
width.

Confirmed on Valkyrie Profile 2: Silmeria (PS2, `~/Development/valkyrie`):
an early probing pass guessed the "SL" resource-record header was 17 bytes
(3-byte magic + 1-byte type + 1-byte version + three 4-byte fields + one
trailing "extra" byte, values `0x7f`/`0xff`/`0x96` observed and left
unexplained). Under that guess, one record's stride field read `0`,
breaking the simple "next record = this offset + stride" chaining rule —
documented as a genuine unsolved edge case ("what does stride==0 mean?"),
with a forward byte-scan finding the real next record 671 bytes later at a
sector-aligned boundary, seemingly confirming there was a real, distinct
behavior to explain.

A later `re-codebreaker` escalation disassembled the game's own loader and
found the *true* header is **16 bytes**, not 17 — the previous 17th byte
was never a header field at all, it was simply the first byte of the
payload's own LZSS control-bitstream (which happened to look like a
plausible flag byte by coincidence). Once the real 16-byte layout was used
to re-walk every chain, `stride == 0` turned out to mean exactly what it
looks like: "this is the last record in the chain, decode it and stop" —
true without exception across all 41 real chains (125 records) on the
disc. There was never a special case to explain; the "0x7f/0xff/0x96
mystery byte" and the "stride==0 anomaly" were both downstream of the same
one-byte-too-wide guess.

**The generalizable move**: when ground truth changes a probe-derived
header's byte width (even by one byte), treat every "not yet understood"
note filed against the old width as suspect, not settled. Re-derive each
one against the new layout before deciding it's still open — a real
anomaly and a width-guess artifact can look identical from the probing
side (both present as "this field's value doesn't fit the pattern"), but
only one of them survives contact with the correct struct.
