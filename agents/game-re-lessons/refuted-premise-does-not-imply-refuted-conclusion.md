# A finding that refutes an old premise doesn't automatically refute the old conclusion — re-check the conclusion directly, on corrected grounds

**When it bites:** a fresh finding this session directly contradicts a
stated *reason* an already-"resolved"/"closed" doc row or TODO row gave for
its conclusion (a mechanism you now know exists was previously asserted not
to exist at all) — and you're deciding whether to reopen the row, silently
leave the contradiction sitting there, or move on without touching it.
None of those three is right.

Confirmed on Valkyrie Profile (PSX, `valkyrie` project). A prior round's
"hardened negative" for `vp1psx-slot4807-sacred-phase` (does anything read
the Seal Rating counter to fork the ending beyond two known events?) had
rested part of its case on: "the scene-script bytecode VM ... implements no
`GetFlag`/`SetFlag`-shaped accessor at all" — checked, at the time, only by
enumerating *native*-code `sra`-by-3 bit-index idioms. A later round found
the VM's own memory-operand ALU family *does* have a general flag accessor
(a computed-address bit-store form, used 3,000+ times corpus-wide) — which
falsifies that premise outright. The temptation on finding this is one of
two overreactions: assume the whole ending-fork question must be reopened
(expensive — it was a multi-pass, multi-technique investigation), or note
the contradiction and move on without resolving it (leaves a doc with two
adjacent claims that can't both be true, misleading whoever reads it next).

**The fix is neither: re-run the *specific* check the old conclusion
actually needs, using the corrected mechanism, and let that result decide.**
Here, the old conclusion was "no scripted setter reaches flags `0x448`/
`0x4CE`." The newly-confirmed mechanism is a bytecode opcode family whose
target address is computed from an accumulator register at runtime — but
that accumulator is always built, directly or through a stored local, from
a `PUSHI`/`PUSHI32` literal somewhere in the same script (bytecode has no
other way to introduce a constant). So the corrected, narrow check is: does
the literal `0x448` or `0x4CE` appear as a `PUSHI`/`PUSHI32` operand
*anywhere* in the bytecode corpus, on either disc? Running it took minutes
(one small script over the already-built corpus-walking helpers) and
returned a clean answer: disc 2 zero hits, disc 1 exactly two hits, both
confirmed on inspection to be ordinary actor-placement coordinates (`CALL`
arguments sitting next to `SPAWN`/`PLACE_CONTAINER`), not flag ids. The old
conclusion held — now for the right reason.

**Write the result as a "premise corrected, conclusion unchanged" note in
place, not a reopen.** Add it where the wrong premise was stated (so a
future reader sees the correction right next to the claim it fixes) and, if
the item has a TODO row, append the same one-line correction to that row's
existing text rather than deleting/reopening it — the row's *status* is
still accurate, only its *stated reasoning* needed patching.

**General shape:** a disproved premise is a reason to re-verify the
downstream conclusion on corrected grounds, not a reason to assume the
conclusion is wrong (most conclusions built on partly-wrong reasoning still
happen to be true, especially "we searched everywhere and found nothing"
conclusions where the missed channel independently turns out to be empty
too) or to leave it uncorrected (the next session that reads the old
premise at face value will trust a mechanism-category claim you already
know is false). The re-check should be the narrowest test that actually
exercises the newly-corrected mechanism against the *specific* values the
old conclusion was about — not a full re-run of the original multi-pass
investigation, and not a shape-based literal scan alone if the corrected
mechanism could also be reached by computed/indirect means (here, the
computed/indirect case reduces to a literal scan only because the format's
own constraint — no non-literal way to introduce a bytecode constant —
makes the literal search exhaustive; that constraint needs to be true and
checked, not assumed, before treating a literal census as decisive).
