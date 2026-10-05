# A probe script written outside the repo tree can't import the project's `file:`-linked ESM-only dependency

**When it bites:** you write a throwaway probe into the session scratchpad
(as the standing "use the scratchpad, not `/tmp`" instruction tells you to),
run it with `npx tsx /path/to/scratchpad/probe.ts`, and it dies immediately
with — or you skip the file entirely and run `npx tsx -e "..."` (or
`--eval`) for a quick one-off check, **even from the repo root itself**,
and hit the identical error anyway:

```
Error [ERR_PACKAGE_PATH_NOT_EXPORTED]:
  No "exports" main defined in <repo>/node_modules/@seer-project/pipeline/package.json
```

The message names the *dependency* and its `package.json`, so it reads as
"that package is broken / needs building" — and there is a real, separate
trap with exactly that shape (see
`file-linked-local-package-needs-build-before-dev-server.md`), which sends
you off to check `dist/` and rebuild the sibling repo. That is not what this
is. `dist/index.js` is present and fine.

## What's actually happening

The package is `"type": "module"` with an `exports` map that only declares
an `import` condition. Node/tsx pick CJS-vs-ESM for *your* file from the
nearest `package.json` walking **up from the script's own path** — and a
script sitting in the scratchpad has no `package.json` above it, so it is
compiled as CommonJS. The resulting `require()` goes through
`resolveExports` asking for the `require` condition, finds only `import`,
and reports "no exports main defined". The dependency resolves to the repo's
`node_modules` (the error path proves it), so nothing about the *lookup* is
wrong — only the module kind of the caller.

`npx tsx -e "..."` fails the identical way for the identical reason, even
when the shell's cwd *is* the repo root: `-e`/`--eval` has no real file
path at all, so there is no "script's own path" to walk up from, and tsx
falls back to the same CommonJS default it uses for a path-less caller.
Being inside the repo directory when you invoke it doesn't help — the
module-kind decision is keyed on the (nonexistent) script path, not the
process's current working directory.

## The fix

**Put ad-hoc probes inside the repo tree as a real `.ts` file** — a
gitignored or untracked scratch dir such as `build/probe-<topic>/` (or, for
a one-off, directly in an existing tool directory, deleted right after) —
so the file inherits the project's `"type": "module"` from its own nearest
`package.json`, then run it by **path**
(`npx tsx build/probe-g1a/dump.ts` / `npx tsx tools/foo/scratch.ts`) rather
than via `-e`/`--eval`, and delete the file when done. Copy anything worth
keeping into the session scratchpad afterwards for the record. Dropping a
bare `{"type":"module"}` next to the scratchpad script fixes the module
kind but not `node_modules` resolution, so it is not a reliable substitute;
neither is invoking `-e` from the right directory, since it never gets a
script path to resolve against in the first place.

Confirmed on `~/Development/chimera` (a seer-framework project depending on
`"@seer-project/pipeline": "file:../seer/packages/pipeline"`); every sibling
seer repo has the same shape, and every session that follows the
scratchpad instruction will hit it the first time a probe imports anything
from `tools/`.
