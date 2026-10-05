# A corpus of same-shaped text files can have a real minority in a different encoding — the mismatch fails silently, not with an error

**When it bites:** a corpus of same-shaped debug/text export files (a
build tool's per-object/per-bank text dumps, a localization export, any
"one file per X" text-table family) is assumed uniformly encoded because
the samples you first checked decode fine as plain ASCII/Latin-1/UTF-8 —
before trusting a "this file/sub-corpus has zero real content" negative
from a row-level text parser (a numeric-id regex check, a delimiter
split), check the file's leading bytes for a BOM.

Confirmed on Metal Gear Rising: Revengeance (PC, `flower`): ~400 Wwise
"SoundbanksInfo" debug cue-sheet `.txt` files inside `data002.cpk`'s
`Debug/sound/` folder are almost all plain ASCII, but a real minority
(`r000.txt` and its `r*`/`ra*`/`rb*`/`rc*`/`rd*` siblings — a genuine Wwise
"Unicode text" export variant, not corruption) are UTF-16LE with a literal
`FF FE` BOM. A parser that decoded the whole corpus as plain UTF-8/Latin-1
(the pattern already verified correct against every previously-sampled
`BGM*.txt` file) silently produced **zero** matched rows for these files —
each row's numeric-id cell decoded to null-interleaved garbage that failed
a `/^\d+$/` check, with no exception anywhere in the pipeline. The failure
mode looks exactly like "this file just has no real content of the kind
I'm searching for," not like an encoding bug — nothing crashes, nothing
warns, the row count for that file is just quietly zero.

**Fix:** detect the BOM (`buf[0]===0xFF && buf[1]===0xFE` for UTF-16LE, the
mirror for UTF-16BE) and pick the decoder per-file, before assuming one
encoding holds for a whole same-shaped corpus just because a majority (or
every previously-sampled file) shares it. Cheap to add, easy to skip
because most samples "just work."
