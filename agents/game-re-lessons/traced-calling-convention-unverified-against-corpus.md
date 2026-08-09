# A byte-exact instruction trace of a calling convention doesn't prove the real corpus exercises it meaningfully

**When it bites:** you've traced a call site's exact argument-passing
convention (which struct byte offsets feed which parameter slots — confirmed
instruction-by-instruction, with a citation for every push) and are about to
document the fields those offsets read as a confirmed part of the game's
data model, without first pulling the real values out of the shipped data
files and checking they make sense.

Confirmed on Vengeance of Excalibur (`middilgard` project, its FSME entity
animation system). `_OpenScene`'s per-roster-entity loop was traced
instruction-by-instruction (`ExcalII.asm:20280-20337`): it reads
`_aForces[i]+34` (a word), `+38` and `+39` (bytes) and pushes them as
`_GetObject`'s resource-id / pose-set / colour-remap-index arguments — an
airtight citation, matching the exact same struct-offset convention Spirit's
own equivalent code uses. Only when the real `EPISODE1.DAT` bytes for a
named entity ("Diego Garcia", located by string search, record start
independently confirmed via the already-known name/position field offsets)
were actually read did it turn up that `+38` and `+39` are **`0` for every
one of the 92 unique entities in the entire corpus**, and `+34`'s values
don't resolve to the confirmed FRML sprite-id range under any additive bias
tried. The instruction trace was not wrong — it's a real, cited fact about
what that code does with those bytes. What was wrong was treating "I traced
the calling convention" as equivalent to "I know what this field means for
real data," without the one cheap check (pull a handful of real records and
look at the actual bytes) that would have caught it immediately.

**The fix:** the moment a calling-convention trace identifies which fields a
function reads, pull the real values for several corpus records *before*
writing the finding up as anything past "this is what the code does with
these offsets." A field that's always zero, or whose values don't fit the
type the code's own downstream logic expects (a resource id outside the
confirmed id range, an enum outside its known cases), is a sign the traced
code path either isn't the one that matters for this data, only applies to
a subset of records you haven't isolated, or the offset means something
else for this record type than the analogous offset does elsewhere (see
`indexed-operand-needs-base-provenance.md` for the same "same-looking
field ≠ same meaning" trap from the opposite direction — resolving an
operand's *base* rather than its declared consumer). Report the
instruction-level trace as confirmed on its own terms; keep the semantic
"and this is what the field holds in practice" claim separate and openly
unconfirmed until the corpus check passes.
