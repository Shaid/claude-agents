# Two bugs can cancel out — fixing only one regresses the other

**When it bites:** something works despite an obviously-wrong-looking piece of code (an empty lookup table, a suspicious substring check, a hardcoded fallback) and you're about to "clean up" just that one spot.

A wrong platform/format detector and a wrong (or missing) lookup table for
that same platform can silently produce the *same* final answer as the
correct pair would — because the detector's wrong output happens to be a
key that the *other* table still has right. Fixing only the table (or only
the detector) in isolation then breaks what was accidentally working.

Confirmed on middilgard: `detectPlatform()`'s `path.includes('/dos')`
substring check matched `'.../dosega'` too (since `/dosega` starts with the
literal substring `/dos`), misdetecting DOS EGA paths as `dosvga`. Separately,
the type-code lookup table's `dosega` entry was an empty object. Individually
each is a real bug; together they cancelled: the wrong platform label
(`dosvga`) happened to index into a table that already had the *correct*
type codes for that shared reversed-4CC convention, so nothing crashed and
no wrong output was ever observed — until the platform label was fixed
first, which would have then hit the empty table and broken resource-type
lookups for real. Both had to be fixed in the same change. When investigating
"why does X work despite Y looking broken," check whether a second,
independent bug is silently supplying the correct-by-coincidence value that
Y's bug would otherwise have corrupted — and fix the pair atomically.
