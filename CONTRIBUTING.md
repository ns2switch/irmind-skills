# Contributing a forensic skill

[Español](CONTRIBUTING.es.md) · [Reviewer guide](docs/REVIEWING.md)

You can improve an investigation methodology without writing Rust. For a new
method, optionally open a **Skill proposal** issue first, especially when coverage
is uncertain. Small fixes can go directly to a pull request.

1. Fork this repository and create `catalog/<name>/` from `template/package/`.
   Start with [aws-ec2-cryptomining](catalog/aws-ec2-cryptomining/SKILL.md) as a
   complete example. Core names are reserved; use lowercase hyphenated names.
2. Fill every frontmatter field: format, name, description, SemVer version,
   author, license, target_schema, tools, sources, categories and invocable.
   Write a step-by-step method using the common event schema's category, type,
   outcome and role filters. State required sources/mappings, how to collect
   them, coverage gaps, ATT&CK candidates, confirmation criteria and false positives.
   Declare only the tools actually needed. Skills never confer permissions.
3. Add `metadata/<name>.json` using the example's exact fields. Sources and
   mappings must exist in the default build of the latest published IRMind.
   Partial analytical coverage is allowed when clearly described; an unavailable
   primary source is not. Add data-only query/reference files if helpful.
4. Put a small synthetic episode under `episodes/catalog/<name>/`, following
   the example's `episode.json` and `source/`. Put expected answers under
   `episodes/private/`, outside the installable package. The scripted model must
   query evidence, propose findings and leave confirmation to the analyst.
5. Obtain a clean checkout of the latest **published** IRMind release outside
   this repository (the tools overlay fixtures there). With its Rust toolchain,
   Python 3.11+ and cargo-nextest installed, run:

   ```sh
   git fetch origin main
   git worktree add --detach ../skills-baseline origin/main
   python3 -B -m unittest discover -s tests -v
   python3 -B tools/review.py --root . --baseline ../skills-baseline --irmind ../irmind-release --output review-results.json
   python3 -B tools/validate.py --irmind ../irmind-release
   git worktree remove ../skills-baseline
   ```

   The released compiler and real engine are authoritative. Episodes run locally
   with scripted responses, no provider calls and no expected answers in context.
6. Open a PR with the checklist. Explain coverage, methodology changes and why
   each tool is needed. Any package content change must increase its SemVer:
   patch for a correction, minor for added methodology, major for incompatible
   scope/interpretation. Build metadata alone is not a version increase.

## Content and license

Write original text, under **MIT OR Apache-2.0**. Cite public ATT&CK or vendor
documentation; do not copy copyrighted posters or guides. Use synthetic data
only: no real incident records, secrets, personal information, executables or
scripts. Do not tell a model to ignore policy, request approvals, broaden scope
or treat a skill as authority. Optional resources are data, never executable.
The package remains subject to ContentGuard, case scope and normal approvals.

## Core versus catalog

`core/` is the source of the skills bundled in IRMind. Propose improvements here;
they arrive through a reviewed sync PR and a subsequent IRMind release. Keep
`core/package-identities.json` and `source-map.json` current using `tools/inventory.py --write`.
Core package names never appear in the signed catalog and cannot be overridden.

`catalog/` contains independently installable community skills. Merge makes a
method available for review on main, **not yet installable**. The maintainer
publishes a signed catalog release in reviewed batches when ready; there is no
fixed publication schedule. After publication, an analyst explicitly runs
`/skills install catalog:<name>`, previews the package and signs admission.
No background download or update occurs.

For a working reference/coverage layout, see [the EC2 example notes](docs/ec2-example.md). Keep clickable web references outside installable resources; the existing ContentGuard admission checks remain authoritative even when a reviewer heuristic is only a warning.
