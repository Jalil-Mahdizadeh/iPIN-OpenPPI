# DEC-0039: Accept development evaluation and stop complex-model claim

**Date:** 2026-08-19

**Status:** Accepted and effective; the development work package is closed,
the complex-model claim is stopped, and protected evaluation is prohibited

**Controlling records:** `DEC-0028`, `DEC-0032`, `DEC-0033`, `DEC-0035`,
`DEC-0037`, `DEC-0038`, gate v37, and the completed-evaluation registry with
SHA-256
`42aa8b19c4c5cfaf36bfbe1bd19bdf74e7de81df27cccb793809a5ec80d0e189`

## Decision

Accept the complete development-only release, scoring, evaluation, production
audit, and clean-room independent validation. Adopt the exact frozen
disposition:

**stop the complex-model claim and stop before protected evaluation.**

No frozen scorer advances toward protected evaluation. Simple graph, length,
3-mer, and interolog controls are retained only as frozen explanatory evidence,
not as a protected-evaluation model. This decision supplies no protected
candidate, truth, private-key, scoring, or metric authority.

## Accepted execution and custody

Accept that:

1. development was decrypted exactly once after the independently validated
   prerelease gate passed;
2. all nine development cells were scored on 9,026,108 rows using exactly nine
   deterministic controls, 30 frozen selected checkpoints, and ten frozen
   three-seed ensembles;
3. no training, retraining, tuning, checkpoint change, scorer change, ensemble
   change, negative or pseudo-negative construction, or protocol change
   occurred;
4. all primary C3, C2, and C1 metrics, 2,000-replicate paired component
   bootstrap intervals, source-exclusive diagnostics, degree/hub strata,
   correlations, seed ranges, and C1 novel-U sensitivity were computed under
   the frozen rules;
5. public artifacts contain aggregate evidence only and no development pair
   identity; and
6. protected candidates, protected truth, and their private keys remained
   sealed and unaccessed.

The immutable development results manifest has SHA-256
`e6b5455e3c1e0346b5b9c9a358db7abc628732b57bab2ec778992d2fbe9c8299`.
The selection and kill trace has SHA-256
`ac583545f2dd3c8305dc477cb2d414e75a31800afcb29ddaedc6276cab165c45`.

## Accepted scientific result

In C3, the best complex candidate is the 650M partner-gated no-dropout
ensemble at `0.49134652604741336`, with percentile-95 interval
`[0.4622492977197828, 0.5372847754287488]`. Its exact deltas are:

- `-0.15333611147533133` versus within-pair 3-mer, interval
  `[-0.2459824782324954, 0.019318960348454824]`;
- `0.006206836644593983` versus 650M linear, interval
  `[-0.043158071185191056, 0.050104062093720605]`; and
- `0.014917351434742432` versus matched no-gate, interval
  `[-0.0017786841786421868, 0.03245385852354833]`.

The last point estimate clears the raw `0.005` magnitude but its interval does
not exclude zero. All other required complexity comparisons fail. HI-II-14 and
HuRI C3 source deltas against the strongest simple comparator are respectively
`-0.23262459775331246` and `-0.1406427868176625`; the outside-top-10%-hub
delta is `-0.15333611147533133`.

The strongest diagnostic patterns are simpler: C3 sequence-length ratio,
within-pair 3-mer, and exact interolog concordances are respectively
`0.6608800512102514`, `0.6446826375227447`, and `0.635701358715407`; C2
training-degree sum is `0.8392632813073615`; and C1 preferential attachment is
`0.9069423975969924`. Every PLM ensemble is near chance in C2 and C1. The
prespecified C1 novel-U view leaves the best-complex deficit essentially
unchanged.

The frozen decimal-`0.001` selection cascade mechanically selects
`lightweight_esm2_150m_linear__linear_lr3e-4`. Accept that this selection does
not override the model-level kill criteria and creates no advancement
authority.

## Exact complexity and kill determination

Reject retention of the partner gate. Reject a supported nonlinear-head or
650M-scale claim. Accept that the following frozen model-level criteria fire:

- best-complex C3 lower bound not above `0.5`;
- no complex C3 gain of at least `0.02` with a positive paired interval;
- interolog or frozen-PLM-linear explanation of the complex C3 result;
- absence of gain outside top-10%-hub pairs; and
- shortcut explanation of C1 without qualifying learned C2 or C3 gain.

The execution-integrity, custody, U-as-negative, post-release-training, and
protected-boundary kill flags remain false. The stop is the exact scientific
outcome required by `DEC-0028`, not an integrity failure.

## Validation basis

Accept the corrected completed production audit at SHA-256
`1724a645e39ec232827aa8d1a8b6142fd257ec9404f133e985f2330e15e073ba`.
It passed 9 of 9 checks.

Accept the standalone clean-room validation at SHA-256
`0d3bc35047bd8971177dbe148d1f5a4bbe515ba6d396552e6f3f3cf49f11039e`.
It was implemented only after production evidence was committed, imports no
production development-evaluation module, and passed 16 of 16 checks. It
rehash-verified all 57 registered files; exactly recomputed 81,234,972
deterministic and 270,783,240 checkpoint score values at maximum absolute
difference `0.0`; checked swap symmetry and all ensemble values; and
independently reproduced every consequential metric, bootstrap, stratum,
novel-U, selection, complexity, kill, and information-flow result.

Accept the final report
`docs/reports/m1/M1_Development_Release_and_Evaluation_Final_v1.md` as the
human-readable scientific record. Its frozen hash shall be recorded in the
post-decision checkpoint.

## Incident closure

Close `ISSUE-0009`, `ISSUE-0010`, and `ISSUE-0011` for this work package.
Accept that each incident failed closed; received a narrowly scoped numbered
authorization; preserved failed evidence; added a regression; and passed
production plus independent requalification. None changed a score, metric,
bootstrap draw, candidate, threshold, benchmark semantic, or scientific
disposition.

## Closed boundary

`DEC-0032` is fulfilled and closed. There is no active executable model work
package. Protected evaluation is not authorized and may not be proposed as an
automatic next step because the frozen stop criterion fired.

Any future scientific programme must begin with a new prospective protocol and
numbered decision. It may not access or reinterpret protected packages under
this stopped claim; retrain on development; tune a frozen scorer; alter the
benchmark, PU-R protocol, or kill thresholds; introduce negatives or
pseudo-negatives; or add an external panel, structure, residue, or interface
model under the closed work package.
