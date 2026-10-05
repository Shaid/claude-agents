# Positional override arg silently swallows a misplaced flag — or any argument you pass an ad-hoc probe

**When it bites:** a pipeline/stage CLI script that accepts an optional
positional override (e.g. an explicit romfs/data-dir path, falling back to
auto-detection when omitted) throws a confusing "not found" error at a path
that is obviously not a real path — often literally the `--flag=value` string
you just passed.

**The nastier variant: no error at all.** The same swallow hits *any*
argument you hand a throwaway probe that imports one of these helpers, and
there the failure is usually **silent**. A probe taking package indices
positionally (`npx tsx build/probe/sibling.ts 15 16 27`) made
`requireRomfs('few-threehopes')` read `process.argv[2] === "15"` as the
romfs root; `RdbSource.openAll()` found no `.rdb` under
`15/File/CMN/...`, returned `[]`, every loop body was skipped, and the
script printed **nothing and exited 0**. That reads as a real negative
result — "nothing matches this filter" — which is exactly the sort of false
absence that gets written into a doc, and it cost several cycles chasing a
nonexistent filter bug. **Pass probe arguments through environment
variables** (`PKGS=15,16,27 npx tsx ...`), never positionally, in any
project using this convention — and treat "a corpus scan produced no output
and exited 0" as suspect until a nonzero records-examined counter says
otherwise.

## What happened

Chimera's `requireRomfs(game, explicit)` helper (`tools/shared/game-config.ts`)
resolves the romfs directory as `explicit ?? process.argv[2] ?? findRomfs(game)`
— i.e. when a stage's `main()` doesn't pass an explicit override, it falls
back to whatever is in `process.argv[2]`, on the assumption that's either
absent or a real path override. Calling a stage script as
`npx tsx tools/few-threehopes/build-meshes.ts --limit=20` (intending
`--limit=20` as a bounded-smoke-test flag, which the script's own CLI
entrypoint does parse via `process.argv.find(a => a.startsWith('--limit='))`)
put the string `"--limit=20"` into `process.argv[2]`, which `requireRomfs`
then swallowed *first* as the positional romfs override — producing
`Three Hopes fdata directory not found: <cwd>/--limit=20/File/CMN/Asset`.
The `--limit=` flag parser never got a chance to run into a problem because
the script errored out before reaching it.

The fix at the call site: when a script accepts both a positional override
and named flags, pass the override explicitly (even as `undefined`) *and*
put any positional value before the flags on the command line — or, when
smoke-testing programmatically, call the exported function directly
(`buildMeshes(romfsPath, limit)`) instead of shelling out, which sidesteps
`process.argv` entirely.

## Generalization

Any game-re pipeline script with a "positional override, else auto-detect"
CLI convention has this trap: a flag placed in the position reserved for the
override gets silently reinterpreted as a path, and the resulting error
message (a bogus path built by string-concatenating the flag into a
directory join) looks like a corpus/data problem rather than a CLI-parsing
one. Before trusting such an error, check whether the invocation put a
`--flag` where a positional arg was expected — and prefer calling the
script's exported function directly from a small driver when you specifically
need a `--limit=`-only invocation for smoke-testing.
