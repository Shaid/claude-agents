# Archive: per-instance-file-set-may-be-duplicate-blobs

Verbatim instance logs behind the condensed lesson.

## 2026-11-04 — valkyrie (VP2 PS2), dedupe-before-voting instance (raw candidate)

# Candidate: keystream-attack votes must be de-duplicated; self-keyed XOR needs a later-word null control
**Kind:** new lesson
**Project / evidence:** valkyrie, battle-logic.md § 14.8, § 15; tools/valkyrieprofile2/verify-pack-contents-not-code.ts
**Overlaps:** none exact (checked verification and compression-crypto index sections by keyword).
**Proposed category + INDEX hook (new lesson only):** compression-crypto — A shared-keystream / known-plaintext attack across many encrypted files shows a surprising vote, or a self-keying XOR (key = first word ^ magic) decrypts "correctly" under a wrong parameter.

## Proposed text
# Dedupe identical members before voting; test a later word for self-keyed ciphers

**When it bites:** You vote for a common keystream pair or header across a population of encrypted files, or a cipher derives its key from word 0 ^ magic.

Two traps. (1) Populations often contain byte-identical duplicates; each duplicate votes for the same candidate, so a count of 11 can be 1 real observation. De-duplicate by a cheap fingerprint (size, first words) before counting, then compare to the chance level. (2) When key = firstWord ^ magic, word 0 equals the magic under ANY multiplier/constant, so a null control that checks the header passes vacuously; check a later word (a member tag at a known offset) under the wrong parameter.

**Check / fix:** after de-dup, require the best vote to clear an empirical null (shuffled or wrong-parameter run); put the null-control probe at a position not determined by the key derivation.

**Canonical example:** VP2 residual 516 TOC entries: raw vote 11 for a shared pair collapsed to 2 (chance) after de-duplicating by (size, c1, c3); the p@Ck verifier's first null control failed (53/53 "matches") until it tested the member tag at +0x80 under multiplier 24385 (0 hits).
