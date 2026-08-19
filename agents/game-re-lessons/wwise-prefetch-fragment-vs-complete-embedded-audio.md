# A Wwise bank's embedded DIDX entry can be a truncated "prefetch" fragment, not real complete audio — check its own RIFF-declared size against the directory

**When it bites:** decoding an Audiokinetic Wwise SoundBank (`.bnk`, or the
banks embedded inside an `AKPK`/`.pck` package's `banks` table) that
contains a `DIDX`+`DATA` chunk pair (an embedded-audio index), and either
(a) some embedded entries fail to open in vgmstream/any Wwise-RIFF decoder
while others succeed with no obvious pattern, or (b) a decoded "audio" clip
plays a fraction of a second then cuts off/errors despite the bank
declaring a larger size for it.

## What went wrong / real finding

Confirmed on NieR Replicant ver.1.22474487139 (PC)'s `data/sound/*.pck`
`AKPK` packages. A `DIDX` entry declares `(id, relOffset, size)` pointing
into the bank's own `DATA` chunk; the bytes at that offset begin with a
real `RIFF`/`WAVE` header. Naively assuming every `DIDX` entry is a
complete, standalone, decodable WWRIFF stream is wrong for a real subset:
this is the standard Wwise **"streamed with prefetch"** authoring pattern
— a short in-bank buffer holds only the *first few KB* of a sound so
playback can start instantly, while the real, complete audio streams in
separately from a sibling `.wem`/streamed-package file under the
**identical numeric Wwise object id**. Feeding vgmstream-cli (or any
Wwise-RIFF decoder) the prefetch fragment's raw bytes fails to open it
outright, since the fragment's own embedded `RIFF` header still declares
the *full* stream's real length — a length the truncated fragment's actual
byte count doesn't satisfy.

The discriminator is fully local and self-contained, no cross-file lookup
needed: **does the entry's own embedded `RIFF` chunk's declared content
length (`readUInt32LE(offset+4) + 8`) equal the directory's own declared
`size` for that entry?** If yes, it's a genuine complete embedded stream.
If the `RIFF`-declared length is *larger* than the directory says, it's a
prefetch fragment — the complete audio exists elsewhere (in this corpus:
under the identical id in a separate `sounds`-table-only `.pck`/`.wem`
pool). This local check was independently cross-verified against an
explicit id-based lookup against the sibling streamed-audio files and
agreed 100% (305/305 real prefetch entries in this corpus's small banks,
zero false positives/negatives) — but the local check alone is sufficient
and doesn't require the sibling corpus to be present or even known about.

In the same corpus, two large banks' `DIDX` entries were **100% complete**
by this check (5,413 + 5,378 real entries, `RIFF`-declared length exactly
matching directory size) and had **zero** overlap in id with the streamed
pool — genuine, unique, complete audio that exists nowhere else, correctly
decoded directly.

## The fix

Before batch-decoding every `DIDX` entry in a Wwise bank as if it were a
complete stream:

1. Walk the bank's chunk sequence (`BKHD`, then `HIRC` and/or
   `DIDX`+`DATA`) to find the embedded-audio index — a bank with no
   `DIDX`/`DATA` pair at all (pure `BKHD`+`HIRC`) is a real, valid
   event/behavior-script bank with zero embedded audio, not a failure.
2. For each `DIDX` entry, compare its own embedded `RIFF` chunk's declared
   content length against the directory's declared `size` for that entry.
   Skip (don't attempt to decode) any entry where they disagree — it's a
   prefetch fragment that will fail to open cleanly if fed to a decoder,
   and its real content (if wanted) needs to be found via a separate
   streamed-audio pool matched by the same numeric Wwise id.
3. Only decode entries where the two sizes agree exactly.

## Second confirmed instance (different game, different tooling)

Astral Chain (Switch): `sound/bgm/BGM.bnk`'s 75 `DIDX` entries all fail to
open in vgmstream-cli with a plain "failed opening" (no partial-decode
symptom this time — vgmstream refuses the whole file outright rather than
producing a truncated clip). Same root cause and same local-check
discriminator: entry 0's 28,815-byte embedded fragment declares a
1,633,367-byte `data` chunk internally, and the complete, correctly-sized
file for that exact short ID (`19760575`) exists as a separate loose
`sound/stream/19760575.wem`. Confirms the pattern generalizes across at
least two unrelated engines/tools (a hand-rolled decoder for NieR
Replicant's `AKPK` packages, and vgmstream-cli for Astral Chain's loose
`.bnk` files) — "every subsong in this bank fails to open, with no error
pattern that looks like real corruption" is itself a fast, cheap signal to
check the prefetch/complete-elsewhere premise before assuming a decoder bug
or an unsupported codec.
