# DEC-0033: Accept development pre-release qualification and activate release

**Date:** 2026-08-19

**Status:** Accepted and effective only for the one-time development release
and frozen-scorer evaluation already authorized by `DEC-0032`; protected-test
access remains prohibited

**Controlling records:** `DEC-0028`, `DEC-0031`, `DEC-0032`, gate v31, and the
complete training-artifact registry with SHA-256
`11d7a92d6dd42ca78434783844cbba2ffb05ac789b76eca4399528d0d19ab318`

## Decision

Accept the production and independent pre-release qualification of the exact
development-only release, scorer, metric, diagnostic, selection, and kill-rule
implementation. The precondition in `DEC-0032` is satisfied. Activate exactly
one decryption of the frozen development package with the development key,
followed only by scoring and evaluation of the frozen 49-scorer census.

This acceptance does not alter `DEC-0028`, authorize a new scorer, permit
training or tuning, or open any protected candidate, protected truth, or
protected private key.

## Accepted implementation and evidence

The production implementation was frozen at commit
`21aa040484eec533a8f519f1e70c11a817317ba7`. Its no-key production audit was
frozen at `9e17cfa0ac3e2654c80dfc176c0b45e35a1f0d50` and passed 12 of 12 checks.
The clean-room validator, which imports no production development module, was
implemented only afterward and frozen at
`34aecb77bebc69ebb5d8423f74b24ca7536496a0`. Its passing evidence was frozen
at `66e9126a5914cd7fdc5c62324823998c92c22ab2`.

Accept these evidence hashes:

| Artifact | SHA-256 |
|---|---|
| Production pre-release audit | `609de99b92e4b4be56a98b61823618056be1cb8bf156cbe51c273f505a0c7ad9` |
| Independent pre-release validation | `146d06a689b6ccb473b663db50675b1fc660a9fd11921e6965c9b6007ce50395` |
| Execution projection | `d74c683bbeb57e8b455efc789f487ca20df7a128ab0ec27b317dc602eda3e57d` |

Together the validators independently established:

1. exact authority, runtime, public-input, embedding, training-registry,
   checkpoint, ensemble, and sealed-ciphertext hashes;
2. exactly nine mandatory controls, 30 training-selected checkpoints, and ten
   three-seed arithmetic ensembles;
3. score-only algebra for all four frozen families, exact swap symmetry, no
   optimizer/training path, and unchanged checkpoint state;
4. exact HT concordance with half ties, PCG64DXSM component draws, distinct-
   and same-component pigeonhole multipliers, paired bootstrap arithmetic,
   interolog max-min identity, selection quantization, strata, sensitivity,
   complexity, and kill-rule thresholds;
5. a resolver that admits only
   `.private/pair_level_pu_r_benchmark_artifacts_v1/development_release_private.pem`,
   performs no private-key enumeration, and cannot resolve either protected
   private key; and
6. no development plaintext, development private-key, protected private-key,
   protected-candidate, or protected-truth access during qualification.

## Activated release boundary

Authorize one decryption of
`data/canonical/pair_level_pu_r_benchmark_artifacts_v1/sealed/development_release.cms`
at SHA-256
`bbbd07472da621a34f45e95ab4b51c799fa0fc967d94de2aa3578e0cda0c1d41`.
The decrypted deterministic archive must hash to
`c8d1520d5dbc5b435a1ed5149cbd2f9a731fb3cee10cd651dd0a19b475741122`.
Plaintext and scores remain under `.private/`; only aggregate counts, metrics,
hashes, and custody receipts may enter governed public evidence.

The release must fail closed before key resolution if either qualification
report, authority, registry, ciphertext, certificate, or activation-gate hash
drifts. A pre-existing release target prohibits a second decryption.

## Required execution and return

Execute all nine development cells with the exact 49 scorers, freeze the
private score artifacts and public hash registry, calculate the frozen C3-first
metrics and diagnostics, apply every complexity and kill rule, then commit
production evidence before implementing the independent completed-evaluation
validator.

Return to governance with exactly one disposition permitted by `DEC-0032`:
advance a fully frozen eligible scorer toward a separately authorized protected
evaluation, retain only the simplest eligible baseline, or stop the complex-
model claim (and stop before protected evaluation when a kill criterion fires).

## Continuing prohibitions

Protected candidates, protected truth, either protected private key, protected
scoring, training, retraining, checkpoint change, model/recipe/seed addition,
tuning, adaptive criteria, negative or pseudo-negative construction, benchmark
change, full-universe materialization, external panels, structures, residue or
interface modelling, and probability/prevalence/calibration or unsupported
transfer/exposure claims remain prohibited.
