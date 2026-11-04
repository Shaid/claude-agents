# A self-keyed cipher's null control must probe a word the key derivation does not already fix

**When it bites:** you have recovered (or guessed) a cipher whose key is
derived from the data itself — `key = word0 ^ MAGIC`, an LCG seeded from the
header, a CRC of the first block — and you are writing the null control that
is supposed to prove the parameters (multiplier, increment, magic) are the
real ones. Especially when that control reports a clean 53/53 "header
matches" and you are about to call the cipher confirmed.

Self-keying makes the header a fixed point. If the key is defined as
`word0 ^ MAGIC`, then decrypting word 0 with that key returns `MAGIC`
**for any multiplier, any increment, any stream parameter whatsoever** —
the derivation guarantees it algebraically. A control that checks the magic
therefore passes vacuously; it is testing arithmetic, not your hypothesis.
This is the free-parameter failure of
`compositional-hash-search-free-parameter-fakes-a-hit.md` in cipher clothing:
the unknown you solved for absorbs the exact symbol you think you are
confirming.

**Check / fix:** write the derivation out algebraically and ask which words
of the plaintext it determines. Place the null-control probe at a position
it does **not** determine — a member tag, a count, or a known string at a
fixed offset deeper into the stream — and require that probe to fail under a
deliberately wrong parameter. A null control that cannot fail is not a
control. Run it both ways: right parameter → hits, wrong parameter → zero.

The same reasoning applies to every "verify the key schedule" check on a
self-keying stream: the first N bytes the derivation touches are off-limits
as evidence.

**Canonical example:** Valkyrie Profile 2 (PS2, `valkyrie`). The `p@Ck`
container's key is `firstWord ^ magic`. The verifier's original null control
checked the header magic and reported 53/53 "matches" under every candidate
LCG multiplier — vacuous. Re-pointing the probe at the member tag at
`+0x80` separated them immediately: the real multiplier hit, multiplier
24385 produced 0 hits. Write-up: `docs/valkyrieprofile2/ps2/battle-logic.md`
§ 15, `tools/valkyrieprofile2/verify-pack-contents-not-code.ts`.

Companion hygiene for the same kind of attack: de-duplicate the population
before counting votes — see
`per-instance-file-set-may-be-duplicate-blobs.md`.

**History:** 1 recorded instance (`valkyrie`).
