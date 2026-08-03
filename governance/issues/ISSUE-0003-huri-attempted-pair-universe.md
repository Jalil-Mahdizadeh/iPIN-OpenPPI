# ISSUE-0003: Public HuRI files do not reconstruct the full attempted/evaluable pair universe

**Status:** Open; mitigated for acquisition, blocking for primary negative labels  
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
