# iPIN-OpenPPI project status and restart checkpoint

**Checkpoint date:** 2026-08-04

**Execution environment:** NAISS Arrhenius; scientific computation must run
through the pinned ARM64 Apptainer image

**Scientific programme state:** Lambourne human Y2H pair-semantics audit
authorized and in progress; sequence-component audit paused and unstarted

The authoritative gate is `governance/gates/gate_status_v12.yaml`.

## Accepted baseline

All work accepted through `DEC-0012` remains binding. In particular, the
negative-evidence audit is complete, PU-R remains the primary design, and no
audited negative record has a universal-nonbinding meaning or an authorized
training-label role.

## Active work package

`DEC-0013` authorizes only a governance-bounded audit of Lambourne et al. 2026
human Y2H-v1 evidence. The active source index is
`data/source_manifests/PREACQUISITION_INDEX_v5.yaml`; the policy is
`configs/source_policy_v3.yaml`; and the license decision is
`governance/licenses/SOURCE_LICENSE_REGISTER_v6.md`.

The work must acquire and freeze the paper source data, Zenodo record 19118078
v2.1 code/input archives, and official IMEx IM-30553 preview. IM-30553 is
curated but not integrated into services, so it remains a dated preview and is
not IntAct Release 252.

Required outputs are:

1. exact reconstruction of all 4,100 originally selected pairs and the 3,222
   final-analysis pairs;
2. exact positive, negative, `NA`, and technical/evaluability accounting;
3. source-faithful construct, bait/prey, sequence-confirmation, assay, species,
   publication, and condition provenance;
4. deterministic mapping to frozen human UniProt 2026_02;
5. overlap with HuRI, frozen IntAct positive/negative evidence, Negatome, and
   other currently permitted direct-PPI evidence;
6. pair and sequence-family contamination diagnostics without constructing
   benchmark splits;
7. protected assay-specific external-benchmark feasibility and claim-
   identifiability analysis; and
8. immutable manifests, independent validation, tests, scientific report, and
   a governance proposal.

## Exact restart point

The source-policy, license, and preacquisition package is being frozen before
download. After acquisition, proceed through raw integrity validation,
representation reconciliation, staging, canonical pair audit, independent
validation, and reporting. Return to governance before any benchmark
integration.

The previously authorized
`benchmark_eligibility_and_sequence_component_audit_v1` remains
**paused and not started**. Resume it only after the Lambourne governance
disposition, preserving its original scope and prohibitions.

## Binding prohibitions

- Do not use Lambourne outcomes as training labels or merge them with Negatome.
- Do not construct benchmark splits, candidates, evidence labels, or models.
- Do not treat `NA`, technical failure, absence, or unreported pairs as negative.
- Do not infer universal nonbinding from any negative outcome.
- Do not collapse bait/prey orientation, constructs, isoforms, or
  sequence-confirmation states.
- Do not present IM-30553 preview exports as Release 252.
- Do not imply experimental validation by this computational project.

## Execution discipline

Keep raw, staging, canonical, validation, report, and governance layers
separate and versioned. Begin production units from a clean tracked Git state,
record the exact implementation commit and container digest, and keep all raw
scientific payloads outside Git under the source-specific release boundaries.
