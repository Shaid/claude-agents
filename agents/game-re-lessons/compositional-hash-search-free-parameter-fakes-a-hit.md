# A compositional hash search whose unknown prefix is a free parameter cannot confirm the part you care about — and will still report a spectacular hit rate

**When it bites:** you have recovered (or guessed) an engine's name-hash
algorithm, it is linear/compositional
(`hash(A+B) = hash(A) + K^|A| · hash(B)`), and you are about to run a
meet-in-the-middle, "solve for the shared prefix", or two-token
concatenation search to recover asset names. Especially if a first run
comes back with an exciting score like 340 of 439 family members matching.

## What went wrong

FE Warriors: Three Hopes (Switch, `chimera`). With `ktid()` recovered, the
obvious next move was to name the 6,923 G1M model resources. Two searches
were run, both looked reasonable, both were worthless — for the same
reason.

**Search 1 — two-token composition.** Take the 153,696-string executable
pool as both halves; for each target hash `h` and each candidate prefix `A`,
compute the required `hash(B) = (h − hash(A)) · K^−|A|` and look it up.
Every one of the 22 resource-type IDs and 40+ class IDs "matched"
something — `KOD` "=" `'4>H-NZ'` + `'S=)l-['`. 153K × 153K concatenations
against a 2^32 space is ~2.3 × 10^10 candidates for 4 × 10^9 slots: every
target matches many times by arithmetic necessity.

**Search 2 — solve for the shared prefix, which looked like a real hit.**
Take a known same-length name family from the string pool
(`cmn_icon_skill_000` … `cmn_icon_skill_438`, 439 names). If real resources
are named `PREFIX + thatName + SUFFIX`, then for the right shift `L` there
is one constant `C` with `C + K^L · hash(n_i)` landing in the real ID set
for every `i`. Intersect `{f − K^L·hash(n_0)}` with `{f − K^L·hash(n_1)}`
over the 166,571 real IDs, then score each surviving `C` against the rest
of the family. Best result: **340 of 439 at L = 27.** That reads like a
decisive confirmation of a 15-character literal prefix.

It confirms nothing. Expand the algebra:

```
C + K^L·hash("cmn_icon_skill_" + ddd)
  = C + K^L·hash("cmn_icon_skill_") + K^(L+15)·hash(ddd)
  = C'                              + K^(L+15)·hash(ddd)
```

`C` is a free 32-bit unknown, so it absorbs `K^L·hash("cmn_icon_skill_")`
entirely. The test therefore only detects that the ID set contains *some*
439-member family with a 3-digit counter at position `L+15` — which it does,
and which the much cheaper positional-difference scan already told us. The
letters `cmn_icon_skill_` contributed exactly zero evidence. Swap them for
any other 15 characters and the score is identical.

## The general rule

Before trusting any compositional-hash search, write out the algebra and
ask **which symbols the free parameter can absorb**. If the unknown you are
solving for (`C`, the prefix hash, the seed) can absorb the very substring
you believe you are confirming, the search is structurally incapable of
confirming it, no matter how good the score looks.

A 32-bit hash carries 32 bits. Any search that leaves ≥ 4 unconstrained
characters anywhere in the string has ≥ 32 bits of freedom and is
information-theoretically dead: it will always find *a* solution, and that
solution is evidence of nothing. Corollary: only searches where **every
character of the candidate is pinned** count — i.e. hashing a complete
candidate string from a dictionary, not composing one around a hole.

Sanity-check every such search against its chance rate before reading
anything into the hit count: `expected ≈ (#candidates × #targets) / 2^32`.
A whole-corpus sweep on this game (710,924 mined strings × 31 extension
variants against 166,571 IDs) produced ~1,700 hits against a ~1,700
expectation — correctly read as zero signal, where an unnormalised "1,700
matches!" would have read as a breakthrough.

See `game-re-method/name-hash-recovery.md` for what *does* work (harvest
literal anchors from the engine's registration code) and for the cheap
positional-difference scan that bounds the problem before you spend a pass
on it.
