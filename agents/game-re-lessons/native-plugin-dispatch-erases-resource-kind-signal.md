# A closed native-code dispatch boundary erases every resource-kind signal — classify by content, not by opcode

**When it bites:** a dispatch opcode/command family (all values already
known, not an unrecognized enum member) references a resource by index into
a table, and you're about to assume "the opcode tells you what kind of
resource this is" — especially once you've traced the reference
reimplementation's consumer down to a `DllImport`/P-Invoke/FFI call that
hands the *whole* raw resource (or the whole archive) to closed native code
with no static type/kind field anywhere in the container.

## What went wrong

FF9's battle-SFX archive (dir13, `~/Development/siren`). Opcodes 0x80-0x87
("play-model-on-target") each carry an `arg1` index into a per-chunk
small-file table. It's natural to assume the opcode value picks a resource
*format* (four "versions" of a model, per the reference reimplementation's
own enum names `PLAY_MODEL_ON_TARGET_V1..V4`). Real corpus data across all
33 known eidolon variants (126 real dispatch commands) refutes this: Ifrit's
own summon sequence dispatches the *identical* small-file via five different
opcodes (0x80/0x81/0x82/0x83/0x85), and that file is an `"AKAO"`-magic audio
cue, not geometry at all. The opcode carries zero resource-kind signal;
`arg2` (always `0` across the whole corpus) and the small-file table's own
`flags` field (always `0` for in-archive entries) don't either.

The root cause, found by tracing the reference reimplementation's real
consumer function: it loads the entire archive into a byte buffer and passes
it *unexamined* into a `[DllImport("SomeNativePlugin")]` call — the original
platform's special-effect overlay, compiled to a closed DLL with no source
in the reimplementation's own repo. There is genuinely no code left to read;
the format's semantics live only inside a binary this session has no copy
of. Confirming that dead end concretely (a literal FFI call site passing a
whole raw buffer with zero interpretation) is much stronger evidence of "no
static reader exists" than a failed grep for one.

## The fix

1. When a dispatch opcode's real consumer turns out to be a closed native
   call receiving raw, unexamined bytes, stop trusting the opcode (or any
   sibling flag field) as a format discriminator — the container was never
   designed to let *anything outside that native code* know what kind of
   resource it's holding.
2. Classify every resource a "polymorphic" opcode family actually dispatches
   by its own leading bytes (magic-sniff each unique referenced resource
   across the whole corpus), the same technique used for an unrecognized
   enum value, just applied pre-emptively to *every* value of an already
   fully-enumerated opcode.
3. Once resources are bucketed by content, check each bucket against
   already-solved formats in the *same* corpus before writing a new decoder
   — a bucket may turn out to be byte-identical (past a tiny bucket-specific
   header) to a container the project solved for a completely unrelated
   subsystem, letting an already-verified reader decode it unmodified.
4. Report the split quantitatively (e.g. "108/126 dispatches are opaque
   native blocks; 14 are audio; 4 are a known static format") — this is
   real, checkable progress even when the majority stays unrecoverable, and
   is stronger than a blanket "requires emulation" verdict for the whole
   opcode family.

This is the FFI/closed-binary root cause of the more general
`unknown-opcode-may-select-a-different-resource-kind.md` symptom: that
lesson's case was one *unrecognized* enum value hiding a different kind;
this one is every *recognized* value of a whole opcode family carrying no
kind signal at all, because the real dispatcher never lived in inspectable
code to begin with.
