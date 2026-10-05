# An operand-token family sharing one on-disk width can still mix signed and unsigned members

**When it bites:** decoding a custom VM/bytecode's operand-token grammar
(a small set of tagged tokens like "immediate byte," "direct-memory byte
offset," "indexed-array byte") where several distinct token kinds share the
exact same on-disk shape (e.g. all a raw `u8` or `u16` right after the tag
byte). It's tempting to write one shared decode helper keyed only by width
("`b` = read one byte, `w` = read one word") and apply it uniformly — but
some of those tokens are literal VALUES (which want sign-extension) while
structurally identical-shaped tokens for a different role are ADDRESS/OFFSET
operands (which must stay unsigned). Treating them uniformly by width alone
silently corrupts every value-typed token that happens to be >= 0x80 (byte)
or >= 0x8000 (word).

## What happened

Porting a Silmarils "ALIS" VM's operand-token decoder (Ishar, Amiga AGA):
`oimmb`/`oimmw` ("immediate byte/word" — a literal constant baked into the
bytecode) and `odirb`/`omainb`/etc. ("direct byte offset into a data
region") are all encoded identically on disk (tag byte + a raw byte or word
value) and were initially decoded through one shared helper that always read
them unsigned. This broke a ring/lateral clamp loop's termination condition:
a `cadd oimmb(0xff) -> adirb(...)` instruction meant "add -1" (a literal
decrement), but reading `0xff` as unsigned 255 made the loop count up
instead of down, and the interpreter ran until it hit its step-count safety
cap with zero useful output. The fix was a one-line special case in the
token reader (`name === 'oimmb' ? signedRead8() : unsignedRead8()`), but
finding it required recognizing that "immediate" and "direct offset" are
different *semantic roles*, not just different tag bytes with the same
physical encoding.

**Bonus finding once fixed:** the same bug had also corrupted an earlier
*manual* hand-analysis of a nearby constant table (a set of per-ring
elevation values) that had been read unsigned and dismissed as implausible
("large positive numbers, doesn't converge toward the horizon as expected").
Re-reading them signed gave small negative values converging monotonically
toward zero — exactly the expected perspective behavior. A wrong-signedness
assumption can retroactively explain an earlier "doesn't make sense"
finding, not just break new decoding.

**Generalizes to:** any bytecode/VM/protocol operand grammar with more than
one token kind at the same width — game scripting VMs, packet formats,
config-file binary encodings. Don't assume uniform signedness from shared
physical width; check each token's semantic ROLE (literal value vs.
address/index/offset) individually, ideally against the reference
implementation's own read function (`(s8)` cast vs. plain `u8` read) rather
than guessing from the tag name alone.
