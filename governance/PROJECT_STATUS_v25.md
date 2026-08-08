# iPIN-OpenPPI project status and execution checkpoint

**Checkpoint date:** 2026-08-08

**Execution environment:** NAISS Arrhenius; every scientific operation must run
through the pinned ARM64 Apptainer image

**Scientific programme state:** `DEC-0022` split, `DEC-0024` pair protocol,
and `DEC-0026` pair artifacts are accepted and immutable; development release,
protected evaluation, and all model work remain unauthorized

The authoritative gate is `governance/gates/gate_status_v25.yaml`.

## Accepted frozen package

`DEC-0026` accepts `pair_level_pu_r_benchmark_artifacts_v1`. Construction ran
from clean commit `043bd73f4b0e6d102b339b5ac66213a88674bb94`;
independent validation ran from clean commit
`7dc5e0ea1bfb87526178d569350bdb4d86c15559` and passed 13 checks with
zero warnings and zero failures.

The package contains:

- 16,799 public training positives and 2,000,000 public training-unlabeled rows;
- 26,108 encrypted development primary/source positive rows and 9,000,000
  encrypted development-unlabeled rows;
- 9,028,821 separately encrypted protected-candidate rows;
- 28,821 separately encrypted protected-truth positive rows, 9,000,000
  protected sampled-unlabeled rows, and the complete 58,049-row role ledger;
  and
- exact cell/stratum allocations, sampling hashes, reduced rational inclusion
  probabilities and weights, table/archive/ciphertext hashes, and manifests.

The package manifest SHA-256 is
`f0f850daf795481c8a1ae0ba64f6d050ae757f2738497ac0517003c6822015f5`.
The construction and validation report hashes are
`878beb38af78157b8b4b3ff50cb7658266900add86a96d7d9e5baca8745c3f65`
and `7eede006ba18dbc4dcc71128743722718bc73f0f6891834ad4ebc0a6ed614e86`.

## Independent validation disposition

The validator independently reconstructed all roles, source-specific cells,
129,614,029 cell-specific unlabeled opportunities, and every one of the
20,000,000 sample rows. It proved each bottom-hash boundary, stratum,
probability, weight, and protected candidate assignment.

There were zero positive-as-unlabeled rows, zero primary role overlaps, zero
training/evaluation endpoint leakage, zero missing/extra/duplicate protected
candidates, and zero protected identities in public workflows.

Cross-cell unlabeled reuse remains prespecified: 3,778,512 pair identifiers
recur across independently keyed cells. Reuse is explicitly recorded and is
neither positive-evidence leakage nor negative evidence.

## Protected custody

Training is the only public pair package. Development remains encrypted until
a future training-artifact hash and release are separately authorized.
Protected candidates and truth use distinct keys. Candidate identities cannot
be public because public sampler information would permit truth inference by
set difference.

A later protected submission must be a frozen scorer executed in a no-network
evaluator. The scorer sees only `candidate_token`, the two endpoint sequence
hashes, and `cell_id`. Predictions are complete/unique/finite, frozen, and
hashed before an exclusive one-first ledger reservation and truth decryption.
Only aggregate receipts may leave the evaluator.

No development package, protected candidate, protected truth, prediction, or
metric was opened or produced in this work package.

## Binding semantics and claims

Unreported eligible pairs remain unlabeled, not negatives. C3 means only both
exact frozen sequence endpoints absent from interaction-supervised training
and component-disjoint under 30% `local_domain_union`. It does not mean unseen
biological family, family generalization, unseen domain, PLM-unseen protein,
or exhaustive nonhomology.

Primary future metrics remain released-positive PU retrieval statistics, not
biological precision, prevalence, calibration, or binding probability. Exact
full-universe rank/Recall metrics remain demoted without later exact streaming
full-universe scoring.

## Immutable parents and panels

The 17,000 endpoints, 7,782 hard-rule components, and
11,900/2,550/2,550 training/development/test assignments accepted by
`DEC-0022` are unchanged. `DEC-0024` rules are unchanged.

The TF-isoform and Lambourne panels remain external-only and unused. The
TF-isoform panel remains unsuitable for training negatives or any training
role, universal-nonbinding claims, prevalence, calibration, and
unseen-endpoint/family benchmarking.

## Qualification note

One curator-only quarantine pair hash appeared in a transient preproduction
validator exception before identity-safe errors were completed. It was not a
training, development, or protected-test positive, was never versioned or
admitted to model development, and remains quarantined. Identity-safe
exceptions were regression-tested before the successful full reruns.

## Binding hold

No next work package is authorized. The following remain prohibited:

- modification, extension, resampling, or relabeling of the accepted package;
- development release or protected candidate/truth access;
- additional pair rows, samples, negatives, or pseudo-negatives;
- full candidate-pair universe materialization;
- modification of the frozen endpoint/component skeleton or protocol;
- external-panel integration or structural-label work;
- prevalence, probability, biological-precision, calibration, unseen-family,
  PLM-unseen, or exhaustive-homology claims; and
- model implementation, embedding, training, tuning, selection, evaluation,
  routing, or release.

Any continuation requires a new numbered authorization.
