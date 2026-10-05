# A linear disassembly silently loses real call sites in code+data blobs — scan every offset independently instead

**When it bites:** you're writing a standalone disassembler (capstone or
similar) directly against a raw code+data binary — not going through IRA/
radare2's own analysis — to build a caller/xref list for a specific address,
the blob is known or suspected to mix inline data tables into the instruction
stream (jump tables, `DC.W`/`DC.L` constant tables, the "inline parameter
block" calling convention some compilers emit), and a linear walk (decode one
instruction, advance by its size, repeat) reports zero or suspiciously few
xrefs to a target you have independent reason to believe is called.

A linear disassembly desyncs the instant it walks into a data table: it
decodes the data bytes as if they were instructions, and every subsequent
instruction boundary in that region is wrong until the stream happens to
resynchronize by chance — silently, with no error, and often for hundreds of
bytes. Any real `BSR`/`JSR`/`LEA` instruction whose bytes fall inside that
misaligned stretch is never seen as itself; it gets consumed as an operand or
prefix of some other misdecoded "instruction." Cross-referencing a target
address against a single linear pass therefore reliably *under-reports*
callers, and the miss is invisible because the pass completes without error.

**Fix:** don't trust one linear pass for an xref search. Attempt an
independent single-instruction decode at **every 2-byte-aligned offset**
(word-aligned, per 68k's own alignment rule — adjust stride for other
ISAs) across the search range, keep only the decodes whose mnemonic is a
control-flow/address-taking form (`bsr`/`jsr`/`jmp`/`pea`/`lea`/`movea`/
`move.l` for absolute or PC-relative addressing), and check each one's
resolved operand against the target list. This is O(range/2) independent
attempts rather than one continuous walk, so a misaligned decode at one
offset can never suppress a real instruction two bytes later — cheap (tens
of thousands of attempts is milliseconds) and catches every call site
regardless of what data lies between them. Confirmed on Black Crypt Amiga's
decompressed `bcdft` S_1 image (166,676 B of code interleaved with
blit-descriptor tables): a linear disassembly of the same range found **zero**
xrefs to 19 known target addresses; the per-offset brute-force scan found
real, verifiable `BSR`/`LEA` call sites to 15 of them immediately, which then
traced the 3D-viewport wall-compositing render loop end to end.

**Alternative fix, same failure mode:** rather than hand-rolling the
per-offset brute-force scan above, radare2's own `aaa` (full auto-analysis)
does real recursive-descent disassembly — it follows actual branch/call
targets instead of walking bytes linearly, so it doesn't desync through
inline data tables the way a from-scratch linear capstone sweep does.
Confirmed on D&D: Tower of Doom (ddtod, CPS2): a linear capstone sweep from
the reset vector, grepping for operand references to a known RAM address
range, found **zero** hits end to end (silently desynced after the first
conditional branch); `r2 -a m68k -e asm.cpu=68000 -c "aaa"` on the same
4MB decrypted opcode image found 2469 real functions, and exporting their
disassembly (`pdf @@f`) and grepping *that* text found the real code
immediately — including functions r2's own linear view alone would have
missed. This is a good default first move for a code+data-mixed 68k blob
before writing a bespoke offset-scanner: cheap (single command), and when
it *also* comes up empty for a target you have independent reason to
believe is called (e.g. real, well-formed data reachable only through it),
that's the point to fall back to the per-offset brute-force technique
above, since `aaa`'s recursive descent has its own blind spot — it won't
find code reachable only via an indirect jump/call it can't statically
resolve (confirmed on the same binary: two functions with real, well-formed
literal data had zero `axt`-reported callers and zero hits from an
exhaustive `bsr`/`jsr`-displacement scan across the whole 4MB image,
meaning they're reached — if at all — by a mechanism neither approach
covers, e.g. `jsr An` through a runtime-computed register or an
unresolved jump table).

**Related but distinct failure, fixed-width ISAs:** on a fixed-width ISA
(AArch64, ARM, MIPS, PowerPC) inline data can't misalign subsequent decodes
the way it can on 68k, but Capstone's `disasm()` has a different
byte-width-independent trap with the identical symptom (a whole-segment
xref/immediate census returns 0 or too-few hits) — see
`capstone-arm64-disasm-silently-stops-at-undecodable-word.md`.

**Companion gotcha, same script:** capstone's M68K operand-string formatter
uses a bare `$` prefix for hex immediates and addresses (`bsr.w $2030e`), not
`0x`. An xref scanner whose regex looks for `0x[0-9a-f]+` in `op_str` will
silently return zero hits for every target — indistinguishable from "really
has no xrefs" unless you first confirm the scanner works on one address you
already know is referenced. Match `\$([0-9a-fA-F]+)` instead (or normalize
both prefixes if the script also handles other architectures' disassemblers).
