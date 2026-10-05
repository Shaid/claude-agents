# A dominant variant's field-offset convention isn't automatically valid for every value of its own discriminant

**When it bites:** A format has a small leading discriminant field (a
`type`/`count`/`version` byte or word) that changes the rest of the
header's byte layout, and a specific field-offset convention (a pointer
table, a sub-header position) has been confirmed — often by a specialist
escalation or a prior session — for only the *dominant* value(s) of that
discriminant. A fresh implementation reads the field unconditionally for
every record, without checking the discriminant first. The rare-variant
records don't crash or throw: they produce a *plausible-looking* wrong
value (a small nonzero pointer, an in-range-ish count) that survives loose
structural checks (nonzero, doesn't overflow the buffer) and only gets
caught by a stronger corpus-wide self-consistency oracle — a redundant
field the format stores twice, a chain-closure walk, or a downstream
render.

## What happened

The 3rd Birthday (PSP)'s `pack` container has a `count` field at offset
0x04 that takes 7 distinct values across the real 436-entry corpus
(`{2, 4, 7, 8, 11, 12, 34}`). A `re-codebreaker` escalation confirmed that
for `count ∈ {8, 12}` (96.6% of the corpus, both sharing `f0c === 128`) a
section-pointer table sits at `f0c + 0x20..0x3c`, with the geometry
region's own pointer at `f0c + 0x34`. The doc was explicit that the other
15 `count` values (3.4%) have "a visibly different header layout past the
first 16 bytes" and that this pointer convention does not apply there.

The first pass of a fresh, independent re-implementation (written from the
doc's prose, not copied from the escalation's scripts — see
`verify-escalation-artifacts-not-just-claims.md`) read `f0c + 0x34`
unconditionally for every `pack`, regardless of `count`. For the rare-shape
packs this landed on unrelated header bytes that happened to form a small
nonzero "pointer," which resolved to an in-bounds file offset and parsed a
plausible-looking `blockCount`. It only surfaced as wrong because the
format's *own* redundant self-check (each geometry block independently
stores its `weightCount`/`strideHalfwords`, which must agree with the
vertex-type-derived layout) failed for exactly those packs — a whole-corpus
regression test caught 10 packs with `selfCheckOk === false`, and every one
of them had `count ∈ {4, 11}` (the rare shapes), confirming the root cause
in one query.

## The fix

Gate the convention explicitly on the discriminant, and make the gate a
named, exported, testable function rather than an inline `if`:

```ts
export function hasConfirmedGeometryLayout(f0c: number): boolean {
  return f0c === 128; // only count ∈ {8, 12}; see doc's header-shape table
}

export function parsePackGeometry(buf: Buffer, f0c: number): PackGeometry | null {
  if (!hasConfirmedGeometryLayout(f0c)) return null;
  // ... f0c + 0x34 read only happens past this guard
}
```

Returning `null` (no geometry) for the ungated shapes is honest — it
matches the doc's own documented open item (a rare-header-shape geometry
pointer that hasn't been located) rather than fabricating a decode.

## Generalizable takeaway

Before porting *any* field-offset convention that a doc/escalation
confirmed only for a subset of a format's discriminant-value space,
grep the doc for whether that scoping was actually stated (it usually is,
explicitly, right next to the confirmed table) — then encode the scope as
a guard, not as an implicit assumption in the reader's head. A structural
check that only verifies "nonzero and in-bounds" is too weak to catch this
class of bug; the format's own redundant self-describing fields (when it
has any — see `redundant-transmission-needs-correlation-not-diff.md` and
the "two independently-located tables agreeing" oracle in the main
`game-re.md` Method §4) are what actually caught it here, via a
whole-corpus test, not a hand-picked sample.

**The guard doesn't automatically cover a second function added later.** On
this exact format, a follow-up session (2026-09-13) added a second reader
of the same `f0c`-relative section-pointer table
(`parsePackTextureTable()`, alongside the already-guarded
`parsePackGeometry()`) and it reintroduced the identical gap — no
`hasConfirmedGeometryLayout(f0c)` check, so the 14 rare-header packs'
unrelated bytes were misread as a texture-table start/end, producing
descriptor entries with `pixelFormat` values up to 4,294,967,295. Fixing
one function that reads a discriminant-gated convention does not fix every
function that reads it: grep the module for every reader of the raw
offset (here, every `f0c + 0x2?` access) and confirm each one goes through
the shared guard. A fresh whole-corpus regression test caught it, not
inspection of already-shipped assets — the production pipeline's own
downstream `pixelFormat === T4 || T8` filter had already silently
protected what actually got shipped, so the bug was real but latent until
a new caller exercised the ungated path.
