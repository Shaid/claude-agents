# A control code with a parameter suffix consumes trailing bytes — a decoder that doesn't know this still looks "mostly fine"

**When it bites:** a text/control-code table has entries whose name carries
a parameter marker (`{wait:b}`, `{key:b}`, `{cmd:w}` — a `:b`/`:w`-style
suffix meaning "this code takes a following 1-byte or 2-byte argument"),
and a from-scratch decoder is about to treat every code as parameter-free
(just look up the code, emit its string, move to the next byte).

A control code with a declared parameter consumes N more raw bytes
immediately after itself — those bytes are the argument, not the start of
the next character. A decoder that doesn't know this reprocesses the
parameter byte(s) as a fresh code lookup instead, which usually fails (the
parameter is an arbitrary numeric value, not a valid character code) and
renders as a spurious `{hex}` escape token sitting right after the control
code's own placeholder. This is easy to miss on a casual read: the output
is still mostly legible prose with the escape token embedded inline (e.g.
`{key:b}{18}{key}` instead of the correct `{key:24}{key}`) — it doesn't
look broken, it looks like one extra stray token. **The only way this
reliably surfaces is checking a decode's unmapped-byte-escape rate all the
way down to exactly zero across the full corpus**, not eyeballing sample
output or accepting a "mostly clean, a few odd `{xx}` tokens" result as
good enough.

Confirmed on FFVI-J (SNES, `ceres` project): the community
`everything8215/ff6` disassembly's own reference decoder
(`tools/romtools/text_codec.py::TextCodec.decode()`) revealed that codes
like `{wait:b}`/`{tab:b}`/`{key:b}` consume 1 following byte as a decimal
parameter substituted into the placeholder. A byte-by-byte JP dialogue
decoder written without this rule produced exactly the described artifact
— a handful of stray `{18}`-shaped tokens (14 occurrences out of 76,324
characters, ~0.02%) sitting right after `{key:b}` in real dialogue lines.
Small enough to be easy to write off as noise, but it wasn't: implementing
the parameter-consumption rule (regex-match the code's value for a
`:b`/`:w` suffix, consume 1/2 more bytes, substitute the decimal value)
took the unmapped-escape count to exactly zero. **The same bug was already
present, undetected, in this project's own previously-"confirmed" US FFVI
dialogue decoder** (`text.ts`'s `decodeDialogText`, shipped in an earlier
session) — it has the identical gap for the identical codes, only
surfaced by contrast once the JP decoder's stricter zero-escape check was
run. A decoder can pass an earlier, less rigorous verification pass (e.g.
"looks like real dialogue," "matches a few known lines") and still carry
this class of bug indefinitely if the verification never drives the
escape rate to a hard zero across the *entire* corpus, not a sample.

**The fix generalizes:** when building a decode table from a reference
project's *transcribed* character/control-code values (not just a rip-list
of addresses), check whether any value uses a suffix convention signaling
"this code takes an argument" — and if the reference project ships its own
decoder source (see `romhacking-community-tools-first.md`'s section on
codec source), read that decode loop's parameter-handling branch directly
rather than assuming every code is parameter-free. Verify by driving the
unmapped-byte-escape count to exactly zero across the full corpus, not a
sample — a near-zero rate is not the same evidence as an exactly-zero one,
and the gap between them is precisely where this class of bug hides.
