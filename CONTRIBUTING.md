# Contributing skills

IRMind skills are data-only forensic methods licensed under MIT OR Apache-2.0.
Write original prose, cite public methodology sources and use synthetic evidence.
Do not submit incident data, credentials, executable code, scripts or instructions
that weaken policy, custody, ContentGuard, scope, approvals or TLS verification.

## Choose the correct tree

| Tree | Delivery | Changes |
| --- | --- | --- |
| `core/<name>/` | Compiled into an IRMind release | Improve an existing core method here; a normal IRMind synchronization PR pins the accepted commit. |
| `catalog/<name>/` | Optional analyst-admitted installation | Add specialized community methods with a distinct name. These packages may be distributed independently after publisher-key provisioning. |

Never duplicate or rename a core package into `catalog/`. The index builder and
IRMind independently reject catalog packages whose names shadow the core.
Core packages are not installable catalog entries. A method is never executable
and never extends permissions, even when signed.

## Package and episode

Start from [the template](template/package/SKILL.md). A package has `SKILL.md` and optional
`queries/`, `rules/` or `references/` text resources. Use the format and limits of
the latest published IRMind compiler: currently 32 KiB per file, at most sixteen
companion resources and 128 KiB overall. Declare only needed tools and honest
source/mapping coverage; describe false positives and confirmation criteria.

Put the scripted scenario at `episodes/<core|catalog>/<name>/episode.json` and
synthetic public input under its `source/` directory. Put expected answers under
`episodes/private/`; never put them in the package or source tree. The public
script contains literal local tool proposals and source-index placeholders, not
code. The independent evaluator opens private answers after the model completes.
Each episode must retrieve actual source evidence, load the method, propose
unconfirmed findings, confirm them as the synthetic analyst, verify custody,
seal and independently verify the export.

For catalog entries, add `metadata/<name>.json` with `minimum_irmind_version`,
`mappings` and `coverage` (`status` and a bounded `description`). This metadata is
outside the installable package. Use the version, target schema and declared
source modules from the package; do not claim unsupported mappings as complete.

Refresh core commitments with `python3 tools/inventory.py --write`, then run
`python3 tools/inventory.py` and `python3 -m unittest discover -s tests -v`.
Core fixture changes also update the explicit source mirror; compiler or engine
code is never accepted in that mirror. CI freezes the latest published IRMind
tag and commit, uses its unchanged compiler and engine, and runs local scripted
episodes without provider credentials. These tests validate integration and
controls, not forensic accuracy with a real model or real incident.

## Trust and publishing

No download or update is automatic. Installing or updating a catalog skill
requires publisher-index verification, preview and a separate Analyst signature.
An installed skill remains untrusted content and never enters the system role.
Catalog signatures and analyst admission are different guarantees.

Production publication is disabled. The manual release rehearsal uses a known
synthetic Ed25519 key, Sigstore and GitHub attestations, and uploads CI artifacts
only. Never compile its key into IRMind and never use it for a production index.
Production-key generation and provisioning remain maintainer operations.

Pre-1.0 minor IRMind releases may change package formats without migration.
Keep tests compatible with the latest released compiler; do not add historical
interpreters or silently rewrite an admitted package.

[Español](CONTRIBUTING.es.md)
