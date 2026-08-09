# A record's start offset can be arithmetically invisible to a "content lands on stride*k+N" check

**When it bites:** a fixed-stride record array's start offset was
"confirmed" only by checking that variable-length content (a printable
name string, any field whose position you located by searching for its
*value*, not by tracing a write) lands on `base + stride*k + N` for a
whole-number `k` — and a leading region exists before the array that could
alternatively be a separate, fixed-size header rather than "record 0's own
early fields."

## Why the check is blind, not just weak

This is a sharper trap than "the count/stride wasn't independently
verified" (`fixed-stride-record-count-unverified.md`) or "a preceding ramp
masked a one-record start error" (`adjacent-ramp-table-masks-off-by-one-
record-start.md`). Those are about picking the *wrong* start position that
still happens to look plausible. This one is a case where **two
structurally different models predict the exact same absolute byte
position for the content you're checking, for every record index
simultaneously** — because addition is commutative. If a hypothesis says
"records start at `base+0`, with the checked field at record-relative
offset `N`," the field's absolute position for record `k` is `base +
stride*k + N`. If the correct model is instead "a `N`-byte header precedes
the array, then records start at `base+N`, with the checked field at
record-relative offset `0`," the field's absolute position is `base + N +
stride*k + 0`. These are the identical expression. A check that only asks
"does field X land on `stride*k + N`" cannot distinguish "header of size N,
field at record offset 0" from "no header, field at record offset N" —
not as a near-miss, but as a mathematical identity, for any `k`.

## Confirmed case

Wings (Amiga, Cinemaware 1990)'s `pilot.dat` roster was documented, across
two sessions, as "41 x 88-byte slots starting at body+0" with the pilot
name at slot-relative `+46`, established solely by a blind regex scan
finding every printable-ASCII run in the decrypted body and confirming
each landed on `slot*88+46` for an integer slot — 0 deviations, which read
as decisive. It was wrong: the real layout is a 46-byte **file header**
(not "slot 0"), then 41 name-FIRST records (`char name[32]` at record
offset **0**), each 88 bytes, starting at `body+46`. Both models predict
the exact same name position (`88k+46`) for every `k`, so the "name lands
on the expected offset" check could never have caught the error — and
didn't, across two separate sessions' worth of otherwise-careful analysis.
The practical damage: every "confirmed" stat-field offset documented
relative to the wrong record start (e.g. `+78`) was really 46 bytes into
the *following* record's own early fields, and two sessions' literal-
displacement greps for those (wrong) offsets predictably found nothing —
see `record-stride-guess-vs-recount-fields.md` for the general shape of
that downstream symptom. A `re-codebreaker` escalation broke it by finding
a `strcpy` instruction whose **destination address** was the record
pointer — tracing what a WRITE instruction targets, not what a scan lands
on — which pins the record's phase unambiguously.

## Fix

A "does variable content land on `stride*k + N`" check only proves the
record's **stride**; it cannot prove where within that stride the record
actually *starts* whenever a same-sized header could be swapped for an
in-record offset without changing any predicted content position. Get an
independent anchor for the record boundary itself before trusting field
offsets built on top of it: the destination of a `strcpy`/`memcpy`/field-
initialization **write** instruction that targets "the start of record k"
is decisive (a write's destination is a real address, not a coincidence of
arithmetic); a bulk-copy's source/destination pointer arithmetic
(`base + index*stride`, confirmed against a *disassembled* instruction,
not just inferred) is nearly as good. If the only evidence for a record's
start is "content of a known shape happens to land at the right relative
offset," treat the record's start as unconfirmed even at 0 deviations —
the check may be structurally incapable of ever failing regardless of
which of two boundary models is correct.
