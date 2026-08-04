# ISSUE-0003: Public HuRI files do not reconstruct the full attempted/evaluable pair universe

**Status:** Resolved by approved estimand narrowing; the tested universe was not recovered
**Opened:** 2026-08-03
**Severity:** High scientific-validity risk
**Owner:** Codex

## Observation

HuRI is presented as nine systematic Y2H screens across Space III, but the public portal downloads are positive interaction lists. The publication supplements expose valuable construct, assay-version, positive, retest, validation, random-control, and selected negative/invalid/autoactivator records. They do not expose a complete pair-level log proving, for every candidate pair and orientation, selection, attempted status, technical evaluability, and observed outcome in every screen.

The screen design further prevents reconstruction by simple Cartesian product: assay-version clone sets differ, strong bait autoactivators were removed, candidate calls used screen/run-specific thresholds, and only selected candidates were pairwise retested.

## Consequence

`not listed in HuRI` cannot mean `experimentally negative`. Doing so would create a very large, systematically biased false-negative class and would invalidate both calibration and biological interpretation.

## Mandatory mitigation

- Store missing/unreported pairs as unknown.
- Never convert invalid, autoactivating, or technical-failure states to negatives.
- Preserve explicit negatives only with their exact assay, construct, orientation, and control-sampling context.
- Use a positive–unlabeled or latent-observation formulation until the attempted/evaluable universe is resolved.
- Report the resulting estimand as evidence-conditioned assay detectability/compatibility, not universal binding probability.

## Resolution paths

1. Locate an official pair-level screen log containing screen/run, bait and prey ORFs, orientation, assay version, selection, evaluability, technical state, and outcome.
2. Obtain the same metadata from the source investigators under terms compatible with reproducible project use.
3. If neither is possible, formally freeze the primary design as PU/latent-label and validate it by simulations plus held-out explicit controls and independent evidence sources.

No laboratory work is available, so the project cannot resolve this issue by generating a new exhaustive negative screen.

## Exit criteria

The issue closes only when either:

- at least 90% of the declared systematic candidate universe has auditable pair-level selection and evaluability states and remaining missingness is characterized; or
- the expert group approves a blueprint amendment making PU/latent-label inference the definitive primary estimand and removes any claim requiring a complete tested-negative universe.

Acquisition and provenance-aware positive-evidence parsing may proceed while this issue remains open. Binary label construction and model training may not.

## Validated public-data disposition (2026-08-03)

The production metadata audit and its independent validator are complete:

- audit SHA-256: `db75b0cb2863cc1b44e45759e924bfc4b00d379fa291873e7e3e10e99748fc5e`;
- validation SHA-256: `2ca92051172b7a7a512072f3ed6212ac8caed5891870abcea7c6e5929cd56a01`;
- validation result: 71 pass, 0 fail, 3 expected blocker warnings;
- HuRI/HI-II-14 evidence: 220,934 rows, all positive;
- primary HuRI negative evidence: zero rows; and
- complete pair-level selected/attempted/evaluable universe: not reconstructed.

The audit covered all 29 scientific supplementary tables, the supplementary
methods and table guide, the portal representations, and the public authors'
repository at its reviewed commit. No public attempted-pair log, complete
retest-failure log, prescreen exclusion log, or alternate scientific tag or
branch was found. The authors' repository has no license file and was not
ingested.

Resolution Paths 1 and 2 remain conceptually available if new official data
appear, but neither is executable from the current public release. Resolution
Path 3 is proposed in:

- `configs/benchmark_estimand_policy_proposal_v1.yaml`;
- `docs/blueprints/iPIN_OpenPPI_Blueprint_Amendment_001_PU_Compatibility_Primary_Design_PROPOSAL_v1.md`; and
- `governance/decisions/DEC-0010-propose-pu-compatibility-primary-design.md`.

## Resolution record (2026-08-04)

The expert group explicitly accepted Blueprint Amendment 001 in `DEC-0011`.
The second exit criterion is therefore satisfied: the definitive primary
estimand is reference-sequence positive–unlabeled ranking and every claim that
requires a complete tested-negative universe has been removed from the active
programme.

This governance resolution does **not** mean that the HuRI attempted/evaluable
pair universe was recovered. The underlying source limitation is permanent for
the frozen public release and remains binding: unreported HuRI pairs are
unlabeled, not negative. A future complete opportunity log could activate TU-C
only through a separate gate.

The accepted decision also authorizes a separate negative-evidence discovery
audit. Its records remain source- and context-conditional and cannot reopen a
universal negative class. Label, split, structural, and model construction
remain prohibited pending later gates.
