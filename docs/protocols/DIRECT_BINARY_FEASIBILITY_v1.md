# Bounded direct-binary feasibility assessment

Date: 2026-09-11. Authority: DEC-0050. Namespace: `direct_binary_feasibility_v1`.

## Question and boundary

Can existing public data support a separate, construct-aware within-anchor
partner-specificity study, with evaluable assay non-detections and adequate
matched alternatives? This is data/design triage, not validation of any model.
No population binding probabilities or universal nonbinding labels are sought.

Before this protocol, we read earlier aggregate audits, the two candidate
papers' public descriptions, supplement descriptions, and the SAVEXIS repository
file inventory. Thus source selection is informed, not blind. No new source
pair table has yet been downloaded or parsed locally, and no new source model
scores have been computed. Timestamp and hash this file before acquisition.

Bound the new follow-up to Shilts 2022 SAVEXIS and Wojtowicz 2020 apECIA.
Existing Negatome/IntAct and Lambourne 2026 / TF-isoform 2025 aggregate audits
provide context only; their pair data stay closed. Do not extend the search
after the bounded disposition simply because a gate fails.

## Decision sequence

1. Public, versionable source and independently generated direct-binary
   measurements. Experimental independence is not proof of zero training-pair,
   homolog, interolog, or protein-language-model pretraining exposure.
2. Reconstructable candidate space and orientation-specific observed assay
   states. Distinguish missing, failed/unevaluable, below-threshold, positive,
   and selected secondary follow-up. Pooled non-detection is not an individual
   pair measurement. A finite numeric value alone does not prove evaluability.
3. Linkable assayed construct sequences/boundaries and relevant QC/conditions.
   Do not silently replace ectodomains, isoforms, heteromeric constructs or
   unresolvable identifiers with canonical full-length proteins.
4. Only if steps 2 and 3 support an auditable evaluable-P/N subset, count
   within-anchor matched support. Keep assay orientation and screening stage
   fixed. For a diagnostic starting point inherit DEC-0049's partner length
   ratio <=1.25, amino-acid frequency TV <=0.10, and >=5 eligible alternatives
   per P; report rather than tune failures. No learned-score selection.
   Do not import its fold-specific support floors as a power calculation for
   a different study. Confirmation requires its own effect/precision-based
   design and independent anchor/family effective sample size before scoring.
5. Evaluation readiness additionally requires a current actual-training
   pair/endpoint/homology/interolog exposure audit, a claim-aligned split,
   adequate confirmation precision, and confirmation isolated from pilot
   outcome-driven design. Public old data are not intrinsically untouched.

Stop at an unmet mandatory prerequisite; do not fabricate matched-P/N counts
from ambiguous outcomes. Raw coverage/structure counts may still be reported
as such. `not assessed` is different from `failed`, and neither is a pass.
If no source is evaluation-ready, keep the current model track stopped and
state whether a specific source merits a separate data-only pilot. Do not
claim that a bounded negative result proves no suitable data exist anywhere.

## Acquisition and verification

Use `containers/images/ipin-data-arm64_0.1.2.sif`, SHA256
`72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629`.
SAVEXIS upstream commit: `82442448e9440c9e847415173979871950e27d77`.
Freeze a filename/blob-ID allowlist before acquisition; maximum twelve files
and 25,000,000 payload bytes. Store raw files under the new ignored run
namespace, using exclusive creation. Record URL, UTC acquisition, byte size,
Git blob SHA1 and SHA256. Verify before reuse. No upstream code execution.

Only aggregate inventories, original audit code, source links, decisions and
reports enter tracked files. The upstream repository declares GPL-3.0;
article material and the separate Dryad deposit have their own terms. Do not
infer that article licensing covers all payloads or copy upstream source code
into the project's implementation. No raw-payload redistribution is needed.

Report schemas, missingness, orientation/construct ambiguities and decisions.
Check aggregate arithmetic independently where computable and verify prior
study registries remain intact. No full model regression is required for
data-only triage, and existing tests are not evidence that a new assay is valid.
