# C unsigned-32-bit wraparound vs JS doubles — a ported key/cipher derivation returns a wrong key silently

**When it bites:** porting a C (or C-derived) hash/key-derivation/checksum
routine to JavaScript/TypeScript for a production pipeline, where the
reference source performs its arithmetic in unsigned 32-bit (or smaller)
integers that wrap at every assignment — and the JS port uses ordinary
`number` (IEEE double) for the running value.

`unsigned int` arithmetic in C wraps mod 2^32 at *every* step. A JS port
that lets the running value grow as a double stays exact only below 2^53;
beyond that the low bits are silently lost (doubles keep the top 53 bits),
so the final `& 0xffffffff` / `>>> 0` produces garbage — while the port
still *runs* and produces a plausible-looking key. A Python reference is
safe by accident: arbitrary-precision ints are congruent mod 2^32, so
computing without masking and reducing only at the end gives the same
result as C's wrapped arithmetic (addition/multiplication mod 2^32 respect
congruence) — which makes "match the Python probe" an unreliable port
check for JS.

CRI ROFS CVM scramble key (`calcKeyFromString`, Odin Sphere / Grim
Grimoire): the C reference (roxfan's `cvm_tool`) wraps `sum` mod 2^32 at
each of the passphrase-loop steps; the first TS port used doubles and
derived `413b413b413b413b` instead of the correct `45e3655352c34c15` — a
wrong-but-deterministic key that only surfaced as a failing known-answer
test (the per-sector decryptor itself was already verified correct, so the
failure isolated to the key function).

Fix: compute with `BigInt` and reduce mod 2^32 at every step
(`% (1n << 32n)`), or mask per-assignment with `>>> 0` ensuring every
intermediate stays below 2^53 (products of two ≤2^32 values need BigInt —
masking the operands first isn't enough). Always keep a known-answer test
from an independently-verified source (the reference tool's printed key,
or the first decrypted magic bytes), not just "matches my Python port".
