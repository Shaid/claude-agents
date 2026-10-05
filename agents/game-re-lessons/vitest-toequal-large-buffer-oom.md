# `toEqual`/`toStrictEqual` on large Buffers/Uint8Arrays OOMs the test worker

**When it bites:** Writing or running a test that does
`expect(bufA).toEqual(bufB)` (or `.toStrictEqual`) on two Buffers or
Uint8Arrays larger than a few MB — most commonly a real, file-based
end-to-end round-trip test comparing actual game archive/container bytes
before and after a write — especially if the test run hangs, takes far
longer than every sibling test, or crashes the whole worker process with
"JavaScript heap out of memory" and no assertion failure to point at.

## What went wrong

A real file-based round-trip test (copy a small ~48 MB game archive,
mutate one record via a writer function, then verify every *other* byte of
the archive is untouched) used
`expect(newData1.subarray(0, originalLen)).toEqual(originalData1)` to
check an append-only invariant on the archive's ~48 MB data blob. The test
run crashed the entire vitest worker process with a V8 "Reached heap limit
... JavaScript heap out of memory" fatal error (heap climbing to ~4 GB
before dying), not a normal assertion failure — no useful stack trace
pointed at the actual line. A first hypothesis (an unrelated full-archive
scan elsewhere in the same test decompressing too many entries) was ruled
out and fixed first, but the crash persisted afterward with the exact same
symptom, which was the tell that the *comparison itself*, not the data
being compared, was the problem.

Vitest/chai's deep-equality machinery (`toEqual`) is built for general
JS values — objects, arrays, nested structures — and tries to build a
structural diff to report on mismatch. Run against a `Uint8Array`/`Buffer`
with tens of millions of elements, this reliably exhausts the worker's
heap even when the two buffers are in fact byte-identical (i.e. even on
the success path — it doesn't need a real mismatch to blow up).

## Fix

Never compare large binary buffers with `toEqual`/`toStrictEqual`. Use
`Buffer.compare(a, b) === 0` or `a.equals(b)` (both native, O(n) byte
comparison with no diff construction) and assert on the resulting
boolean/number instead:

```ts
expect(newData1.subarray(0, originalLen).equals(originalData1)).toBe(true);
```

This applies to any seer-framework project's tests, not just one game —
any test that does a genuine end-to-end round trip against real game
archive/container data (not a small synthetic fixture) should reach for
`.equals()`/`Buffer.compare` from the start once a compared buffer is more
than a few MB, rather than discovering the OOM the hard way. Small
(sub-MB) synthetic fixtures are fine with `toEqual` — this is specifically
a large-real-data problem.
