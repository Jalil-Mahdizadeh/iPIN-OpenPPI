# DEC-0026: Accept and freeze the pair-level PU-R benchmark artifacts

**Date:** 2026-08-08

**Status:** Accepted and effective; the benchmark package is immutable and all
development release, protected evaluation, and model work remain unauthorized

**Decision owner:** Codex under delegated project-execution authority

**Controlling records:** DEC-0024 and DEC-0025

## Decision

Accept `pair_level_pu_r_benchmark_artifacts_v1` as technically complete,
independently validated, and frozen exactly under the immutable `DEC-0024`
pair-level PU-R protocol.

Production construction ran from clean commit
`043bd73f4b0e6d102b339b5ac66213a88674bb94`. Its aggregate evidence was
committed before independent validation. The validator then ran from clean
commit `7dc5e0ea1bfb87526178d569350bdb4d86c15559` and passed 13 checks
with zero warnings and zero failures.

The accepted package preserves the 17,000 endpoints, 7,782
`local_domain_union_30` components, frozen endpoint partitions, all pair roles,
source-specific cells, deterministic salts/seeds, sample allocations, rational
weights, and the primary reference-sequence positive-unlabeled ranking design.

## Accepted artifacts

Accept and freeze:

- the public training census of 16,799 released-positive pairs and its
  2,000,000-row deterministic unlabeled sample;
- the encrypted development package containing 26,108 primary/source positive
  rows, 9,000,000 sampled-unlabeled rows, exact strata, and supported
  source-visible training subsets;
- the separately encrypted protected-candidate package containing 9,028,821
  candidate rows across the nine primary/source test cells;
- the separately encrypted protected-truth package containing 28,821 cellwise
  positive-truth rows, 9,000,000 sampled-unlabeled rows, and the complete
  58,049-row curator-only positive role ledger;
- all table, archive, ciphertext, manifest, certificate, inclusion-probability,
  weight, stratum, and sampling-hash records; and
- the protected evaluator custody and aggregate-receipt procedure.

Large pair artifacts remain in the designated ignored canonical root. Their
versioned manifests, checksums, public certificates, reports, schemas, code,
and validation evidence are the durable reproducibility record.

## Accepted independent checks

The validator independently reconstructed all 58,049 released-positive pairs
and their mutually exclusive training/C1/C2/C3/quarantine roles; all
source-specific roles; 129,614,029 cell-specific unlabeled population
opportunities; all 20,000,000 realized sample rows; exact bottom-hash
thresholds; reduced rational inclusion probabilities and weights; and the
9,028,821-row protected candidate union.

It found zero positive-as-unlabeled rows, zero multi-role primary positives,
zero interaction-supervision endpoint leakage, zero missing/extra/duplicate
protected candidates, and zero protected pair identities in public workflows.

Cross-cell unlabeled-pair reuse is accepted exactly as prespecified by
`DEC-0024`: 3,778,512 pair identifiers recur across independently keyed cells,
with 4,463,150 repeated rows beyond the first and a maximum of seven cells for
one pair. This is deterministic design reuse, not positive-evidence leakage and
not negative evidence.

## Accepted protected-test boundary

Protected candidate identities may not be published because the public
universe and sampler would permit positive-truth inference by set difference.
Candidate and truth keys remain distinct. A future submission is a frozen
scorer executed inside a verified no-network evaluator, never a public
pair-keyed score file.

The scorer-facing session is restricted to `candidate_token`, the two endpoint
sequence hashes, and `cell_id`. Unprojected metadata is not retained. The
scorer and session are rehashed, predictions are validated and hashed, and an
exclusive package-scoped one-first ledger is reserved before truth decryption.
Only aggregate metric receipts may leave that boundary.

Neither development release nor any protected candidate/truth access, scorer
execution, prediction, or metric computation occurred in this work package.

## Qualification note

A preproduction validator exception exposed one curator-only quarantine pair
hash in a transient operator log before identity-safe exception handling was
completed. It was not a training, development, or protected-test positive, and
no protected-test identity was exposed. The log is unversioned and excluded
from model-development workflows. Identity-safe errors were then
regression-tested and both smoke and production validations rerun successfully.
The pair remains quarantined.

## Claim disposition

Unlabeled pairs are not negatives. C3 means only both exact frozen sequence
endpoints absent from interaction-supervised training and component-disjoint
under `local_domain_union_30`. No unseen biological family, unseen domain,
PLM-unseen protein, or exhaustive-nonhomology claim is authorized.

Universal-nonbinding, prevalence, biological precision, calibration,
probability, and sampled-as-full-universe claims remain prohibited. The
TF-isoform panel remains external-only and unsuitable for training negatives
or any training role, universal-nonbinding claims, prevalence, calibration,
and unseen-endpoint/family benchmarking.

## Accepted evidence

| Evidence | SHA-256/result |
|---|---|
| Configuration | `cdafad900887e74a6148cdb6d6832e56392649703c261909d5f581e39fd9e795` |
| Package manifest | `f0f850daf795481c8a1ae0ba64f6d050ae757f2738497ac0517003c6822015f5` |
| Construction report | `878beb38af78157b8b4b3ff50cb7658266900add86a96d7d9e5baca8745c3f65` |
| Independent validation | `7eede006ba18dbc4dcc71128743722718bc73f0f6891834ad4ebc0a6ed614e86`; 13 pass |
| Production commit | `043bd73f4b0e6d102b339b5ac66213a88674bb94` |
| Validation commit | `7dc5e0ea1bfb87526178d569350bdb4d86c15559` |

The expert-facing interpretation is
`docs/reports/m0/M0_Pair_Level_PU_R_Benchmark_Artifacts_Final_v1.md`.

## Continuing hold

This decision authorizes no next work package. The accepted artifacts may not
be modified, extended, resampled, relabeled, or released to development.
Creating additional pairs or samples, opening development/protected packages,
constructing negatives or pseudo-negatives, materializing the full candidate
universe, integrating panels or structures, or implementing, embedding,
training, tuning, selecting, calibrating, evaluating, routing, or releasing a
model requires a new numbered authorization.
