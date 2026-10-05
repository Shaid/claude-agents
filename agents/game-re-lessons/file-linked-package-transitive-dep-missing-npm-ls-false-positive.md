# `npm ls`/`npm install` can both report a dependency as fine while `require()` still fails

**When it bites:** a seer project is the first to exercise a newly-added
pipeline dependency of one of its `file:`-linked local packages (e.g. a
`@seer-project/pipeline` helper starts using `sharp` for the first time,
and the consuming project's own `package.json` gets a matching `"sharp":
"^0.35.x"` entry added). `npm ls sharp` reports it resolved at the expected
version, and `npm install` (with or without `--no-audit --no-fund`) reports
"up to date" with no changes made — yet the very first real `import
sharp`/`require('sharp')` in pipeline code throws `MODULE_NOT_FOUND` (or
the equivalent ESM resolution error), with no other symptom.

Confirmed on Reunion (Amnesty Design, Amiga AGA, `methanoid` project):
`@seer-project/pipeline`'s `writePNG()` helper depends on `sharp`; the
consuming project (`methanoid`) had `sharp` added to its own
`package.json` `dependencies` and both `npm ls sharp` and a plain `npm
install` reported everything fine. The actual gap was only surfaced by
`node -e "console.log(require.resolve('sharp'))"`, which threw
`MODULE_NOT_FOUND` — `sharp`'s package directory was simply absent from
`node_modules` despite npm's own bookkeeping believing it was satisfied.
Root cause: a `file:`-linked sibling package's own dependency list had
changed more recently than the consumer's `node_modules` was last fully
materialized, and a plain `npm install` in an npm workspace doesn't always
re-materialize every new transitive dependency introduced this way — it
can trust its existing lockfile/tree state without actually checking each
linked package's binary presence on disk.

**The fix:** don't trust `npm ls`/`npm install`'s silence as proof a
newly-added dependency is actually importable — after adding or bumping
any dependency (your own, or one pulled in transitively through a
`file:`-linked package), do a direct resolution check
(`node -e "require.resolve('<pkg>')"` or an equivalent real import) before
writing code that depends on it, especially in a monorepo where packages
are symlinked rather than tarball-installed. If the check fails despite
`npm ls` looking clean, run an explicit `npm install <pkg>@<matching
version>` at the consumer's own root — this reliably re-materializes the
missing package directory where a bare re-run of `npm install` did not.
This is distinct from `file-linked-local-package-needs-build-before-dev-server.md`
(that lesson is about the linked package's own `dist/` not being built at
all) — here the linked package is built fine, and the gap is one level
further down, in the *consumer's* own `node_modules` for a package the
linked package merely depends on.
