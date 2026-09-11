# Homology/interolog and source-aware internal challenge v1

Date: 2026-09-11. Authority: DEC-0047.

## Question and information boundary

Does the DEC-0046 pair-dependent signal survive stronger interaction-transfer
controls, reduced remote-homology exposure, and restriction of training evidence
to one source? This is a locally prospectively specified follow-up on previously
explored public training data. The model family, question and parent folds were
informed by prior outcomes; this is not independent confirmation.

Reuse the 11,900 public endpoints, their three whole `local_domain_union_30`
component folds, 16,799 released P and 2,000,000 sampled U, raw identity-verified
150M embeddings and DEC-0046 pair/linear-unary checkpoints. Do not open any
development or protected package. U is unlabeled throughout. Keep every parent
artifact unchanged; new arrays go into a separate ignored namespace.

Source provenance is a new, explicitly scoped projection, not a read of
evaluator metadata. Join the original frozen pre-benchmark gene-pair evidence
to public endpoint gene mappings and then to the exact already released P
allowlist inside DuckDB. Return only `(public_positive_index, source_bit)`;
1=HI-II-14, 2=HuRI, 3=both. Require complete P coverage and no other output.
Never annotate additional pairs, inspect withheld records, or infer opportunities
from positive-only detection metadata. Original-source files are scanned inside
the constrained projection; this is not a claim that no broader archive was
physically read. No new hidden outcomes may influence model data or features.

## Sequence search and stronger controls

Run the already pinned MMseqs2 18-8cc5c binary on **only public sequences**,
single high-sensitivity search (7.5), no adaptive first-hit termination,
20% minimum exact identity, E-value <=1e-3, at least 40 alignment columns,
no coverage floor, masked low complexity and composition correction. Search
caps exceed the 11,900-target universe. Export integer spans/mismatches, lengths,
E-value and bits; recompute identical residues as
`query_span + target_span - alignment_columns - mismatches`. Filter both spans
>=40 and exact identity >=20%. Keep the maximum symmetric score over emitted
orientations. Heuristic search failure to find a hit is not nonhomology.

For qualifying alignment h, two sequence similarities are frozen:

- local: `identity * min(1, min(query_span,target_span)/80)`;
- coverage-aware: `identity * sqrt(query_coverage*target_coverage)`.

Two additional similarities are normalized 3-mer cosine and nonnegative raw
150M pooled cosine (no learned projection or heldout normalization). For each
similarity H and candidate (A,B), compute **exhaustively over every eligible
fitting P edge (u,v)**:
`max_(u,v) max(min(H[A,u],H[B,v]), min(H[A,v],H[B,u]))`.
There is no top-k neighbor truncation, test-edge lookup or test-label fitting.
This is within-species homology/representation-based interaction transfer;
"interolog" is shorthand, not evidence of evolutionary orthology.

Compare the unchanged pair head against all four transfer controls and the
empirically stronger linear-unary control, not only the weaker nonlinear null.
Also retain original direct 3-mer/pooled/length controls as descriptive context.

## Three challenges; no joint-axis claim

1. **Union evidence:** reuse DEC-0046 checkpoints on exactly its C3 panels and
   quartets, adding all four fitting-only transfer controls. Report exclusive
   HI-II-14, exclusive HuRI and shared-positive strata, using the same released
   U partners. These are evidence strata, not complete assay cohorts.
2. **Remote-homology purge:** for each fixed evaluation fold, find any outside
   endpoint connected to a heldout endpoint by a qualifying alignment with
   identity >=20%, both coverages >=20%, both spans >=80 and E-value <=1e-3.
   Remove its entire original component from fitting and normalization. Refit
   the pair and linear-unary heads, three original seeds, identical original
   five-pass recipe. Both fitting endpoints must survive. Evaluate the same
   full C3 panel. Controls use only surviving fitting P. Require zero direct
   qualifying cross-edges after purge. This controls detected remote links,
   not all transitive remote families or undetectable homology.
3. **Bidirectional source transfer:** HI-II-14→HuRI-only and HuRI→HI-II-14-only,
   separately within every original component fold. Fit only P carrying the
   visible source, including shared P. Add every other public P outside the
   evaluation fold to fitting U with weight 1; retain original sampled-U
   rational weights. Train the same two heads/three seeds from scratch; final
   checkpoints only. Evaluate target-exclusive P and the parent C3 U panel;
   shared P is not a target. Source-specific quartets are the parent frozen
   quartets with both P edges target-exclusive; no replacement selection.
   No heldout endpoint may enter fitting or normalization.

The source fits are **not** combined with the remote purge. Success on separate
axes cannot establish success under both simultaneously. Upstream training
roles and U sampling used the full source union, and both releases informed
earlier model choice. Adding target-only public P to fitting U fixes visible
label exclusion only on this public support; it cannot undo upstream curation.
Both sources share the HuRI research programme and related Y2H methodology.
Source membership cannot substitute for complete attempted/evaluable assay logs,
batch metadata, independent laboratory replication or biological negatives.

## Feasibility, execution and inference

Freeze this protocol/config before annotation counts/search; freeze tested
implementation, inputs, panels and similarities before any new fit or score.
All authorized feasible new fits finish before new heldout scoring. Use the
original recipe, models, seeds, raw identity joins and training-only normalizers;
there is no hyperparameter/model/split search. Maximum new fits: 54.

Each new arm/fold needs >=100 fitting P, >=1,000 fitting U, >=50 eligible
anchors and >=20 anchor components. Quartet statements require >=30 selected
quartets and >=20 contributing components **in every fold**. If an arm fails a
fold floor, do not fit that arm at all; report it as infeasible. Do not rebalance
or change thresholds. Missing quartet support does not block anchor evaluation.

Primary metric is the same equal-anchor design-weighted P-versus-U concordance.
Arithmetic-mean raw-score ensembles are primary; per-seed and per-fold outcomes
remain visible. Use 2,000 paired Poisson(1) original-component multipliers with
seed 20260915, the parent's partner-reweighted within-anchor ratios, and unique
four-endpoint-component quartet weights. Intervals are conditional on fixed
heads, folds, released panels and observed source membership, not refitting,
source sampling or complete population uncertainty. Parent fold-0 concentration
persists. Record all valid-replicate counts; <95% invalidates an interval.

Report paired deltas/CIs vs every frozen comparator. The strongest control is
the maximum *macro metric*, not the maximum score at each row. Report its point
margin and the descriptive paired bootstrap minimum margin. No control is
chosen for deployment using these results. A challenge's anchor signal survives
only if pair margin >=0.02 over the strongest control, every paired 95% lower
bound >0, and every fold and seed beats the linear unary point. All-comparator
requirements are conjunctive, not selection of a favorable comparison.
Quartet survival separately requires pair lower bound >0.5 and positive paired
lower bounds vs the four transfer controls. The overall claim survives only if
all four arms (union, purge, two source directions) pass; otherwise report mixed,
explained-by-controls, or inconclusive evidence, preserving individual results.
These are research triage rules, not formal universally calibrated hypothesis tests.

Sensitivity: on the union arm, retain only pairs for which neither endpoint has
any qualifying >=40-span alignment to the original fitting endpoints. Report
coverage and point metrics if >=50 anchors/20 components pooled. This is
"no detected hit", never "nonhomologous". No new success gate uses this subset.

## Verification and claim ceiling

Add synthetic tests for exact identity, reverse orientation, partial domains,
source overlap/unknowns, target-to-U reinsertion, component purging, empty support,
interolog brute-force equality and heldout-edge poisoning. A separate reference
implementation verifies all source annotations, fit masks, normalization,
learned forwards and point metrics; independently recompute sampled exhaustive
transfer scores and bootstrap arithmetic. Preserve failure logs. Validation is
same-author numerical auditing, not independent scientific peer review.

Reference methods: [MMseqs2 official guide](https://github.com/soedinglab/MMseqs2/wiki).
The previously verified source-completeness audit is
`docs/reports/m0/M0_Systematic_Screen_Metadata_Audit_and_Benchmark_Estimand_Proposal_v1.md`.
The original leakage graph already includes 30% local/domain links; its protocol
and limitations are in the accepted M0 leakage/split reports. No external source
or model download is required or authorized by this study.
