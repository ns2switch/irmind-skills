# Third-party notices

Core methodologies and the development tools are original IRMind project text
under MIT OR Apache-2.0. The initial package bytes are identical to those compiled
in IRMind v0.5.0.

## HuntEval synthetic episode data

The AWS IAM, Azure IAM and GCP IAM public sources and the separate Azure/GCP
evaluator answers originate from [HuntEval](https://github.com/ns2switch/HuntEval),
commit `4cbb555a56bc17cb03b988ad2f15b1374eecf183`.
Copyright 2026 Aníbal Cañada. Licensed under Apache-2.0; see its
[license](https://github.com/ns2switch/HuntEval/blob/4cbb555a56bc17cb03b988ad2f15b1374eecf183/LICENSE).
The original attribution and checksums are also retained in the producing
[IRMind notice](https://github.com/ns2switch/irmind/blob/v0.5.0/THIRD_PARTY_NOTICES.md).

Expected answers are evaluator data outside installable packages. Neither the
model nor evidence ingestion reads those files. Scripted tests measure integration
and control behavior; they do not claim an independent real-model benchmark.
