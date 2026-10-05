# A boot-time clear loop touching two adjacent pools in lockstep can clear past either pool's real usable boundary — trust the reader's own index bound, not the clear loop's iteration count

**When it bites:** decoding a fixed-size-record "pool"/array from a raw
memory dump, where the only evidence for the pool's total size is a
boot-time initialization/clear loop's iteration count — especially when
that same loop advances two (or more) separate base pointers together
(one iteration = N bytes cleared at each of several independent
pointers), and a naive read using that iteration count produces
high-index "records" that look garbage-shaped (extreme/out-of-range field
values) compared to the low-index records.

## What went wrong

Golden Axe (Sega System 16B, `kolbold`): two work-RAM sprite-template
pools (`$F400`, `$F800`) are cleared by one shared loop —
`clr.l (a0)+; clr.l 4(a0); clr.l (a1)+; clr.l 4(a1); lea 0x10(a0),a0; lea
0x10(a1),a1; dbra` — running 80 iterations. Naively concluding "each pool
is therefore 80 records (0x500 bytes)" and decoding a captured snapshot
with that boundary produced 13 "records" in the `$F800` pool, several with
implausible field values (`top=255 bot=254`, `pitch=-126`, `X=511` — all
extreme/clamped-looking). These were not real sprite data: they were
ordinary unrelated work-RAM bytes living *past* the pool's real boundary,
picked up only because the over-generous 80-iteration read window
extended into them.

The clear loop's 80-iteration count is a **boot-time convenience/safety
margin**, not the pool's contractual size — it simply clears more bytes
than either pool actually addresses, because clearing a little extra is
harmless and cheaper to code than two separately-sized loops. The
authoritative size lives in the **reader/consumer code's own index
bound**: the per-frame display-list-builder routine that indexes into
these same pools uses `move.w #$3f,d1` (a 64-iteration `dbra` bound,
i.e. valid slot indices `0`-`63`) — giving the real per-pool size (64
records = `0x400` bytes), confirmed by re-decoding with that boundary and
getting a clean "0 nonzero records" result for `$F800` (consistent with
its writer never having fired in that run) instead of spurious garbage.

## The fix

For any pooled/array structure whose size is inferred from an
initialization or clear routine rather than a documented header field,
cross-check against the **actual consumer's** loop bound (a `dbra`/`cmp`
constant, an index-mask, a table-lookup range) before trusting the
init routine's own iteration count — especially when the init routine
visibly serves more than one structure at once. The two numbers agreeing
is confirmation; disagreeing means the init routine is the loose one, not
the reader.

This is a sibling case to `declared-range-field-loose-for-bulk-records.md`
(a stored field can be a loose bound) and
`fixed-stride-record-count-unverified.md` (don't size an array from
`(size-header)/stride` alone) — here the loose bound comes from a
*shared, multi-target* init loop rather than a per-record header field or
a raw byte-count division.
