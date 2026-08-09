# A bundled utility's `strings` output full of short scrambled-looking runs may be plaintext reversed per fragment, not encrypted

**When it bites:** `strings`/a printable-run regex scan over a small
bundled tool (an installer, disk-copier, cracktro, or other non-game-asset
executable shipped alongside the real game data) returns dozens of
short runs that look like noise (`"OGNIKRO"`, `"rorrEO"`, `"YPOCKSID 0"`)
rather than either real words or genuinely random garbage — tempting a
"this file is packed/encrypted, skip it" conclusion.

## What went wrong (and the fix)

Gunship 2000 AGA's bundled `gscopy` (an 8,840-byte, 10-hunk AmigaOS
executable, structurally a disk backup/copy utility) returned a `strings`
dump that was almost entirely short, garbled-looking runs. Reversing the
*whole file's byte stream* and re-running `strings` did **not** help — it
just produced the same garbled runs in a different order, because doing so
also reverses the order of fragments relative to each other, not just each
fragment's own byte order.

The actual scheme: every individual printable-ASCII run (the run boundary
is any non-printable byte, typically the NUL between adjacent string
literals) is stored **byte-reversed on its own** — not a real cipher, no
byte-value transform at all, just local order permutation. This is a
trivial, cheap "defeat casual `strings` scanning" trick that costs the
original developer nothing (probably typed the literal backwards in the
assembler source, or ran it through a one-line reverse macro at build
time) and needs no key/algorithm to undo.

**Fix:** regex-extract each printable run individually (`[\x20-\x7e]{5,}`
or similar) and reverse *only that substring*, one run at a time — don't
reverse the whole file. This immediately recovered clean English:
`"GUNSHIP "`, `"0 DISKCOPY"`, `"SOURCE"`, `"DESTINATION"`, `"(Y/N)?"`,
`"intuition.library"`, `"** Stack Overflow **"`, AmigaDOS device paths
(`"ENV: RAM:"`, `"RAW:0/"`), confirming the file's role (a bundled
"back up your original disks" installer utility) without needing any
disassembly at all.

**Distinguishing this from a real cipher:** the tell is that the garbled
runs are short, numerous, and roughly word-length (5-20 chars) rather than
one long undifferentiated high-entropy blob — see
`high-entropy-trivial-cipher.md` for the sibling trap where a whole file
or record is wrapped in a genuine (if trivial) bit/byte transform. Try the
cheap per-fragment-reversal read first on any small bundled non-game-data
utility before assuming obfuscation means a real cipher.
