# A single corrupt field inside an otherwise-valid record calls for sanitizing that field, not tightening the record's accept/reject gate

**When it bites:** a decoded fixed-stride record run shows a small,
non-zero fraction of records with one specific field reading as garbage
(non-finite, absurdly out of range, or a recurring nonsense bit pattern)
while every other field in those same records — including whatever
criteria currently decides "is this a real record" — stays perfectly
valid; and the instinct is to add a stricter per-field validity check to
the accept/reject gate to filter them out.

Confirmed on Chaos Legion (PS2, `flower` project): 631 of 44,983 decoded
mesh vertices (1.40%) carried a non-finite/astronomically large UV value
(the same recurring garbage bit pattern, `0x70000000`-class exponent) while
their *position* fields — the existing accept/reject criteria — stayed
completely valid, so the vertex (and every neighboring one) was already
being accepted correctly. Before fixing anything, a candidate stricter
gate (reject the whole record unless a second field, attribute-A's known-
constant sibling values, also matched exactly) was A/B-tested against the
existing logic across the whole corpus: it reduced total decoded vertices
from 44,983 to 23,509 — cutting more than *half* the corpus's real,
already-verified position data to filter out 631 bad UV values, because
that "known-constant" field turned out not to be universally constant
after all (a documented, unverified assumption from an earlier pass). The
correct fix was narrower: sanitize only the corrupt field itself (clamp
the bad UV to a neutral value) and leave the record's accept/reject logic
completely untouched — verified corpus-wide that this changes zero
vertex counts (byte-identical totals before/after) while eliminating every
non-finite/out-of-range value from the affected field.

**Fix:** when tightening a record's validity gate is on the table,
A/B-test the candidate gate against the current one across the *whole*
corpus and check which direction it moves record counts — a gate that
should only be removing garbage but instead removes a large fraction of
records is a sign the new criterion isn't as universal as assumed, not
that the gate is working. If the corruption is confined to one field and
every other field (including whatever already reliably distinguishes real
records from junk) is fine, sanitize that one field in place instead of
rejecting or truncating the record — this preserves every already-verified
value the existing criteria correctly accepted, and a corpus-wide "before
vs. after" count comparison is the cheap way to prove the fix didn't
regress anything.
