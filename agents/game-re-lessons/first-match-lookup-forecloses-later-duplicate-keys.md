# A first-match-wins lookup over duplicate keys structurally forecloses later duplicates — proof from the algorithm beats any caller census

**When it bites:** investigating "what selects/triggers resource entry `X`"
where `X` is reached (if at all) only through a keyed lookup function — a
by-id search, a name resolver, a directory scan — and the *same key value*
appears more than once in the table `X` belongs to. A caller/literal-argument
census of the lookup function has already been run (maybe more than once,
across widening scopes) and keeps coming back with "no site passes this
exact key" or "many sites pass it, from many callers" — tempting either a
"needs live capture to see which caller wins at runtime" conclusion, or
another escalation.

Confirmed on Valkyrie Profile (PSX, `valkyrie`): a battle-animation
directory entry (`TOC 1489` entry 48, `animId=0`) was the sole
data-authored path onto another entry (`animId 16`) via an already-solved
chain mechanism, but nothing explained how entry 48 itself ever got
selected. Two rounds of investigation censused every call site of the two
functions that can select a directory entry by `animId` — literal
arguments, register-sourced arguments, a widened corpus-wide `jal`-target
scan covering essentially the whole executable (both discs) — and found
`animId=0` was *never* passed as a literal anywhere, though the functions do
have register-sourced call sites whose runtime value could in principle be
anything.

**The decisive move was disassembling the lookup functions' own search
loops, not just their call sites.** Both turned out to be a plain forward
linear scan that initializes an index counter to 0 and `beq`-breaks the
first time `directory[index].key == query` — a textbook "first match wins"
search. The target directory has **five** entries sharing the queried key
(`animId=0`) at indices 34, 36, 43, 47, and 48. Given the confirmed
algorithm, *any* call requesting that key — literal, register-sourced, from
any caller, under any runtime condition — resolves to index 34, the
earliest match. Entry 48 is not merely un-triggered by anything found so
far; it is **provably incapable of ever being the result**, independent of
which of the many call sites (or a caller not yet found) supplies the
query. The caller census was never going to answer the question, because
the question wasn't "which caller reaches it" — it was "can the lookup
produce this index at all," and the lookup's own bytes already say no.

**General shape:** when a corpus-wide caller/argument census for a keyed
lookup stalls or produces an unhelpfully large/ambiguous result set, check
whether the *key space itself* has duplicates (grep the confirmed
container/table for repeated key values, not just confirm the target's own
key) and disassemble the lookup's own loop for its duplicate-resolution
rule (first match / last match / highest-priority match / undefined-latest-
write). If the target entry is anything other than the position the rule
would select, this closes the question outright — no further caller
tracing, no live capture, and (usually) no escalation is warranted, since
the proof holds for every possible runtime value the still-untraced callers
could ever supply. This is a stronger and cheaper evidence class than an
exhaustive-but-inherently-incomplete caller census, because it reasons from
the algorithm's own confirmed structure rather than from an absence of
found callers — the same distinction `negative-from-addressing-root-not-
shapes.md` draws between a real negative and a search that merely came up
empty, but inverted: here the *positive* proof is what closes the question,
not another round of searching.

This differs from `writer-invariant-impossible-value-means-wrong-object-
identity.md` (a confirmed *writer* proves a stored *value* impossible,
redirecting to the referring pointer's identity) — this lesson is about a
confirmed *lookup/search* proving a *selection outcome* impossible,
closing a "what triggers this" investigation rather than redirecting it.
