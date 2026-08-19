# On a block-padded platform, a byte histogram or tail hexdump describes the padding, not the file

**When it bites:** you're characterizing an unidentified small file from a
first look — a byte-frequency histogram, a `xxd` of the head and tail, "what
does this mostly consist of" — and the answer comes back as "almost entirely
one repeated byte" or "mostly filler with a bit of structure at the front",
on a platform where files are padded out to a block boundary (Amiga/Atari ST
128-byte disk blocks, CD/DVD 2,048-byte sectors, 512-byte FAT sectors,
console archive alignment). Also bites when a whole-corpus classifier buckets
such files by dominant byte value.

The file's *stored* length is not the length the game reads. Loaders very
often carry the real payload length as an immediate at the call site
(`move.w #$33E,-(a7)` / a size field in a TOC) and read only that many bytes;
everything past it is mastering padding that the engine never touches. A
histogram computed over the stored length is therefore weighted by however
much padding the file happened to need, which is an artifact of the file's
size modulo the block size — nothing to do with its content. A short file
that needs a lot of padding can look like it *is* padding.

Confirmed on Phantasie III (Amiga, `nicodemus` project). `D/M0` (896 bytes on
disk) had been written up in the project's own format doc as "almost entirely
a single repeated character (`0x3E`/`'>'`) — reads as either a border/divider
graphic asset or a degenerate/mostly-empty table", and its sibling `D/M1` as
"dense binary, purpose undetermined". Both classifications came from looking
at the stored bytes as a whole. Tracing the loader showed the engine reads
**830** of `M0`'s 896 bytes and **659** of `M1`'s 768 — the `0x3E` run is
128-byte-boundary padding *past* the read length, the same padding convention
every `.cmp`/`.csh`/`.set` file in that game uses. Within the real read
lengths both files are three-track music: exactly three `0xFF` track
separators at 298/623/829 in `M0` (the last landing on the final byte of the
declared read) and 252/454/658 in `M1`. A "border graphic" was a music
stream, and the only thing standing between the two readings was 66 bytes of
disk filler.

**What to do instead.** Before characterizing an unidentified file's content:

- **Get the loader's declared read length first**, and compute every
  statistic over `data[:readLength]` only. On 68k this is usually a literal
  immediate pushed at the `Read`/`fread` call site — cheap to find once you
  have the filename string's xref.
- If you can't find the loader yet, **check whether the file size is an exact
  multiple of a plausible block size** (128 / 512 / 2,048). If it is, treat
  the trailing run of any single repeated byte as presumed padding and strip
  it before histogramming — a one-line change that costs nothing if you're
  wrong.
- Trailing padding is **not necessarily zero**. It is "whatever byte the
  mastering tool had handy", and a non-zero filler (`0x3E`, `0x1A`, `0xF9`,
  the last content byte repeated) is exactly what makes it read as content.
  Don't gate the strip on the filler being `0x00`.

## The filler byte may *measure* the content — test before dismissing it

The bullet above says the filler is "whatever byte the mastering tool had
handy." Often true — but check first, because when it isn't, the padding
hands you every file's exact payload length for free, with no loader trace
at all.

On Phantasie III (Amiga, `nicodemus` project) the rule is
**`fillerByte == contentLength mod 128`**, verified across **58 of 58**
files whose size is a multiple of 128, zero deviations. (The only
exclusions are the three files that aren't 128-multiples and therefore carry
no block padding.) That one script independently reproduced every read
length the project had already code-traced — `m0` → 830, `m1` → 659,
`s1`-`s20` → 1,050, `phantasy.set` → 35,785 (exactly its documented
`35 + 3750 + 32000` layout) — and handed over two lengths nobody had traced:
81 and 496, which immediately factored as 9×9 and 31×16 and then matched the
loader's own `#$51` / `#$1F0` read immediates byte-for-byte. Two files whose
grid dimensions had defeated five separate approaches fell out of the
padding.

**How to test it, in one pass over the corpus.** For every file whose size
is a multiple of the block size: strip the trailing run of the final byte,
call what's left `content`, and check whether the stripped byte equals
`len(content) mod blockSize` (also try `blockSize - (len(content) mod
blockSize)`, i.e. the pad *count*, and the low byte of `len(content)`). A
whole-corpus hit rate of 100% with zero deviations is the signal; anything
partial means the filler really is arbitrary and you've lost a minute.

Why it happens: a mastering routine that computes `pad = 128 - (len % 128)`
has the length residue sitting in a register anyway, and `memset`ing with it
is one instruction cheaper than loading a constant. It is worth checking on
any block-padded platform, not just this one — and it is strongest exactly
when you most need it, on small unidentified files where the loader hasn't
been found yet.

## The same residual can look like a leading header instead of trailing padding

The rule above assumes you already suspect the file's *tail* is padding.
But for a fixed-stride record array, a size that doesn't divide evenly by
the stride (`fileSize = recordCount × stride + residual`) is genuinely
ambiguous from arithmetic alone: the residual could be a leading header
*before* record 0, or trailing padding *after* the last record — and only
one of those readings is right.

Confirmed on Phantasie III (Amiga) `monsinfo.dat`: 3,072 bytes, and 80
monster records at a 38-byte stride (confirmed independently via the
overworld encounter engine's own `index × 38` addressing arithmetic)
leaves a 32-byte residual. Reading records starting at offset 32 (residual
as a leading header) produced *plausible-looking* output — legible
monster names — but each one carried a single stray leading garbage byte
(`"MSniverling"` instead of `"Sniverling"`), which should have been the
tell that the record boundary was off by one byte's worth of drift, not
just "some header exists." Re-deriving from `recordCount × stride ==
fileSize` with **no header** (records starting at offset 0) produced
clean 13-byte name fields with zero stray bytes, and the 32 leftover
bytes landed at the *end* as pure `0x60`-byte filler — exactly the
already-documented 128-byte-boundary padding convention (`3,072 = 24 ×
128`), and `0x60 == 3,040 mod 128`, the same `fillerByte == contentLength
mod blockSize` rule confirmed above on unrelated files.

**Fix:** when a fixed-stride record array's size leaves a residual, don't
default to "leading header" — test both placements against real record
content. A correct reading should never need "there's one extra garbage
byte at a predictable position in every record" to explain itself; if it
does, the boundary is off by that many bytes, and the residual almost
certainly belongs at the end (check it against the block-padding rule
above) rather than the start.

Sibling lessons: `all-zero-stub-file-inflates-failure-count.md` and
`partial-zero-fill-dropout-vs-corrupt-decode.md` cover zero-fill that makes a
file look *broken*; this is the opposite — non-zero fill that makes a file
look like *different content than it is*. `patterned-fill-defeats-naive-entropy-scan.md`
covers synthetic fill that passes as real data in an unused disk region.
