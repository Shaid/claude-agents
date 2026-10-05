# Recovering an engine's name hash — and knowing when it can't name anything

Modern engines routinely address every asset, every object property and
every resource *type* by a 32-bit hash of a string, shipping no name table
at all. Koei Tecmo's KTGL "KTID" is the worked example here (FE Warriors:
Three Hopes, Switch, `chimera`), but the shape is generic: Unreal's FName
pools, Wwise short IDs, CRI cue IDs, Havok class IDs, most in-house
`.rdb`/TOC designs.

This file is the full chain: get anchors, derive the algorithm, then bound
honestly what the algorithm can and cannot buy you. Steps 1–2 are cheap and
almost always work. Step 4 is the part people skip, and it decides whether
the rest of the pass is worth running.

## 1. The anchor corpus is in the engine's own registration code

You need `(plaintext, hash)` pairs. Do **not** start by guessing candidate
strings and hashing them — you have no algorithm yet, so you cannot test
anything. Start by finding pairs the binary already contains.

The reliable source is the engine's **property / descriptor / reflection
registration code**, which necessarily holds both halves adjacent: the
name string (for tooling, logging, editor round-trips) and the
precomputed hash constant (for the runtime lookup). No symbol table is
needed and the binary can be fully stripped.

Worked example, Three Hopes' `main` NSO (ARM64). A large jump-table
dispatch at `main+0x6A572C` has one case per registered property, each
exactly four instructions:

```
adrp x13, PAGE_A ; ldr d1, [x13, #OFF_A]   ; 8-byte {u32 (type<<24)|count, u32 nameKtid}
adrp x13, PAGE_B ; add x13, x13, #OFF_B    ; pointer to the property-name string
b    #0x6a572c                             ; shared tail
```

Scanning `.text` for that idiom (resolve the ADRP page, add the offset,
read the constant cell and the C string) produced **8,037 literal
(name, hash) cells**, of which 2,756 distinct names survived a
well-formedness filter on the descriptor word. That was the whole ballgame.

How to find the idiom without knowing it in advance:

- Pick a string you *believe* is a hashed name — an obvious property or
  type name in the string pool (`"…ObjectNameHash"`, `"…ResourceHash"`,
  `"Position"`, `"Scale"`). Resolve its ADRP+ADD xref.
- Read ±40 instructions around that xref. If you land in a per-case run of
  identical short sequences (a jump-table body), you have found the table;
  the constant loaded alongside the string in each case is the hash.
- Then generalise the sequence into a scanner and harvest the whole table.

A **negative worth acting on**: if the string has *no* code xref at all, it
lives in a pointer pool referenced some other way; fall back to hashing the
whole string pool once you have a candidate algorithm (step 2) and matching
against real IDs.

## 2. Derive the algorithm algebraically — don't sweep known hashes

A 15-algorithm × 4-variant sweep (CRC32 and inverted CRC32, FNV-1/1a with
both seeds, Jenkins one-at-a-time, djb2 add and xor, sdbm, ELF, murmur3,
`h*K+c` for K in {5,7,17,31,33,37,101,127,131,137,139,251,257,1313,65599,
0x1000193}, each × raw/lowercase/NUL-terminated) scored **0 / 2,756**.
Sweeps only find hashes someone else already named. Two structural tests
found this one in minutes:

**Test A — is it affine over GF(2)?** Every CRC, LFSR and table-driven
polynomial hash is. Find same-length quadruples `a, b, c, d` with
`a ^ b ^ c ^ d == 0` bytewise, and check `h(a) ^ h(b) ^ h(c) ^ h(d) == 0`.
Three Hopes: **0 / 401** quadruples held, which eliminated the entire
CRC/LFSR family in one shot — including all the custom-polynomial variants
a sweep can never enumerate.

**Test B — is it integer-linear, and with what per-position weights?**
Collect every pair of same-length anchors differing in **exactly one**
character position `i`. Each gives `Δh ≡ Δchar · W[i,len] (mod 2^32)`;
solve for `W` (when `Δchar` is odd it is invertible mod 2^32 directly,
otherwise divide out the common power of two and solve mod the reduced
modulus). Then look at the resulting table:

- If `W` depends only on `i` and **not** on the string length, the hash is
  a plain positional sum with no length term and no finalizer.
- The weights themselves usually reveal the constant: Three Hopes gave
  `W[0]=31`, `W[1]=961`, `W[4]=0x01B4D89F`, `W[6]=0x67E12CDF` — i.e.
  `31^(i+1) mod 2^32`, so `ktid(s) = Σ s[i]·31^(i+1)`.

Finally subtract the modelled sum from every anchor and histogram the
residual **per length**. A residual of exactly 0 at every length (2,756/2,756
here) proves there is no length seed, no terminator contribution and no
final mix. A constant-per-length residual would mean `init · 31^(len+1)`;
a constant residual overall would mean a plain additive seed.

**Then confirm it in the disassembly.** Search `.text` for the multiply
idiom (`*31` compiles to `lsl w,w,#5; sub w,w,worig`) inside a loop that
also has a byte load and a backward branch. Three Hopes had two instances,
`main+0x75D574` and `main+0x76DC08`:

```
mov   w7, wzr                ; h   = 0
mov   w21, #1                ; pow = 1
loop: ldrsb w26, [x22]       ; c = (SIGNED char)*p
      cbz   w26, done
      lsl   w27, w21, #5
      sub   w21, w27, w21    ; pow *= 31   (before the accumulate)
      madd  w7, w21, w26, w7 ; h += pow * c
      ...
      b.ne  loop
```

Reading the real loop is what caught the two details a purely algebraic fit
could never see with ASCII-only anchors: the power advances *before* the
accumulate (hence `31^(i+1)`, not `31^i`), and the byte load is **`ldrsb`**
— characters are **signed**, so any byte ≥ 0x80 contributes negatively.

## 3. Exploit linearity — for search, and be honest about its cost

A positional-sum hash is compositional:

```
hash(A + B) = hash(A) + K^|A| · hash(B)   (mod 2^32)
```

That is genuinely useful — it makes prefix/suffix candidate testing O(1)
per candidate instead of O(len) — and it is what makes step 4's structural
scan possible. It is also the reason blind inversion fails; see
`compositional-hash-search-free-parameter-fakes-a-hit.md` before building
any meet-in-the-middle or "solve for the shared prefix" search on top of it.

## 4. Bound the naming problem *before* spending a pass on it

Two measurements decide whether recovering the hash will actually name
anything. Do both first.

**(a) How long are the real names? Measure it from the ID set alone, with
no plaintext.** For each character position `i` and each small delta `d`
(1, 2, 10 — digit steps), count how many IDs `h` in the target set also
have `h + d·K^(i+1)` in the set. Two names differing only by a digit at
position `i` produce exactly that difference, so a count far above the
chance rate `n²/2^32` localises the varying digit fields — and therefore
the name length.

Three Hopes' 6,923 G1M model IDs: chance expectation **0.011** pairs;
observed **182 at position 15, 178 at 26, 148 at 27, 129 at 30**. Model
names carry decimal counters out to position 30, i.e. they are roughly
16–36 characters long. That single cheap scan is what proved brute-force
inversion hopeless before any brute force was attempted.

**(b) Does a plaintext source for those names exist at all?** Hash every
printable string you can reach — the executable's pool, and strings mined
from samples of *every* resource type in the shipped data — against the
full ID set, with a handful of extension/case decorations. Compare the hit
count against the chance rate `(#candidates × #targets) / 2^32`. Three
Hopes: 710,924 distinct data strings × 31 extensions produced ~1,700 hits
against a ~1,700 chance expectation, i.e. **nothing**.

If (a) says names are long and (b) says no plaintext survives, the answer is
a *reasoned negative*, not an unfinished search: a 32-bit hash of a 30-char
name has ~10^47 preimages of the right length, and no amount of cleverness
recovers information that was never shipped. Write it up that way and move
on — but note that the algorithm still pays off, because any external
filename list that surfaces later (a community dump, a sibling title that
ships plaintext) can be verified against the whole corpus in one pass.

## What the hash *did* buy on Three Hopes, for calibration

Even with model/animation names unrecoverable, the hash converted a bag of
numbers into a readable graph:

- **21 real resource names** — every string in `main` hashed against all
  166,571 RDB `fileId`s. All 21 were the engine's hardcoded bootstrap
  object databases (`Field_Common.character.level.kidssingletondb`, …),
  which also pinned the naming convention: a resource is named by a **bare
  filename with extension, no directory path**.
- **3,187 / 3,354 (95.0%)** of the object database's distinct property-name
  hashes resolved to plaintext, covering 10.5 M property occurrences —
  which is what made the container worth decoding at all.
- A **188-edge resource dependency graph**, every edge type-homogeneous
  (`KTGLModelDataResourceHash` → G1M in 3,654/3,654, `KTGLRigBinResourceHash`
  → RIGB in 2,094/2,094, …). That homogeneity is itself a strong
  verification of the record layout: a wrong layout cannot produce it.
- Independent confirmation on shipped data from an unrelated resource type:
  an `SRGC` audio-graph resource is **self-describing** — 10 of its 14
  embedded strings hash to a `u32` present in the same file.

Names of *classes* and *types*, by contrast, resolved 0/22 and 0/866: those
strings are not in the binary either. Same rule as everywhere — the hash
names exactly the strings that survived somewhere, and nothing else.
