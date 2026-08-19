# A flat file that resists every dimension/factorization analysis may be N concatenated copies of a *sibling* file's leading region

**When it bites:** a flat data file with no header, no magic and no
row-boundary markers refuses to yield a grid size or record stride — its
byte count has no clean square factorization, autocorrelation finds nothing
convincing at any plausible width, and the working note has drifted toward
"dimensions could not be determined."

Before any more dimension analysis, spend one loop testing whether the file
is not one structure at all but a **concatenation of a region already
present in its sibling files**:

```python
big = open('mystery.bin','rb').read()
for name in sibling_files:
    d = open(name,'rb').read()
    for k in (len(d), 4096, 2048, 1024, 512, 256):   # try whole file, then prefixes
        i = big.find(d[:k])
        if i >= 0:
            print(name, 'prefix', k, 'found at', i); break
```

A hit at a multiple of `k` is the answer outright, and it hands you the
sub-structure's size for free — which is usually the number that no
factorization of the *whole* file was ever going to reveal.

Confirmed on Phantasie I (Amiga, `nicodemus` project): `maps.int` (9,360
bytes) sat documented for a whole prior pass as "no clean square-grid
factorization, no row-boundary markers found, open/unresolved." It is
**18 × 520 bytes**, and block `k` is byte-identical to the leading 520
bytes of the `k`-th `out*.dat` file — 18 exact substring matches at the
predicted offsets, zero mismatches, the whole file accounted for. The
520-byte sub-block is a 20 × 26 tile grid; 9,360 factors as 20 × 26 × 18,
which no square-grid search would ever surface, and the *only* reason 520
was findable at all is that it appears standalone at offset 0 of eighteen
sibling files sitting in the same directory.

**Two corollaries worth internalising:**

- **Search for sibling prefixes anywhere in the file, not just at offset
  0.** A whole-file equality test would have failed here; the win came from
  `find()` over the whole container.
- **The block order may not follow the filenames.** `maps.int`'s block 16 is
  `out18.dat` and block 17 is `out19.dat` — there is no `out17.dat`, and the
  container is packed by *ordinal over the files that exist*, not by the
  numeric suffix. Derive the block→file mapping from the match offsets
  rather than assuming `block k == file k+1`; a gap in a numeric filename
  series is exactly where that assumption breaks.

This is the same underlying tool as `filename-pairing-unverified.md` (a
systematic prefix byte-diff across the whole corpus, not just the file the
naming convention suggests) reached from a completely different symptom.
That lesson fires when two filenames *look* paired; this one fires when a
file looks structureless.
