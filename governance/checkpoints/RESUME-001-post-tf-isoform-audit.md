# RESUME-001: Post-TF-isoform-audit execution checkpoint

**Checkpoint written:** 2026-08-04, after the completed audit was committed and
pushed

**Reason for pause:** Project-owner request due to the Codex weekly usage limit

**Required state:** Stop here. Do not begin the sequence-component audit until
the project owner explicitly asks to resume after the usage limit refreshes.

## 1. Exact repository state at the pause

The completed TF-isoform audit was pushed to `origin/main` before this
checkpoint was written.

- completed-audit commit:
  `6156f21c7271b4d7f57f5b759bf33d6ad4d700e5`;
- production implementation commit:
  `9de608ddc301d0af548d043c9fbd57b5c7e1b7f2`;
- audit authorization commit:
  `4a36e93c332281bfed9c69d4206fc090cebd044b`;
- pinned SIF SHA-256:
  `72e4a13299df1c7036dbf5c8845f3a1d9d02bf6143bd2e4ee675aabd03112629`.

At audit push time, local `main` and `origin/main` both resolved to
`6156f21c7271b4d7f57f5b759bf33d6ad4d700e5`, and the worktree was clean. The
commit containing this checkpoint is the one immediately after that audit
commit and has subject `Record post-audit resume checkpoint`.

No file, script, configuration, staging dataset, canonical dataset, or report
for `benchmark_eligibility_and_sequence_component_audit_v1` existed at this
pause. That work package is **not started**.

## 2. Completed work that must not be repeated

The bounded Lambourne et al. 2025 TF-isoform Y2H/N2H audit is complete.

- scientific report:
  `docs/reports/m0/M0_TF_Isoform_2025_Y2H_Semantics_and_Contamination_Audit_Final_v1.md`;
- production audit:
  `artifacts/validation/tf_isoform_y2h_audit_v1/AUDIT_REPORT.json`;
- independent validation:
  `artifacts/validation/tf_isoform_y2h_audit_v1/VALIDATION_REPORT.json`;
- proposed disposition:
  `governance/decisions/DEC-0016-propose-tf-isoform-y2h-disposition.md`;
- authoritative gate:
  `governance/gates/gate_status_v15.yaml`;
- project status:
  `governance/PROJECT_STATUS_v15.md`.

Immutable verification values:

| Object | SHA-256/result |
|---|---|
| Production audit report | `9235569bd40adc4114c0b1f4387e57fb4fcabc823a28a3509676607ef809a281` |
| Independent validation report | `af9297e54203b7486a883eaa555d006dfac57da232f475f165395cf888f42327`; 26 pass, 0 warning, 0 fail |
| Staging manifest | `49221d602c1f2d966c451985604538c045fa9ffa8744363c35824aade7a9bffc` |
| Canonical manifest | `c71de2354bacfdef43b35d7f0ecbe07851568ab4abeb6a23df7065f1d8c39b68` |
| Acquisition manifest | `1c163f8cafaad152a49cc002af66a26a0779e9387a7cc9c3fca6bfaa56f60e96` |
| Raw verification | `59c4536b3ed07f2c78349a7adbd52dce48c9ddd4e2b609d0a8440b6656ba9bf2` |
| Final targeted tests | 25 passed |

Disposition: **external-only diagnostic candidate**, quarantined and not
currently suitable for protected benchmark integration. Do not rerun source
acquisition, reconstruct the audit again, alter its immutable Parquet files,
or resume the earlier sequence audit from any intermediate assumption.

## 3. Mandatory resume preflight

When the project owner explicitly says to resume, perform these checks before
any edit or scientific execution:

1. Read this checkpoint, `PROJECT_STATUS_v15.md`, `gate_status_v15.yaml`,
   `DEC-0012`, `DEC-0015`, and `DEC-0016`.
2. Run `git fetch origin` and verify local `main` equals `origin/main`. Do not
   discard or overwrite user changes if the worktree is not clean.
3. Verify the current HEAD includes the checkpoint commit whose subject is
   `Record post-audit resume checkpoint`.
4. Verify the SIF path
   `containers/images/ipin-data-arm64_0.1.2.sif` and its SHA-256 above.
5. Verify the four production sidecars in the audit, staging, and canonical
   directories. Do not overwrite the immutable validation report.
6. Confirm no later governance decision changed the accepted PU-R policy or
   the sequence-component work-package scope.

Useful read-only verification commands from the repository root are:

```bash
git status --short --branch
git rev-parse HEAD origin/main
git log -3 --format='%H %s'
sha256sum containers/images/ipin-data-arm64_0.1.2.sif
(cd artifacts/validation/tf_isoform_y2h_audit_v1 && sha256sum -c AUDIT_REPORT.json.sha256 && sha256sum -c VALIDATION_REPORT.json.sha256)
(cd data/staging/tf_isoform_y2h_audit_v1 && sha256sum -c STAGING_MANIFEST.json.sha256)
(cd data/canonical/tf_isoform_y2h_audit_v1 && sha256sum -c AUDIT_MANIFEST.json.sha256)
```

## 4. The one work package to resume

Resume only the previously authorized
`benchmark_eligibility_and_sequence_component_audit_v1`. Its controlling
sources are:

- `configs/benchmark_estimand_policy_v1.yaml` (`accepted_effective`);
- `docs/blueprints/iPIN_OpenPPI_Blueprint_Amendment_001_PU_Compatibility_Primary_Design_v1.md`;
- the incorporated detailed first-work-unit specification in
  `docs/blueprints/iPIN_OpenPPI_Blueprint_Amendment_001_PU_Compatibility_Primary_Design_PROPOSAL_v1.md`, section 16; and
- authorization in `governance/decisions/DEC-0012-accept-negative-evidence-discovery-audit.md` and `governance/gates/gate_status_v11.yaml`.

The authorized sequence is exactly:

1. freeze eligibility fields, source versions, hashes, schema, and deterministic
   tool parameters;
2. enumerate usable frozen reference-sequence Space III proteins;
3. report every mapping exclusion and ambiguity without imputation;
4. compute the exact unordered candidate count algebraically, without
   materializing candidate-pair rows and without calling that count “tested”;
5. construct and validate deterministic 40%, 30%, and 20% sequence-identity
   components using the governed bidirectional coverage rule;
6. report only aggregate eligible-positive mapping coverage, exclusions,
   component sizes, and feasibility needed for a later gate;
7. independently validate all consequential counts and components; and
8. return to governance before anything downstream is constructed.

Start with a read-only inventory of the accepted policy, frozen UniProt and
primary-reconciliation manifests, available clustering tools in the pinned
SIF, and existing benchmark module conventions. Then prepare the new
governance-bounded configuration/schema/tests before the first production
artifact. Do not infer missing eligibility rules; resolve them from the
accepted policy and frozen local evidence.

## 5. Prohibitions that remain binding on resume

The resumed unit must not:

- materialize the Space III candidate-pair universe;
- construct positive/unlabeled or negative evidence indicators;
- use Lambourne 2025, Lambourne 2026, Negatome, or IntAct-negative outcomes as
  training labels;
- merge external-panel outcomes with Negatome;
- create pseudo-negatives, C1/C2/C3 assignments, partitions, or train/dev/test
  splits;
- construct structural mappings or structure-derived training labels;
- implement, train, tune, calibrate, threshold, select, or route models;
- change the accepted primary PU-R design;
- interpret any negative observation as universal nonbinding; or
- claim experimental validation.

All scientific commands must run on Arrhenius through the pinned ARM64
Apptainer image. Keep raw, staging, canonical, validation, report, and
governance layers separate and return to the gate after this one bounded work
package.

## 6. Resume instruction to the future agent

When the user says “resume from the checkpoint,” do not ask them to restate the
project history. Verify section 3, state that the sequence-component audit is
still unstarted, and continue from section 4. Do not perform any further work
in the session that created this checkpoint.
