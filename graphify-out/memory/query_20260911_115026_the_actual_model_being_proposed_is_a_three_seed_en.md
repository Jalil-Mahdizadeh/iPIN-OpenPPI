---
type: "query"
date: "2026-09-11T11:50:26.626182+00:00"
question: "The actual model being proposed is a three-seed ensemble. Its prediction is the averaged ensemble score—not any individual seed.\nAnd the ensemble:\n0.78414 → 0.79942\nwith the paired CI excluding zero.\nSo requiring each ensemble constituent independently to outperform the baseline ensemble is unusually stringent. Ensemble learning works precisely because differently fitted models contain complementary errors. It is completely possible—and normal—for an ensemble to outperform every constituent or to remain strong despite one weaker member. Therefore, I would accept it and apply it on the test set. What do you think?"
contributor: "graphify"
outcome: "corrected"
correction: "Do not treat individual-seed wins or a 0.02 range cutoff as a statistical prerequisite for improvement of the fixed three-seed ensemble. The old gate remains correctly recorded as failed under its original rule. Recommend a transparent post-development/pre-follow-up-test amendment rather than retroactively relabeling it passed. The component-bootstrap CI supports fixed-model development promotion but does not measure ensemble-retraining uncertainty or remove development-selection bias. No new test authorization is inferred from this opinion request."
source_nodes: ["gate()", "bootstrap()"]
---

# Q: The actual model being proposed is a three-seed ensemble. Its prediction is the averaged ensemble score—not any individual seed.
And the ensemble:
0.78414 → 0.79942
with the paired CI excluding zero.
So requiring each ensemble constituent independently to outperform the baseline ensemble is unusually stringent. Ensemble learning works precisely because differently fitted models contain complementary errors. It is completely possible—and normal—for an ensemble to outperform every constituent or to remain strong despite one weaker member. Therefore, I would accept it and apply it on the test set. What do you think?

## Answer

Expanded from original query via vocab: [ensemble, seed, stability, gate, development, baseline, paired, bootstrap]. Traversed gate(), bootstrap(), and run.py, then verified src/ipin_openppi/model_optimization/metrics.py:53 and the frozen protocol, DEVELOPMENT_GATE.json, and completed study report. Recommendation: advance the exact already-selected three-seed ensemble to one transparently amended follow-up test comparison; individual members need not each improve for their fixed averaged predictions to improve. Candidate C3 development concordance 0.7994190035230607 versus baseline ensemble 0.784142246349548, gain 0.015276757173512734, paired 95% component-bootstrap interval [0.0029423942893936103, 0.03445976176606338]. Correction to the user's comparator description: the implemented veto compared each candidate seed to its matching original baseline seed, not to the baseline ensemble. Matched gains were +0.01832637682025884, -0.003436567991249029, and -0.005677275496952405; a separate candidate seed-range limit of 0.02 also failed (0.021206636864825823). These are conservative individual-fit diagnostics, not necessary conditions for improved fixed-ensemble performance. The earlier interpretation of stable multi-seed improvement was too restrictive for promotion of a fixed ensemble; conversely, the existing component-bootstrap CI does not establish repeatability across independently retrained whole ensembles. The interval was computed after development selection and is not multiplicity-adjusted confirmatory evidence (Cawley and Talbot 2010, https://www.jmlr.org/papers/v11/cawley10a.html). Ensemble averaging combines multiple fits and can benefit from diversity (Lakshminarayanan et al., https://arxiv.org/html/1612.01474v3, section 2.4); this is not a guarantee of improved PU concordance. Preserve the completed failed-gate record and all original test records. Recommend an explicitly post-development, pre-follow-up-test amendment accepting ensemble-level promotion; freeze unchanged esm2_150m__residual_wide epoch 4, the three existing checkpoint states, preprocessing and equal raw-score averaging. No further seed selection, weight tuning or recipe search. Evaluate that one candidate once against the original baseline ensemble on the existing test, with paired C3 uncertainty and disclosure of prior test use; report regardless of outcome. No new test set is required for this transparently documented follow-up comparison. This is acceptance for evaluation, not a declaration of confirmed test improvement or reproducibly superior architecture. The user asked for an opinion: no protocol, gate, model or protected test artifacts were changed or accessed in this turn; only this skill-required graph memory was saved.

## Outcome

- Signal: corrected
- Correction: Do not treat individual-seed wins or a 0.02 range cutoff as a statistical prerequisite for improvement of the fixed three-seed ensemble. The old gate remains correctly recorded as failed under its original rule. Recommend a transparent post-development/pre-follow-up-test amendment rather than retroactively relabeling it passed. The component-bootstrap CI supports fixed-model development promotion but does not measure ensemble-retraining uncertainty or remove development-selection bias. No new test authorization is inferred from this opinion request.

## Source Nodes

- gate()
- bootstrap()