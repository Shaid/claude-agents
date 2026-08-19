# A prior "proprietary/compressed, no readable structure" verdict often just means the real header was never located

**When it bites:** project docs describe an undecoded format as
"KT-compressed"/"encrypted"/"proprietary, no reference tooling" with "no
readable strings" — and you're about to either believe that verdict and
skip straight to compression-cracking work, or escalate it as a hard
codebreaker problem, without first re-deriving the byte offset of whatever
the *real* container header actually is.

**Confirmed on Fire Emblem: Three Houses (Switch, `chimera` project):** an
earlier pass's docs described the `.kldm` model-container family (DATA0
entries ~883-984) as "KT-compressed... no readable mesh-name strings...
proprietary Koei model format." A fresh byte dump of one such entry showed
the literal ASCII tag `"MDLK0001"` sitting in plain sight at a small fixed
offset (0x74) — not hidden, not obfuscated, just never located because the
prior pass's search apparently stopped at the outer per-entry archive
compression (`ktGzDecompress()`) without dumping and reading the
*decompressed* bytes far enough to find it. Past that tag: a completely
uncompressed, self-describing chain of the same public-template-documented
model format (`G1M`, magic `"_M1G"`) already confirmed elsewhere in the
same game — no proprietary compression existed at all. The "no readable
strings" claim was true only because the scan that produced it never
reached the offset where the readable tag actually starts.

**Why this keeps happening:** "high entropy" and "no readable strings"
are properties of *where you looked*, not properties of the whole file.
A format with a short ASCII/ID header followed by dense binary payload
(mesh vertex data, texture blocks, compiled bytecode — all naturally
high-entropy) will fail a naive full-file strings scan or an entropy
histogram taken from byte 0, even though the header itself is trivially
readable a few dozen to a few hundred bytes in. A verdict written after
one such scan reads exactly like a verdict written after genuinely
exhausting compression-cracking attempts — nothing in the prose
distinguishes "we looked hard and it's really compressed" from "we didn't
look far enough."

**Fix:** before trusting (or escalating) an existing "compressed/
proprietary, no strings" verdict on a format nobody has fully cracked yet,
re-dump the raw bytes yourself and scan for: (a) any known sibling
format's magic bytes appearing anywhere in the first few hundred bytes,
not just at offset 0 — many containers have a small preamble before the
real payload starts; (b) ASCII runs at *every* offset a coarse hex dump
shows a printable run, not just the very start of the file; (c) whether
any "compressed" classification was made on bytes that were themselves
still wrapped in an *outer* container's own compression layer (per-entry
archive compression is common and easy to forget you're still inside).
Only escalate or begin real decompression work once you've confirmed the
bytes you're calling "compressed" survive this check — cheap (minutes),
and it turned what this session's brief called "a genuinely hard, bounded
RE problem" worth an Opus escalation into a same-session solve.
