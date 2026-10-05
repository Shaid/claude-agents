# Hash the whole per-instance file set before theorizing about one sample — "19 per-stage files" can be 2 distinct blobs

**When it bites:** a directory holds one file per level/stage/character/
chapter (`S000-Local.bin` ... `S081-Local.bin`), you sample one, and you're
about to write a hypothesis about what *this stage's* copy contains — or
you're about to inherit such a hypothesis from a prior pass that sampled
exactly one file.

Run the census first. It is one command and one second:

```
md5sum dir/*.bin | sort | uniq -c -w 32
```

Confirmed on Fire Emblem Warriors (Switch, `chimera`): `nx/stage/local/`
holds 19 files, all exactly 350,500 bytes — and only **two** distinct
contents (17 stages share one blob byte-for-byte, `S030`/`S032` share
another). A prior pass had sampled `S000` alone and written "plausibly local
prop/decal texture data... not fully surveyed across the corpus," which
framed a shared bundle copied into every stage directory as per-stage
content and kept the item open. The census refuted the entire framing before
a single byte was parsed. The same one-liner separately showed that 5 of the
19 stages ship a byte-identical *navigation grid* — which then explained,
rather than contradicted, why those stages' own marker points failed the
on-grid oracle that the other 14 passed.

Why it's worth doing unprompted rather than when suspicious:

- **Identical file sizes across a per-instance set are a hint, not proof** —
  fixed-capacity tables also have identical sizes and are genuinely
  per-instance. Only content hashing separates the two.
- **A duplicate group is itself evidence.** Which instances share a blob
  usually maps onto a real category the corpus hasn't named yet
  (tutorial/reduced-scope stages, DLC, unused slots), and that grouping is
  often reusable as a control set elsewhere — an oracle that fails on
  exactly the shared-blob members is behaving correctly, not failing.
- **Near-duplicate groups matter too.** Extend the census with a per-file
  byte-difference count against the group representative when the hashes all
  differ; a set that differs in a handful of bytes points straight at the
  per-instance field, and the diff *positions* are the field offsets.

Sibling trap: `all-zero-stub-file-inflates-failure-count.md` (whole-prefix
groups of empty stubs) — same class of "look at the whole set, not one
sample" hygiene, different symptom.

**The same principle also disproves a per-instance-data *hypothesis* for a
sub-region inside otherwise-different files, with just two samples — you
don't need a full corpus and you don't need to fully decode the region
first.** When a candidate "maybe this is the missing per-group/per-instance
table" span is still opaque (no header, no tag, nothing self-describing),
diff its raw leading bytes between two real files chosen to be maximally
different on every OTHER axis you've already confirmed (different content,
different sizes, different counts). Near-identity there is fast, cheap,
decisive evidence the span is a shared boilerplate template (a fixed
GPU-command-buffer or compiled-shader-constant-buffer preamble, an engine-
wide default-state block) rather than per-instance content — confirmed on
NieR (2010, PS3, `flower`): a `KPKy`-container record's still-unidentified
"4th offset slot" (flagged across several passes as "genuinely
unidentified," a real remaining candidate for the game's missing per-
geometry-group material index) turned out byte-for-byte near-identical in
its first ~128 bytes between `CHARA/MML020` (82 geometry groups, region
size 4,880 B) and `CHARA/YONAH010` (6 geometry groups, region size 2,272
B) — two models with nothing else in common — settling in under a minute
what a from-scratch semantic decode would have taken much longer to reach
the same answer on.
