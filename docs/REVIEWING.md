# Reviewing and publishing skills

[Español](REVIEWING.es.md)

## Automated evidence and human judgment

CI checks package limits/structure with the **released IRMind compiler**, byte
identities, default-build source/mapping availability, reserved core names,
SemVer increases and each scripted synthetic episode through signed admission,
evidence queries, proposed/analyst-confirmed findings, verification, seal and
export. Expected answers stay outside packages and model context. A report
summarizes coverage and non-blocking notices for unusual tools and instruction-like
wording. Heuristics are not proof of safety or correctness.

A reviewer must assess methodology, minimal tools, false positives, honest coverage,
source acquisition instructions, original writing and whether the synthetic episode
represents the claim. Look for attempts to bypass policy, request approvals or
expand scope, including indirect instructions in references. Do not execute package
content. No real incident data or secrets are acceptable. An attack technique is
not confirmed merely because a query matched.

PR workflows have read-only permissions, no release environment and no secrets.
The trusted default-branch reporting workflow reads bounded JSON as data, checks
the originating PR/run and comments fixed-format results; it never executes PR code.
Fork workflows require maintainer approval according to repository settings.

## Publish a catalog release

1. Merge reviewed packages after CI. Choose a new numeric or prerelease tag and
   a strictly increasing `release_sequence` in `catalog-release.json`. Commit the
   change through a PR. Never replace a published tag/index. Changes to a method
   require a new package version.
2. Create the tag on green main and launch **Publish signed skill catalog**
   (`release.yml`) at that tag. Validation freezes the latest published IRMind
   compiler/engine commit; core packages are never indexed.
3. Review the immutable tag, index sequence, packages and validation result before
   approving the protected **release** environment. Only its signer process reads
   `CATALOG_ED25519_SEED_HEX`; it is never an argument, file or artifact. Production
   and synthetic rehearsal signers have separate workflows. Do not enable debug
   tracing or print environment variables. A mismatched public key fails closed.
4. The workflow verifies Ed25519, signs payloads and SHA256SUMS with Sigstore,
   attaches provenance and an SBOM, then publishes the release. Check the workflow
   and independently download/verify with `tools/verify_release.py` (see README).
   Inspect the key ID against IRMind's compiled roots and the tag's exact OIDC identity.
5. With the published IRMind binary, run `/skills install catalog:<name>`. Check
   preview/version/coverage/tools, sign admission and use a synthetic case through
   verification, sealing and export verification. Retain negative tests for changed
   index bytes, a different signing key and a lower previously signed sequence.

## Corrections and withdrawal

Publish a new version with clear correction/coverage notes; never overwrite old
assets. To withdraw a problematic method, remove it from a new higher-sequence
index and explain the withdrawal in release notes. Already installed packages do
not change silently: notify users to inspect, update or disable them. A key withdrawal
requires an IRMind release; a catalog release cannot replace compiled trust roots.

For a reported security problem, keep any sensitive report private, fix it with
neutral technical wording and publish the correction promptly under IRMind's
pre-1.0 policy. Do not publish incident data or secrets. The maintainer decides
whether to withdraw the method, publish a corrected version or rotate the key.
