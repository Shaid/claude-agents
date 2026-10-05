# A record appended past a silent loader clamp "works" (file parses, game boots) but is never installed — and a corrected cap finding must be propagated to every staged artifact built on the old "appendable" claim

**When it bites:** a doc, TODO row, or open-thread bullet says a table
"already proved appendable via the live `[N]` row" / "grows via data
alone", and the evidence is that the game booted with the longer file. Or:
a cap has since been confirmed (a `cmp #CAP ; csel` clamp, a fixed-trip
copy loop, a `min(count, CAP)`), a correction block was written — and a
staged mod/PoC/patch built *after* that correction still appends at index
`CAP` or beyond because nobody re-derived the artifact from the corrected
claim.

## What happened

Fire Emblem: Three Houses (`chimera`): `PersonData` grew 1059 -> 1201
records across official updates with no executable patch, a machine-code
census found "zero hardcoded checks against the base count", and the docs
concluded the table was growable via data alone; a live mod then appended
record index 1201 and it was written up as "appended and live", cited in
three places. A later escalation found the loader clamps section 0 at
exactly 1201 (`cmp w9,#1201 ; mov w10,#1201 ; csel w9,w9,w10,lt` — the
same idiom every table uses, `CAP == shipped count`), and a correction
block was added. But the "genuinely new character" proof-of-concept staged
*after* that correction appended record **1202**, and an open-thread bullet
still said "PersonData already proved appendable via the live `[1201]`
row". Neither row is ever installed in the entry array: the clamp is a
`csel`, not a fault, so a too-long file loads, boots, and plays exactly
like the pristine one. Boot success was zero evidence of reachability.

## Two rules

1. **"Appendable" means "installed and reachable", not "parses".** The
   test for a data-only table extension is a consumer observing the new
   record (a name resolving, a model loading, a debug read of the entry
   array), never "the game didn't crash". If the loader's clamp shape is
   known, check the appended index against it before staging anything.
   Silent-clamp idioms to look for: `cmp/csel` (ARM64), `min` via
   `cmp/b.lt/mov` (any ISA), fixed-trip-count copy loops, a `count >= CAP ?
   CAP : count` before a `memcpy`.
2. **A cap correction is not done until every artifact built on the old
   claim is re-derived.** After writing the correction block, grep the docs
   *and* the staged mods/PoCs/patch recipes for the old index (`[1201]`,
   `1202`, "appendable", "growable") and fix or flag each one — a stale
   artifact is the same trap as stale tracker prose
   (`tracker-prose-is-not-evidence.md`), one layer further from the
   evidence and therefore harder to notice. The usual fix is reuse, not
   append: tables capped at their shipped count almost always carry
   byte-identical filler rows inside the cap (113 of 1201 here), and a
   record re-parked on one of those passes every downstream filter with no
   code patch at all.
