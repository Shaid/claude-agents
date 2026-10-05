# A `do{}while(i<=N)` loop that runs N+1 times can be intentional, matching an already-documented placeholder-record convention elsewhere in the same format family

**When it bites:** a disassembled decode loop's bound looks like a classic
off-by-one bug — e.g. `do { ...; i++; } while (i <= count)`, which executes
`count + 1` times, not `count` times — and the instinct (yours or a tracing
agent's own explicit flag) is to "correct" it to `count` iterations when
porting the algorithm, or to treat the extra iteration as a decode error to
be trimmed off.

**Confirmed** on Parasite Eve (PSX, `~/Development/parasite`): a
`ghidra-disasm` trace of the animation-clip decoder (`FUN_80039d24`/
`FUN_80039ed4`) found the per-bone rotation-track loop written as
`do {...} while (iVar7 <= clip[1])`, where `clip[1]` is the clip header's
own `boneCountByte` field — executing `boneCountByte + 1` times. The
tracing agent flagged this explicitly as worth double-checking rather than
trusting blindly. It turned out to be genuine, intentional data layout: the
model-format's own bone table (a *different* structure, already documented
independently in this same project) has a confirmed convention where
`h[1]`'s low byte equals `boneCount + 1` — one extra, always-inert
placeholder bone record padding out every model's bone array. The
animation-clip format's per-bone rotation-track count matches this
convention exactly (`boneCountByte + 1` rotation tracks per frame, one per
real bone plus the placeholder), and porting the loop literally (not
"fixing" it to `boneCountByte` iterations) was required for the decode to
byte-exactly consume every clip's declared resource size across the whole
9,042-clip corpus with 0 remainder.

**What actually resolves it:** don't decide from the loop shape alone in
either direction (neither "this is obviously a bug, normalize it" nor
"this is obviously fine, ignore it"). Check whether a *sibling* structure
in the same format family already has a confirmed, independently-derived
convention that predicts the same "+1" — here, the model header's own
placeholder-bone-record fact, found in an unrelated earlier investigation,
directly predicted and explained the clip loop's bound before any byte
was decoded under it. When such a sibling convention exists and matches,
port the loop literally. When no such sibling convention exists, the
byte-exact whole-corpus consumption check (does decoding with N+1
iterations consume the resource's own declared size exactly, corpus-wide,
with 0 remainder?) is the deciding oracle — not a hand-wavy "looks like an
off-by-one" judgment call, and not blind trust in a fast trace's literal
transcription either.
