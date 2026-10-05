# A format grammar comment's compact shorthand for a repeat/loop construct describes authored data, not a parser rule

**When it bites:** a chip/protocol/format's own reference documentation
(a source comment, a hardware datasheet excerpt) describes a repeat-loop
or nested-block construct using compact shorthand that concatenates two
grammar productions on one line — e.g. `11---rrr --ffffff nnnnnnnn` to
mean "a repeat-count header, followed by what looks like a rate+count
sub-block" — and you're tempted to write a distinct, special-cased parse
path for "the bytes that follow a repeat/loop header" before checking
whether the real reference implementation's dispatch logic actually does
anything different there.

The shorthand is often just describing the *conventional shape of
well-formed authored data* (what a repeat block is normally followed by in
practice), not a rule the parser itself enforces. If the real state
machine just returns to its ordinary generic-header dispatch after
processing the loop/repeat construct — re-reading whatever byte comes
next through the *same* top-level switch/case used everywhere else — then
there is no special sub-grammar to reverse-engineer separately, and
writing one is wasted (or worse, silently wrong-but-untested) effort.

Confirmed on the NEC uPD7759 ADPCM chip (via MAME's `upd775x_device::
advance_state()`, ported for Golden Axe/`kolbold`): the documented grammar
comment writes the repeat-loop construct as `11---rrr --ffffff nnnnnnnn`,
which reads as if the bytes after a `0xC0`-class repeat header are a
distinct, differently-shaped sub-block. The real state machine's `case
0xC0` handler does nothing of the sort — it sets a repeat counter/offset
and transitions back to the *same* `STATE_BLOCK_HEADER` state that every
other block type returns to, which re-dispatches on the next byte through
the identical generic `header & 0xC0` switch used for silence/nibble/
repeat blocks alike. The "`--ffffff nnnnnnnn`" shorthand is simply
describing that well-formed ROM data conventionally puts an ordinary
rate+count nibble-block right after a repeat header — not a parsing rule
the chip enforces. A port that faithfully mirrors the generic dispatch (no
special-casing) is therefore *correct*, even though it looks like it's
"ignoring" what the grammar comment implies.

**Fix:** when a format/protocol doc's shorthand notation implies a nested
or distinct sub-grammar immediately following some construct, check the
real reference implementation's dispatch/state-transition code for that
construct specifically — does it read the next unit through a *different*
code path, or does it just re-enter the same generic dispatch loop? If the
latter, the shorthand is describing an authoring convention, not an
enforced rule, and a generic-dispatch port is the correct one; don't add
special-case parsing code to match the prose. This is a sibling trap to
`packed-bitfield-prose-order-vs-real-lsb-first-packing.md` (that one is
about a RAM-map's bit-string field *order* being misleading) and to
`websearch-cited-repo-may-not-exist.md`'s broader theme of "verify a
secondary description against the real source it's summarizing" — here
the "secondary description" is the format's own doc comment, and the "real
source" is the reference implementation's actual code, not its prose.
