# All-zero placeholder files inflate a batch decode run's failure count — classify before reporting

**When it bites:** a batch decode/export run across a large real corpus
reports a success rate noticeably below 100% (e.g. "77.9% ok"), and the
per-file error messages for the failures all describe the same
symptom — a missing/zero magic, "wrong header," "probably encrypted" —
concentrated in whole-prefix groups of otherwise-related files (a cut
level, a removed feature, a whole content category).

Commercial game builds routinely ship **genuinely all-zero stub files** in
place of removed/cut content — the file's directory entry and expected
size survive to retail (build tooling, disc layout, or a manifest
generator didn't bother stripping the entry), but the payload was
zero-padded rather than deleted. A decoder correctly reports these as
unparseable (there's no real header to find), and that correct behavior
looks identical to a real decode failure in a raw pass/fail tally unless
you check.

Confirmed on Drakengard 3 (PS3): a full-corpus `umodel` export across 3,238
UE3 packages reported 2,522 ok / 716 failed (77.9%). Independently checking
each failed file's first 4 bytes (plain Python `open().read(4)`, not
trusting the tool's own error text) found exactly 715 of the 716 are
byte-for-byte all-zero — the same benign "cut content shipped as zero
padding" pattern already independently confirmed for one specific known
file in the same corpus (`GLOBALPERSISTENTCOOKERDATA.UPK`, 44MB, entirely
zero). That left **exactly 1** file with a genuine, unexplained decode
error out of 3,238 — a 99.96% real success rate, not 77.9%.

**The fix**: before reporting or acting on a batch run's raw failure count,
partition the failures by a cheap independent check (read the first N
bytes, compare against a zero buffer) rather than assuming every reported
failure is a format/tooling problem. This matters for two different
reasons depending on direction: undercounting success makes a genuinely
working pipeline look broken or incomplete (wasted debugging effort
chasing "failures" that aren't); and it also means a future automated
health-check for this corpus should special-case the all-zero pattern
(exclude it from the denominator, or track it as its own "known-empty"
category) rather than re-discovering this by hand every run.

Related: `optional-per-record-compression.md` (the sibling case where a
"corrupt" minority turns out to be a real, if under-handled, format
variant rather than empty content) and
`wildcard-batch-tool-aborts-on-first-bad-file.md` (a different failure
mode in the same kind of batch run, worth checking alongside this one).
