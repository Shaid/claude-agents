# Hunting for order-issuing/input UI code: census a suspected state global, don't keyword-search for "mouse"/"click"

**When it bites:** a task or prior session's writeup says "mouse/input/
order-issuing UI code was searched for but not found" — typically after a
whole-binary string/keyword search for terms like `mouse`, `click`,
`button`, or `order` came back empty, or after only forward-tracing from
already-known input-adjacent globals failed to turn anything up.

Compiled game binaries carry no strings naming their own UI intent — a
"currently selected command mode" byte has no `"mouse"` or `"order"` label
anywhere near it, so a keyword search is structurally blind to it no matter
how thorough. But once you have even a weak *hypothesis* for a specific
state-variable global (a byte/word plausible as "current selected icon/
mode/order type" — inferred from context, e.g. sitting near an
already-confirmed player-identity global, or read by code that also reads
screen-coordinate globals), an **exhaustive literal-address census of that
one global** (every `move`/`cmp`/`tst` instruction referencing its address,
found the same way as any other absolute-address xref scan) reliably
surfaces the whole UI chain in one pass: its writer (the icon-click
handler), its readers (target-validation switches gated on its value), and
the code that stages an order once a valid target is hit.

Confirmed on PowerMonger (Amiga): two prior sessions' whole-binary
mouse/click/order keyword and pattern searches found nothing. A third
session instead tested one specific global (`$7DFE8`, hypothesized as
"active order mode" from its proximity to an already-confirmed
per-team-roster-cache global) and traced all 9 of its literal-address
occurrences — immediately surfacing the icon-select handler, a >600-line
target-legality switch keyed on its value, and a per-entity mouse
hit-test/order-staging routine with 9 independent call sites, closing a
negative that had stood across 2 prior sessions.

**Fix:** when "no input/order-issuing code found" persists after a keyword
search, switch techniques rather than searching harder with the same one —
form a hypothesis for the specific state-variable global the UI must be
reading/writing (a mode/selection/order-type byte, often near an
already-confirmed player-identity or team-cache global) and run a literal-
address census on *that address* instead of the vocabulary of the feature.
