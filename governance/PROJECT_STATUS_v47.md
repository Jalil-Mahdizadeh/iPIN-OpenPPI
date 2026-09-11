# iPIN-OpenPPI status: signal survives internal homology/source challenges

Date: 2026-09-11. Authority: DEC-0047.
Supersedes `governance/PROJECT_STATUS_v46.md` for the new bounded work only.

The homology/source challenge is executed and numerically verified. All four
prespecified anchor-ranking challenges pass: original union plus stronger
interaction-transfer controls, remote-homology-purged refits, HI-II-14→HuRI-only
and HuRI→HI-II-14-only refits. Pair-head concordance is respectively 0.663612,
0.657382, 0.593449 and 0.623196. Gains over linear-unary controls are 0.079409,
0.073490, 0.047688 and 0.039812, all with positive paired conditional 95% lower
bounds. All four transfer-control paired lower bounds are positive in every arm.
Every fold and seed beats linear unary. Direct older controls remain visible;
not every new transfer control is empirically stronger than those older scores.

Three swap challenges pass. HuRI→HI-II-14's swap result is **inconclusive**:
only 66 inherited quartets, below per-fold support floors, with preference
0.560606 and interval [0.158668, 0.952464]. The global protocol therefore does
not pass in full. It is not an explanation-away of the anchor signal.

The new search finds 344 >=30%-identity local links across original internal
folds (and nine at >=40%). ISSUE-0015 records the limitation of the frozen
heuristic leakage graph. The prespecified >=20% purge removes whole fitting
components and leaves zero detected direct qualifying cross-links per fold.
Its signal is largely retained; no original component assignment is modified.

Source annotations were projected only onto the 16,799 already released public
P pairs from allowlisted pre-benchmark archives. No evaluator source package,
role ledger, development/protected candidate/truth or key was accessed.
Target-only public P is reinserted as U in source-limited fitting, not silently
excluded using target labels. Upstream source-union curation, shared programme/
Y2H methods and missing complete assay-opportunity logs still limit inference.
Source restriction and homology purging were not tested jointly. HI-II-14-only
training substantially lowers HuRI-only recovery relative to union training;
source invariance is not established.

Verification: 54 new fits; 390 distinct tests covered across qualified CPU/GPU
runs; all 16,168,200 learned values checked by separate NumPy forwards; all four
full similarity matrices, source annotations, fitting masks, point metrics and
specified uncertainty checks pass. Maximum forward difference is 4.29523e-6.
The supporting arithmetic audit passes. A pre-fit FP32 accumulation issue was
fixed using FP64 accumulation with unchanged tolerance; original evidence is
preserved. All validation is same-author numerical auditing, not external review.

This is stronger internal ranking evidence, not proof of physical specificity,
source/laboratory independence, unseen families or architecture novelty. The
old gating/complexity stop and protected-evaluation hold remain. Next priority
is independently assembled source/assay-aware evidence, not a model sweep.
No additional experiment, protected access, data acquisition or remote push is
authorized automatically by these results.

Report: `docs/reports/m1/M1_Homology_and_Source_Challenge_v1.md`.
Readout: `artifacts/results/homology_source_challenge_v1/RESULTS.json`.
Ledger: `governance/gates/gate_status_v47.yaml`.
