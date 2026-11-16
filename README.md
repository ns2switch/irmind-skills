# IRMind skills

Source repository for the data-only forensic skills used by [IRMind](https://github.com/ns2switch/irmind).

- `core/` contains the packages included with each IRMind release. IRMind builds from a pinned local copy; it never downloads skills during a build.
- `catalog/` contains optional community packages admitted through `/skills install catalog:<name>`. Core names are never installable catalog entries.
- Synthetic episodes and evaluator-only answers live outside installable packages.

A skill grants no permissions. Tool policy, case scope, organization limits, ContentGuard and analyst approvals remain authoritative. Packages contain no executable code.

Catalog production releases are not published until its production signing key is provisioned. Rehearsals use synthetic keys only.

[Español](README.es.md)

Licensed under MIT OR Apache-2.0.
