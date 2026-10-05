# A pointer-array's structural stride signature is not enough on its own — score candidate runs on what the pointers point *at*

**When it bites:** locating a table in an executable image by a purely
*structural* signature — a fixed record stride where one field advances by a
constant per entry and another stays constant — and taking the longest
matching run as the answer. Especially when you're about to reuse that
locator on a sibling title/build to see whether it has the same table.

## What happened

Fire Emblem Warriors (Switch, `chimera`). Its global resource-path registry
is a 24-byte-stride array of `{u64 pathPtr, u64 handleSlotPtr, u64 flags}`
where `handleSlotPtr` increments by exactly 8 every entry and `flags` is
`0x403` throughout. That signature is genuinely excellent — it finds the
real 13,133-entry array with no hardcoded address, filename or magic
constant, which is exactly what you want in a committed extractor.

Then the same locator was pointed at the two sibling Koei Tecmo Switch
titles' `main`. It confidently returned a **17,322-entry** array for Three
Hopes and a **946-entry** one for Three Houses — same stride, same 8-byte
progression, same `0x403` flags. Both were garbage: the pointers resolved to
short fragments like `"default"`, `"d"`, `"n"`, `"b"`. Those games have no
path registry at all (they address assets numerically inside
`LINKDATA`/`DATA0`), so the correct answer was `null`.

An "is it printable ASCII?" guard did **not** catch this — short symbol
fragments are perfectly good ASCII, so the run passed a 90%-ASCII threshold
easily. Had the sibling check not been run, a future pass would have been
handed a confident, fully-populated, entirely wrong name table.

## Why the structural signature over-fires

Any array of `{something, sequentially-allocated-pointer, constant-tag}` has
this shape: vtable-ish dispatch tables, per-object slot arrays, interned
symbol tables, allocator freelist descriptors. A big optimized binary has
many of them, and the *longest* one is not necessarily yours. Stride
regularity is a necessary condition, not a sufficient one.

## The fix

Two changes, both cheap:

1. **Add a content-plausibility test on the dereferenced payload**, not just
   on the container shape. Here: require ≥50% of a run's `pathPtr`s to
   resolve to something path-shaped (contains `/`, ends in a dotted
   extension). Generalize as "does the pointed-at data look like the *kind*
   of thing this table is supposed to hold" — a path, a magic word, a
   plausible struct.
2. **Rank candidates by that score, not by length.** Collect every run over
   the minimum size, score each, keep the best; don't lock onto the longest
   run and then test only it. Cap the scoring at the few longest candidates
   so a pathological image can't make the scan quadratic.

With both in place the locator returns the registry for the game that has
one and `null` for the two that don't — which is the behaviour that makes it
safe to hand to a future pass.

## The cheapest version of the same mistake: "the address is in range"

The same rule bites at much smaller scale, and there the content test is
nearly free. Valkyrie Profile (PSX, `valkyrie`): each behaviour module's entry
prologue forms its dispatch table's address with a `lui`+`addiu` pair, so the
locator paired those by register and accepted the first result that **landed
inside the module with room for the table**. In-range is a bounds check, not a
content check — several modules have other `lui`+`addiu` pairs in the same
prologue, and the locator happily returned "tables" whose first handler
address was the integer `24`.

The fix cost three lines: every slot must be `0` (an unused entry) or a
word-aligned address inside the module, and at least one must be live. That
alone removed 6 false positives from a 655-module corpus. Generalize it as:
whenever a locator's acceptance test is "the computed address is inside the
region", ask what the pointed-at *bytes* must look like if the hypothesis is
true, and test that too — a handler address, a magic word, an in-range index.
Bounds checks pass on coincidence; content checks mostly don't.

## The general rule

A locator you intend to *reuse* must be tested on a target that should
return nothing. A scan validated only against the one binary you already
know contains the thing has never demonstrated it can say "no". Finding a
true negative to test against is usually as easy as pointing it at a sibling
title — and it is the difference between a reusable tool and a confident
liar.
