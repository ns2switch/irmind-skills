# IRMind skills

Source repository for the data-only forensic skills used by [IRMind](https://github.com/ns2switch/irmind).

- `core/` contains the packages included with each IRMind release. IRMind builds from a pinned local copy; it never downloads skills during a build.
- `catalog/` contains optional community packages admitted through `/skills install catalog:<name>`. Core names are never installable catalog entries.
- Synthetic episodes and evaluator-only answers live outside installable packages.

A skill grants no permissions. Tool policy, case scope, organization limits, ContentGuard and analyst approvals remain authoritative. Packages contain no executable code.

Production catalog releases require the protected release environment and maintainer approval. The production public key is pinned by IRMind v0.5.4. Rehearsals use synthetic keys only.

[Español](README.es.md)

Licensed under MIT OR Apache-2.0.

## Packages and validation

There are **23 core packages** and **1 community example in catalog/**. A catalog entry becomes installable only after its signed release. The original v0.5.0 commitments are in the [inventory](core/package-identities.json) and [initial baseline](core/baseline.json).

| Skill | Declared sources |
| --- | --- |
| [aws-credential-compromise](core/aws-credential-compromise/SKILL.md) | parser-json |
| [aws-s3-data-exfiltration](core/aws-s3-data-exfiltration/SKILL.md) | parser-json |
| [azure-entra-identity-compromise](core/azure-entra-identity-compromise/SKILL.md) | parser-entra, parser-ecs, parser-json |
| [gcp-service-account-abuse](core/gcp-service-account-abuse/SKILL.md) | parser-gcp-audit, parser-ecs |
| [k8s-cluster-compromise](core/k8s-cluster-compromise/SKILL.md) | parser-kubernetes, parser-gcp-audit, parser-falco |
| [k8s-workload-compromise](core/k8s-workload-compromise/SKILL.md) | parser-kubernetes, parser-falco, parser-gcp-audit |
| [linux-persistence](core/linux-persistence/SKILL.md) | parser-linux, parser-ecs, parser-velociraptor, parser-plaso |
| [linux-triage](core/linux-triage/SKILL.md) | parser-linux, parser-syslog |
| [linux-webshell](core/linux-webshell/SKILL.md) | parser-linux, parser-ecs |
| [malware-execution-triage](core/malware-execution-triage/SKILL.md) | parser-evtx, parser-ecs, parser-eztools, parser-velociraptor, parser-plaso |
| [network-c2-beaconing](core/network-c2-beaconing/SKILL.md) | parser-zeek, parser-suricata, parser-ecs |
| [windows-lateral-movement](core/windows-lateral-movement/SKILL.md) | parser-evtx, parser-ecs, parser-hayabusa, parser-velociraptor |
| [windows-persistence](core/windows-persistence/SKILL.md) | parser-evtx, parser-ecs, parser-eztools, parser-velociraptor, parser-plaso |
| [windows-ransomware](core/windows-ransomware/SKILL.md) | parser-evtx, parser-ecs, parser-eztools, parser-velociraptor, parser-plaso |
| [windows-triage](core/windows-triage/SKILL.md) | parser-evtx, parser-hayabusa, parser-eztools, parser-velociraptor, parser-plaso |

[Contributing](CONTRIBUTING.md) · [Package template](template/package/SKILL.md) · [Episode example](template/episode/episode.json)

CI freezes a tag and commit of the latest published IRMind release, including pre-releases. It uses the real compiler, limits, policy, guard and engine, runs every core and catalog episode and the existing hostile-content tests, verifies, seals and exports. Provider credentials are unnecessary. Private answers stay in `episodes/private/` and are opened only after the model finishes.

The signed index contains only `catalog/`. Packages under `core/` arrive with each IRMind release and are not installable through `/skills install catalog:`. Propose core improvements here; a development script creates a pinned local mirror through a normal IRMind PR. The IRMind build never downloads packages.

The manual rehearsal creates indexes with a known synthetic Ed25519 key, Sigstore bundles, GitHub provenance and an SBOM. It stores CI artifacts only: it never creates a release or accesses production keys. For external artifact checks use `cosign verify-blob` with the exact workflow identity and `gh attestation verify`; rehearsal identity refers to its branch, not a production release.

## Propose a skill

[Contribute a methodology](CONTRIBUTING.md) without Rust: sources, false positives, queries and synthetic episodes. `core/` ships with IRMind; `catalog/` becomes installable only after a maintainer-approved signed release. Start with [the EC2 example](catalog/aws-ec2-cryptomining/SKILL.md).

## Verify a published catalog

Requires OpenSSL 3, cosign 3.1.3+ and a current GitHub CLI. Download the exact
release's assets, then verify the Ed25519 index, package hashes, checksum manifest,
Sigstore workflow/tag identity and provenance independently:

```sh
gh release download v0.1.0 -R ns2switch/irmind-skills -D verified-catalog
python3 -B tools/verify_release.py --directory verified-catalog
```

The production key ID is
`f04daae3f8243ed76452d5f787ea527c8fbec895ca0c91a35f453f6677575e4f`.
The exact Sigstore identity is
`https://github.com/ns2switch/irmind-skills/.github/workflows/release.yml@refs/tags/v0.1.0`,
issuer `https://token.actions.githubusercontent.com`. IRMind v0.5.4 compiles the
Ed25519 public key; it does not require cosign at runtime. Installation is explicit:
`/skills install catalog:aws-ec2-cryptomining`. Inspect coverage and tools before
signing admission. Core names cannot be overridden. [Release review](docs/REVIEWING.md)
explains publication and withdrawal. Synthetic rehearsals never use the production seed.
