# TypeScript's negative-branch narrowing fails when the discriminant you test is a sibling member's *own* multi-literal type, not a single unique literal

**When it bites:** a discriminated union has one member whose discriminant
is itself a 2+-literal union (e.g. `{ family: 'A' | 'B'; ... } | { family:
'AMN'; ... }`), and code branches with
`if (x.family === 'A' || x.family === 'B') { ... } else { /* expect
AMN here */ }` — the `else` branch fails to narrow to the `AMN` member,
producing `tsc` errors on every field access inside it, even though the
check is logically exhaustive.

## What went wrong

Reunion (Amiga OCS/ECS floppy, `methanoid`)'s block classifier returns a
union of `CompressedBlock` (`family: '2AM' | '1AM'`) and `AmnBlock`
(`family: 'AMN'`). Writing the dispatch as
`if (id.family === '2AM' || id.family === '1AM') { ...compressed path... }
else { ...treat as AmnBlock... }` compiled with 7 errors — inside the
`else` branch, `id` stayed typed as the full union, not narrowed to
`AmnBlock`, so every `id`-specific field read failed.

TypeScript's control-flow analysis narrows a union by literal-value
comparison per branch. Testing equality against **two separate literal
values** (`'2AM'`, `'1AM'`) that happen to be exactly the members of one
type's discriminant union does not get recognized as "this exhausts that
member's type" — the negative branch is only computed as "not `'2AM'` and
not `'1AM'`", which stays a subset of the *original* discriminant type,
not a proof that the *other* union member applies. Rewriting the same
check as `if (id.family !== 'AMN') { ...compressed path... } else {
...AmnBlock... }` — testing against the **other** member's single unique
literal — narrows both branches cleanly, because a single-literal
inequality check is TypeScript's well-supported narrowing shape.

Verified with a minimal reproduction: a two-member union where one member's
discriminant is `'A' | 'B'` and the other's is `'C'`; `x.d === 'A' ||
x.d === 'B'` fails to narrow the `else` branch to the `'C'` member, while
`x.d !== 'C'` narrows both branches correctly.

## Fix

When branching a discriminated union where one member's discriminant is a
multi-literal type, prefer `x.discriminant !== '<the other member's unique
literal>'` over `x.discriminant === '<literal1>' || x.discriminant ===
'<literal2>'` — even when the two forms are logically equivalent, only the
single-literal-inequality form narrows both branches. If the union has more
than two members and no single unique literal is available for the
negative side, narrow explicitly instead (an `as` cast with a comment
citing this limitation, or a nested type guard) rather than fighting the
inference — don't spend time trying to coax the compiler into recognizing
the multi-literal disjunction; it's a known, stable limitation, not a bug
to work around cleverly.
