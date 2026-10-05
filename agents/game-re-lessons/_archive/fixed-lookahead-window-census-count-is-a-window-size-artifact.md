# A multi-instruction dataflow-chain census's total is an artifact of its lookahead window, not a property of the code, unless the window is liveness-based

**When it bites:** re-deriving (or first building) a whole-file census for
a multi-instruction register-chain idiom — e.g. "shift by a stride, add a
base register, then load a field" (`sll ×N ; addu ; load`), or a simpler
"reload a pointer, then access field X/Y/Z off it" idiom — matched by
"look ahead K instructions for the next stage" where K is a fixed constant
chosen by feel rather than derived from register liveness. A doc citing a
specific total ("N sites, M of one kind") from such a census, especially
one sourced from a single one-time probe with no committed, re-runnable
script, is a candidate for this trap. **Also bites when a liveness-
respecting re-scan reproduces the doc's exact headline COUNT** — a stable
count across methodologies is not itself corroboration; diff the actual
SET of matched sites, not just its size, since two errors (one false
inclusion, one false exclusion) can cancel numerically while both being
real. And when the matched "access" at each site could be either a load
or a store (the idiom's own description doesn't distinguish them) — a
census that doesn't tag each hit read-vs-write can silently sum unlike
things into one figure that looks like a clean, single-typed total. Also
bites in a quieter shape: a windowed census's committed script can have
individual checks that are still literally, permanently true (they only
ever claimed the narrow in-window result) while its own header comment or
check LABEL claims completeness — such a script never fails, so nothing
ever flags the staleness once a wider, unbounded rescan (elsewhere in the
doc tree, possibly in a sibling file) supersedes the completeness claim;
see the third instance below.

## What happened

Confirmed on Valkyrie Profile (PSX, `valkyrie`), round 214 (the 15th rigor
spot-audit). item-skill-system.md's item-stat-table indexing correction (a
`re-codebreaker` escalation) stated: "a whole-overlay census of the
`(sll ×32 ; addu <base> ; load)` idiom finds 11 sites; the 8 based on `s3`
... 0 deviations (the other 3 are an unrelated `+0xc84` field on different
base registers)." A later rigor audit had only spot-checked 3 of the 8
`s3`-based addresses individually — the "11 sites / 3 unrelated" totals
themselves were never independently re-derived.

A from-scratch re-scan, using a plain fixed lookahead window (look ahead
K instructions after the SLL for a matching ADDU, then K more after the
ADDU for a matching load) to sanity-check the methodology, produced
**wildly different totals depending on K**: window=1 gave 8 hits, window=2
gave 9, window=3 gave 10, window=4 jumped to 19, window=5 and 6 both gave
20. No fixed window reproduced "11" at all. The count is not measuring a
fact about the binary — it's measuring an artifact of an arbitrary
constant nobody had written down or justified.

The only principled fix was to drop the fixed window entirely and instead
track the shifted-index register's own **liveness**: follow it forward
with no length bound at all, and abandon the candidate the instant some
*other* instruction writes to that same register before the expected next
stage appears (an ordinary "does this write clobber the value I'm
tracking" check — see `dataflow-chase-must-track-destination-not-mere-
reference.md` for the general write-target-vs-reference distinction this
reduces to for a single hop). That liveness-respecting scan found exactly
9 real chains — not 11 — with the same 8 `s3`-based hits (individually
confirmed byte-exact, on both discs this time) plus exactly 1 non-`s3`
hit, not 3.

**The second-order damage is worse than a wrong count.** The "3 unrelated
sites at `+0xc84`" claim wasn't just over-counted — it named the WRONG
field entirely. Manually disassembling the loose-window scan's extra
"hits" showed they were a completely different, unrelated 4-instruction
`sll+addu+addu+load` 2D-indexing idiom that only coincidentally shares its
first two instructions' shape with the real 3-instruction idiom; the
fixed window was wide enough to let an unrelated *second* `addu`
re-clobber the register before the load, and too naive to notice. The
one REAL non-`s3` hit read a genuinely different, previously-undocumented
field (a byte the doc's loose scan never singled out at all) feeding a
real, previously-unknown second writer of an already-documented shared
struct field. A census that "finds 0 deviations" under the wrong
methodology can silently misattribute a real hit to the wrong field
family while looking clean — the 0-deviations framing is exactly what
makes nobody go re-check it.

## A second instance: same headline count, wrong membership, reads mixed with writes

Confirmed on the same project (`valkyrie`), round 216 (the 17th rigor
spot-audit). `battle-logic.md` §83.2 claimed a windowed scan ("`lw
$r,0x26f4($r2)` ... followed within 30 instructions by a `0x6($r)` or
`0x8($r)` access") found "all six real reads of `instance+0x6`/`+0x8`
... every one of them falls inside this one function's own body ... 16
total register uses across those 6 reload sites." A liveness-respecting
re-scan over the WHOLE cached region (not just the one function the doc
assumed contained everything) found **the same count — 6 read-bearing
sites** — which superficially looks like a clean re-confirmation. It
wasn't:

- One of the doc's six cited sites (`0x8009d76c`) is not a read at all —
  it's a STORE (the routine's own ease-out write to that field). The
  windowed scan's "access" match had no load/store discriminator, so it
  silently counted this write as one of the "six reads," and folded a
  second, entirely un-cited write-only site (a "phase 2" analog 80+ bytes
  further on, whose reload instruction the doc's own instruction listing
  had simply omitted from its transcription) into the same "16 total
  register uses" figure — mixing reads and writes into one number with no
  way to tell which contributed what.
- Removing that miscounted write left five real reads. The site that
  filled the sixth slot back up to six was a **completely different,
  previously-uncensused read** — outside the one function the doc claimed
  contained "every one of them" — that the original windowed scan had
  missed entirely. Two independent errors (one false inclusion, one false
  exclusion) happened to cancel in total count while leaving the doc's
  claimed *membership* and its completeness claim ("every one of them
  falls inside this function") both wrong.

The generalizable point: **a re-scan reproducing the exact same number is
weaker evidence than it looks.** Always diff the matched-address SET
against the doc's cited addresses, not just compare cardinalities — and
when an idiom's "access" could be a load or a store, tag every hit with
which one it is before aggregating a total.

## The fix

- Treat any doc-cited total for a multi-instruction (2+ hop) pattern
  census as suspect until you know **how the census decided a candidate
  chain was complete** — a fixed lookahead window, or genuine liveness
  tracking. If the methodology isn't stated (common for a one-time
  `re-codebreaker`/probe-script result that was never committed), assume
  fixed-window until proven otherwise.
- Before trusting (or re-deriving) such a count, sweep several window
  sizes and check whether the total is stable. If it changes at all
  across small window changes, the number in the doc is not a fact about
  the code — rebuild the census as a liveness-respecting forward walk
  (abandon on redefinition, not on a step counter) and treat THAT as the
  real total.
- When a loose census's "other/unrelated" bucket shrinks under the
  principled re-scan, don't just update the count — re-examine what that
  bucket's remaining member(s) actually are. A miscounted census doesn't
  just miscount; it can misclassify a real, differently-shaped hit as
  belonging to a superficially similar but unrelated family, hiding a
  genuine finding behind a wrong label.
- A re-scan that reproduces the doc's cited total is not, by itself,
  confirmation. Diff the matched-address SET against the doc's own cited
  addresses; a stable count can hide one false inclusion and one false
  exclusion cancelling each other, plus a false "every one falls inside
  function X" completeness claim that only breaks once you check set
  membership rather than size.
- If the idiom's "access" covers both loads and stores, classify every
  hit as one or the other before aggregating any total. A figure like
  "N total register uses" that doesn't state whether it's reads, writes,
  or both is a candidate for silently mixing unlike things together.

## A third instance: the check never failed, only its comment lied

Confirmed on the same project, round 218 (the 19th rigor spot-audit).
`battle-logic.md` § 94.4 (2026-09-24) claimed a fixed-15-instruction-window
scan of "`lw $reg,0x50($base)` then same-register `+0xf` read" found "the
COMPLETE set... not a sample" (3 sites, all testing one bit-mask). A
liveness-respecting rescan (no fixed window, follow the register until
redefined or `jr $ra`) found 5 sites, not 3 — 2 more, at distance 30 and 63
instructions, testing a SECOND mask the doc had called "still
unconfirmed." This part is the same pattern as the first two instances
above. What's new: **the original committed script's individual checks
were never wrong and never failed** — `hits.length === 3` and `hits.every
(h => h.maskTested === 0x40)` are both still literally true today, because
they only ever tested the narrow in-window claim, not the doc's broader
"complete set" prose wrapped around them. A different session, working in
a SIBLING doc file, had already found and fixed the real gap one day
later (with its own separate script) and even left a `> Superseded` block
— but that correction never propagated back to the section and script
that originated the claim, and because the original script kept exiting 0
with `ALL CHECKS PASSED`, this campaign's own "does every committed script
still pass" discipline had nothing to catch. A `git log -S` on the exact
phrase, or a fresh liveness-respecting rescan, are what actually surfaces
this class of staleness — a clean test run does not.

**The fix, generalized:** when auditing a windowed census's own committed
script, don't just re-run it and check for PASS. Read its check LABELS
and header comment for completeness language ("the complete set," "not a
sample," "exhaustive") separately from what the check body actually
tests, and treat any mismatch between the two as the real finding — fix
by relabelling the check to state its true (narrower) scope, not by
changing the assertion, since the assertion was never wrong.
