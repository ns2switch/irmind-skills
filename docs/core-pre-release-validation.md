# Validate new core sources before an IRMind release

Core skills ship with the IRMind binary. Their episode inputs may use a decoder
that is present in the release candidate and absent from the latest published
binary. Catalog packages must run on the latest published IRMind version.

For a core change that introduces such inputs, compile the packages with the
released compiler. Run core source-coverage checks and the complete scripted
episodes against an exact IRMind commit on protected `main` with the required
checks green. Pin that commit through reviewed workflow code. A contributor
branch, archive from a pull request, mutable ref, or user-supplied command cannot
select the test binary. Run the existing custody, export and hostile-evidence
checks on the same candidate. Keep the catalog and its publication checks on the
published release. Both paths run without provider credentials or a release
environment.

After integrating the core changes, synchronize the immutable core commit into
IRMind through its normal mirror check. Run the same episodes in the release
candidate before publication. Return the core episode baseline to the newly
published version once that version contains the sources. This procedure uses
one released IRMind version to introduce both the decoders and their core
skills.
