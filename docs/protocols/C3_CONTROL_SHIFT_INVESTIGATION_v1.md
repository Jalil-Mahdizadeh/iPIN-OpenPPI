# C3 control-shift investigation v1

Date: 2026-09-11. Status: post-hoc diagnostic, not a model-development or
protected-test authorization. Requested after both test evaluations and the
dual-model freeze. This scope was recorded before running the new diagnostics.

## Question and boundaries

Why do the fixed 3-mer, interolog and length controls perform better on
development C3 than test C3, while the affine PLM ensemble is stable?
These controls are deterministic, not fitted neural competitors. The 650M
architecture rivals were not evaluated on the final test.

Use existing development rows/scores, frozen public sequence features and
already published test aggregates only. Do not open protected test pair rows,
truth, predictions or keys; rerun the protected evaluator; fit or select models;
reverse score directions; change split assignments; or modify any closed
evaluation, model, protocol, role or ledger. Do not interpret U as verified
non-interactions. Publish aggregates, not pair identities.

## Diagnostic sequence

1. Verify input hashes and development endpoint membership. Reproduce the
   published development concordances. Compare length and 3-mer scores over all
   development C3 rows against frozen feature formulas, and interolog against
   the original CUDA implementation. Exercise the original protected CPU
   scorer on a fixed development-only sample (all positives plus up to 8,192
   evenly spaced unlabeled rows). Use absolute tolerance 1e-12 for deterministic
   scores and 1e-9 for aggregate concordance reproduction. No new test scoring.
2. Rank development components by their pre-existing endpoint sizes, not model
   performance. Tabulate positive and HT-weighted U mass touching each of the
   ten largest components. Decompose concordance into positive-group
   contributions against the same full U reference. Separately remove **both**
   positive and U pairs touching the largest component. This last comparison
   changes the population and is not a replacement benchmark result.
3. Summarize length, within-component status, and development source membership.
   Compare controls within fixed unordered endpoint-length bins with boundaries
   200, 500 and 1,000 residues; average bin-specific concordances using positive
   mass and report coverage. This is descriptive adjustment, not causal proof.
4. For full development and the largest-component-excluded subset, calculate
   2,000 component-pigeonhole bootstrap replicates using the existing fixed
   C3-development component draws, common to both scopes. Report marginal
   intervals and paired *sensitivity* differences, not a new selection gate.
   Do not calculate a paired dev/test interval: their proteins are different.
5. Compare published C1/C2/C3 and source-exclusive aggregates. Distinguish a
   measured development mechanism from explanations of the unseen test-row
   mechanism, which these inputs cannot establish.

Use the checksum-pinned ARM64 model Apptainer image with an actual CUDA GPU.
Mount only development private inputs into the analysis runtime; hide the
repository's other private data. Check the frozen-model/history verifier before
and after. Keep new evidence under `c3_control_shift_investigation_v1`; refuse
to overwrite existing result files. Preserve all exploratory qualifications and
null results. No new test set or additional model evaluation is requested.
