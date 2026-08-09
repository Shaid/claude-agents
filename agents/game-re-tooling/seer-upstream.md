# Upstreaming reusable tooling to `@seer/*`

**When it bites:** you built or found code in a project's `tools/`/`src/`
that has **zero game-specific logic** — a generic compression codec, a
container-format parser, a math/array utility, a CLI helper — and it could
plausibly recur in another seer-family project. The signal that confirms
"plausibly" isn't theoretical: it's a *second* unrelated project in the
family independently hitting the same thing. (Real example: a TypeScript
LZEXE v0.91 decompressor, ported while tracing Vengeance of Excalibur's DOS
VGA executable, moved to `@seer/pipeline` once Conan the Cimmerian — a
different game, different developer, same era — turned out to need the
identical decompression. One project needing it is a maybe; two confirms it.)

## Check before building anything new

Read the target package's own README and skim its `src/` — don't assume
from the package name alone. A near-miss (same idea, slightly different
signature) should usually be *extended*, not duplicated alongside. `@seer/core`
already picked up an `AtlasMeta`/`AtlasFrame` type and a `cyclePalette()`
utility this way, after both were found independently redeclared (one of
them *wrongly*) across multiple consumer projects' scaffolded templates.

## Which package it belongs in

| Kind of code | Package |
|---|---|
| Browser-safe, zero/minimal deps (binary readers, asset-loading, generic shape types) | `@seer/core` |
| Node-only offline pipeline utility (file I/O, PNG/WAV writers, decompressors, hex-dump) | `@seer/pipeline` |
| Generic IFF-85 container parsing | `@seer/iff` |
| SMUS/Sonix audio format + synthesis | `@seer/smus` |
| Something that needs its **own** heavy, unrelated runtime dependency | **a new package**, not a bolt-on to an existing one |

The last row matters: `@seer/engine` was renamed to `@seer/engine-2d` (freeing
the name for a planned `@seer/engine-3d`) specifically so a PixiJS-based 2D
engine and a Three.js-based 3D engine stay separate packages — folding both
into one would mean every 2D-only consumer's `npm install` also pulls in
`three`, for nothing. Prefer a new package over merging incompatible
dependency trees.

## Testing without the real data

The whole point of moving code out of a consumer project is that the seer
repo has **no access to (and must never vendor) that project's real,
often-copyrighted game files**. Don't let that become an excuse to skip
tests or fake coverage:

- If the format/algorithm is simple enough to hand-construct a real, valid
  synthetic fixture correctly (most IFF-derived chunk formats are), do that
  — a small real-format file you built beats a mock every time.
- If it isn't (an interleaved bitstream compression format is a real
  example that isn't worth the risk of a subtly-wrong hand-built fixture),
  write the package's own tests for what *can* be verified without real
  data — malformed-input/error paths are almost always testable this way —
  and leave a clear docblock note that full round-trip correctness is
  verified in the originating consumer project's own test suite (name the
  file), which already has the real data gitignored locally. Don't silently
  under-test; say exactly what's covered where and why.
- Either way, re-run the **consumer's** full test suite after switching its
  import to the package — that real-data test is the actual proof the move
  didn't change behavior, not anything you can assert from the seer side
  alone.

## Propagating a breaking rename/move across every consumer

A change like this usually needs the same treatment in every sibling
project (`crawl`, `wyrm`, `nicodemus`, `sorcery`, `middilgard`, `strike`,
`hunter`, `ceres`, ...), not just the one you started in — check each
repo's actual `package.json` + real import sites yourself, don't assume
which ones are affected. When fanning this out across many repos (directly
or via sub-agents):

- Stage **by exact filename**, never `git add -A`/`git add .`/`git add -u`.
  A repo can have substantial unrelated in-progress work sitting
  uncommitted; sweeping it into your commit is a real incident that has
  happened, not a hypothetical.
- If a repo's git state looks unusual (no prior commits at all, a huge
  pre-existing dirty working tree, detached HEAD) — **stop, report it, and
  wait** rather than deciding unilaterally how to fold that state into your
  commit. This is exactly the situation an over-eager "clean commit" makes
  worse, not better.
- A stray project-local `.gitignore` rule can silently hide real, legitimate
  source files from git for years (a bare `data/` pattern matching a nested
  `src/data/` is a real, previously-undetected case across four sibling
  repos) — if a file you expect to see modified doesn't show up in `git
  status`, check `git status --ignored` before assuming it doesn't exist.

## After landing it

- Update the package's own README with the *real*, verified signature — a
  stale or invented-looking API description is worse than no docs (this
  package family has shipped more than one README documenting a function
  parameter that never existed).
- Update every consumer's import path/comments, delete the now-redundant
  local copy, and confirm that consumer's tests/lint/`tsc --noEmit` are
  still clean before calling it done.
