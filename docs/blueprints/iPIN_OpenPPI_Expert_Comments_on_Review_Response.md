# iPIN-OpenPPI

## Expert-Group Comments on the Response to the Independent Technical Review

### Scientific assessment, remaining issues, feasibility, and recommended Version 3 actions

**Prepared for:** The iPIN-OpenPPI expert working group  
**Date:** 3 August 2026  
**Status:** Independent discussion document

---

## Executive assessment

The response to the independent technical review is scientifically mature, candid, and largely correct. It accepts the review's principal findings instead of attempting to defend every element of the original blueprint. In doing so, it moves iPIN-OpenPPI from an ambitious but statistically under-specified concept toward a credible staged research programme.

The response is particularly strong in four respects:

- it abandons the claim that the first model can directly estimate one universal, context-free biochemical interaction probability;
- it adds assay false positives and recognizes identifiability as a central research risk;
- it replaces partner-independent interface routing with partner-conditioned joint patch-pair routing; and
- it removes several attractive but nonessential branches from the initial critical path.

The document should be circulated to the expert group as a strong discussion draft. It should not yet be treated as the final Version 3 execution plan. Most of the scientific direction is now sound, but several critical concepts remain expressed as principles rather than operational definitions, measurable gates, assigned work packages, or funded commitments.

> **Recommended decision:** Accept the response as the basis for Version 3 and approve a conditional six-month de-risking phase. Do not authorize the complete 24-month programme until the target, assay, candidate universe, numerical gates, staffing, compute allocation, and experimental protocol have been fixed in an operational appendix.

---

## 1. Resolution assessment

| Review issue | Response assessment | Remaining requirement |
|---|---|---|
| Universal intrinsic interaction probability | **Partially resolved** | The universal claim is correctly rejected, but the replacement estimand and reference context are not yet fixed. |
| Assay false positives | **Resolved in principle** | The sensitivity/specificity equation is appropriate; its estimability and parameter-sharing assumptions still require tests. |
| Non-random pair selection | **Partially resolved** | Systematic screens are correctly prioritized, but selection and technical assay success remain combined. |
| Context-dependent binding | **Mostly resolved** | The response recognizes context-dependent binding and a reference distribution, but does not define the initial context or distribution. |
| Statistical identifiability | **Strong response** | Nested baselines and a fallback are appropriate; recovery, prior stability, negative controls, and partial identification must be implemented. |
| Partner-independent routing | **Strongly resolved in principle** | Joint patch-pair routing is the correct revision; scaling, differentiability, leakage, and oracle gates still need operational details. |
| Overloaded multi-task scope | **Resolved directionally** | Deferrals are correct, but the reduced critical path still needs named owners, effort, dates, and dependencies. |
| C1/C2/C3 and strict benchmarks | **Mostly resolved** | C2 is corrected and a benchmark ladder is proposed; interface-audit confidence and full information cutoffs remain missing. |
| Negative-label semantics | **Strong response** | Conditional negatives and technical failures are handled conceptually; the data schema and likelihood treatment must be specified. |
| Licensing and redistribution | **Correctly accepted** | A source-by-source matrix must become an early deliverable rather than a general recommendation. |
| Arrhenius feasibility | **Plausible but unproven** | Hardware appears sufficient, but allocation, software qualification, throughput, storage, and scaling have not been demonstrated. |
| Prospective validation | **Correctly prioritized but not secured** | The final wording makes validation optional; a partner, protocol, throughput, budget, and decision endpoint are required. |

---

## 2. Primary target and output semantics

### 2.1 The response makes the right conceptual correction

It is correct to reject the original target of direct interaction "under some compatible biochemical condition" as the first calibrated probability claim. That existential target makes a universal negative almost impossible to establish. The proposed reference-distribution idea is scientifically coherent, and the decision to use a compatibility or prioritization score unless identifiability is demonstrated is appropriate.

### 2.2 The endpoint notation still contains an important inconsistency

Section 3 calls the following quantity an assay- and construct-conditioned "interaction probability":

`P(y = 1 | S_A, S_B, assay, constructs, orientation, recorded context)`

Section 4 then uses `y` as the observed assay result. An observed assay-positive probability is not identical to a direct-binding probability. Calling both quantities an interaction probability recreates, at the terminology level, part of the ambiguity that the response is intended to remove.

Version 3 should distinguish at least four states:

- `s`: whether a pair was selected or attempted;
- `e`: whether the attempt produced a technically evaluable result;
- `b_c`: whether direct binding exists in the specified biochemical context `c`; and
- `y`: the observed assay outcome.

The initial assay endpoint should therefore be described as:

`P(observed assay positive | selected, technically evaluable, sequences, constructs, assay, orientation, context)`

The project may separately estimate `P(b_c = 1 | sequences, context)` only where the context is defined and the evidence can identify that quantity. The general sequence-derived compatibility score should not be reported with probability language, Brier scores, or universal calibration claims until that interpretation has been justified.

### 2.3 The first reference context must be concrete

A universal reference distribution over biochemical conditions is unlikely to be defensible at the start. The pilot should instead name one systematic assay/search space and define its construct and context distribution. Expansion to additional assays can then test transportability rather than being assumed from the outset.

The expert group should decide before implementation:

- the primary organism;
- the initial interaction class;
- whether homomers are included or excluded;
- the systematic tested universe;
- the primary assay and construct system; and
- the candidate universe to which calibration statements apply.

The response's final use of "heteromeric" is a substantive narrowing that is not otherwise discussed. It may be the correct decision, but it must be explicit and justified rather than introduced only in the final programme statement.

---

## 3. Observation, selection, and identifiability

### 3.1 Adding specificity is essential and correct

The revised sensitivity/specificity observation equation is a substantial improvement. It allows observed positives to arise from artifacts, indirect bridging, mapping problems, contamination, autoactivation, construct-induced effects, or curation errors. Treating orthogonally supported records as high-reliability probabilistic anchors rather than deterministic truth is also appropriate.

### 3.2 Selection and successful testing should not share one variable

The response introduces `t_ABm` for a pair being "selected and successfully tested." These are different processes. A selected pair may fail during cloning, expression, purification, localization, sequencing, assay quality control, or construct verification. Such an outcome is neither an assay negative nor an untested pair.

The evidence model and warehouse should record separately:

1. membership in the intended search space;
2. selection or attempted testing;
3. construct availability and identity;
4. technical success or failure;
5. evaluable assay outcome; and
6. publication or database inclusion.

This separation is especially important if the project intends to learn assayability or correct selection bias. Otherwise, technical feasibility may be mistaken for biological compatibility.

### 3.3 The fallback is scientifically legitimate

The proposed nested-model comparison is excellent. The complete latent model must compete against assay-specific classifiers, matched-negative baselines, non-negative PU methods, hierarchical assay heads, and restricted reliability models on identical data and splits.

The latent model should proceed only if:

- synthetic experiments recover known parameters under comparable missingness;
- conclusions are stable under plausible assay and prevalence priors;
- repeated and cross-assay evidence is sufficient to constrain reliability;
- negative-control fits and label or identity permutations behave appropriately;
- improvements survive strict biological holdouts; and
- results are not primarily an assay-source classifier.

If point identification is unsupported, uncertainty or partial-identification intervals should be reported. Falling back to calibrated assay-specific prediction plus an evidence-integrated compatibility score would remain a strong scientific result, not a project failure.

---

## 4. Partner-aware sparse routing

The proposed architectural correction is persuasive. A protein can expose different domains, motifs, disordered regions, or surfaces to different partners. A router that sees each protein independently can learn general interface propensity, but it cannot reliably select the interface relevant to a particular partner. Joint patch-pair selection is therefore the appropriate hypothesis.

The proposed sequence of shared encoding, coarse multi-scale patches, partner-conditioned patch-pair scoring, sparse high-resolution cross-attention, a global path, and exact swap symmetry for the biological head is well designed.

Several operational points remain:

- the coarse patch-pair matrix is still quadratic in the number of patches;
- motif-scale plus domain-scale windows may create a large candidate set;
- hard top-k selection requires a defined training strategy;
- the selected patch budget and long-sequence complexity must be quantified;
- biological interaction symmetry should not be imposed on orientation-dependent assay-observation heads; and
- structural or predicted interface supervision must be generated within the permitted training partition.

The oracle experiments should be treated as genuine stop/go decisions. If oracle interface regions do not improve strict generalization, interface-local reasoning is probably not the principal bottleneck. If oracle regions help but learned routing does not, the proposer is the problem. Only if learned partner-aware routing captures a meaningful fraction of the oracle benefit and reduces long-pair cost should sparse routing remain on the critical path.

---

## 5. Benchmark, calibration, and model selection

### 5.1 Improvements correctly adopted

The response correctly makes C1, C2, and C3 exclusive, recommends separate benchmark axes, and reserves one combined stress test. It also correctly rejects the assumption that undocumented proteome pairs are verified negatives and ties calibration to a declared candidate universe, assay, retrieval policy, and prevalence.

### 5.2 Important benchmark controls still need to be restored

Version 3 should add the following elements from the independent review:

- interface-audit confidence classes: experimentally audited, computationally audited, sequence-audited only, and unknown;
- restriction of novel-interface claims to independently audited examples;
- complete temporal cutoffs covering source releases, sequence databases, PDB/templates, MSA databases, teacher versions, PLM corpora, text-mined sources, and candidate-generation rules;
- contamination reports at exact-sequence, homology-family, and interface levels;
- confidence intervals that account for repeated proteins, families, complexes, studies, interface families, and assay batches; and
- a hidden final test or otherwise protected final evaluation where operationally possible.

Sequence-cluster thresholds at 40%, 30%, and 20% should be sensitivity analyses around one prespecified primary threshold. They should not become interchangeable choices selected after results are known.

### 5.3 The primary metric is not yet chosen

The response agrees that one primary metric plus hard constraints should replace the composite geometric score, but it does not actually choose the metric. Before finalist comparison, the programme should define:

- one primary retrospective metric on a stated tested universe and prevalence;
- minimum precision and calibration requirements;
- the candidate budget at which retrieval and reranking are judged;
- secondary coverage, efficiency, mechanism, and uncertainty diagnostics; and
- a separate prospective primary endpoint, such as blinded top-k validation yield or uplift over a prespecified baseline.

Graph density, clustering, complex recovery, pathway coherence, and other network measures should remain secondary diagnostics. They must not be used as evidence that an individual novel pair is correct, because known interaction networks are incomplete and historically biased.

---

## 6. Evidence warehouse and label semantics

This is one of the strongest parts of both the original programme and the response. Construct-level provenance, conditional negatives, technical-failure categories, structural quality controls, and licensing can become durable contributions independent of the final neural architecture.

The Version 3 decision table nevertheless should not say that the evidence warehouse is adopted "unchanged." The concept is retained, but the schema must be revised to include:

- intended search-space membership;
- selection and assay attempt;
- technical success or failure;
- construct sequence, boundaries, isoform, tags, mutations, and orientation;
- assay and biochemical context;
- observed outcome and evidence reliability;
- source and release-date provenance;
- structural biological-assembly and interface-audit confidence;
- conflict and repeated-measurement links; and
- licensing and redistribution status.

The preferred wording is: **retain the evidence-record concept; revise and freeze the pilot schema before ingestion.**

A smaller warehouse with reliable construct mapping and a known tested universe is more valuable for the pilot than a much larger collection of canonical pairs with ambiguous provenance.

---

## 7. Uncertainty, retrieval, and graph claims

These points receive less attention in the response than they deserve.

### 7.1 Uncertainty must be demonstrated under shift

Average in-distribution calibration does not establish epistemic uncertainty or reliable abstention. Finalists should be tested for calibration and risk-coverage across unseen families, interfaces, assays, species, and sequence-similarity strata. The analysis should include deep-ensemble or comparable uncertainty baselines, corrupted or partner-swapped controls, and the relationship between abstention and prospective validation yield.

The terms "epistemic" and "aleatoric" should be used only if the modeling assumptions and empirical evidence support that separation.

### 7.2 Retrieval can limit the entire system

A reranker cannot recover a true partner that candidate generation never retrieves. The pilot should compare a global vector, multiple query/key projections, region or domain embeddings, and compact patch-level late interaction. Retrieval recall at the intended budget must be measured before reranker precision is interpreted.

### 7.3 Graph plausibility is not pair-level validation

Network diagnostics are valuable for detecting pathological outputs, but graph-constrained decoding should be reported separately from sequence-only pair scores. Agreement with the known graph can reward publication and research biases rather than biological truth.

---

## 8. Scope, staffing, and six-month feasibility

The response is right to defer mechanism experts, three-protein competition/cooperation, broad cross-study affinity regression, large custom PLM pretraining, and simultaneous structural and MSA teacher branches. These changes are necessary.

### 8.1 Minimum credible team

For the proposed six-month de-risking phase, a credible minimum is approximately:

- one dedicated evidence and benchmark engineer;
- two model researchers or research engineers;
- one curator or protein scientist with substantial protected time;
- named fractional statistical leadership;
- named fractional HPC/MLOps support; and
- a committed experimental team with agreed construct and validation capacity.

This is roughly four core internal FTE plus specialized support and external experimental effort. The complete original programme would still require approximately six to ten computational, biological, and experimental FTE to execute rigorously.

### 8.2 Conditions for a feasible six-month phase

The ten proposed month-six outcomes are feasible only if the following exist at kickoff:

- one identified systematic dataset with a known tested universe;
- timely data access and acceptable redistribution terms;
- an initial evidence ontology and construct-mapping workflow;
- a named assay and experimental partner;
- a usable Arrhenius allocation; and
- the core team working concurrently rather than sequentially.

Without these prerequisites, six months is optimistic. The statistical and routing pilots should not begin on moving data definitions. A sensible sequence is:

1. **Month 0-1:** scope, assay, tested universe, schema, licensing, ownership, and success criteria;
2. **Month 1-3:** evidence MVP, construct audit, frozen splits, simple baselines, and HPC qualification;
3. **Month 3-5:** identifiability experiments and retrieval audit on the frozen pilot;
4. **Month 4-6:** oracle, full-attention, and routing proof of concept; and
5. **Month 6:** independent gate review and a documented narrowing or continuation decision.

---

## 9. Prospective validation

Prospective validation is one of the programme's strongest potential differentiators. The phrase "validated prospectively where feasible" weakens that commitment and can be read as an escape clause.

A better formulation is: **prospective validation will proceed under a prespecified protocol if the evidence, retrieval, model, compute, and assay-readiness gates are passed.**

Before candidate selection, the protocol should define:

- frozen model weights, data, and candidate-generation rules;
- the organism, search space, and candidate budget;
- positive, negative, uncertainty, and assay-performance controls;
- construct design and orientation rules;
- technical-failure handling;
- primary and orthogonal assays;
- sample size or precision objectives;
- blinding or other bias control where feasible; and
- the primary endpoint and analysis plan.

Experimental design and construct feasibility work must start at programme kickoff even if physical testing occurs later.

---

## 10. Arrhenius and engineering feasibility

The response correctly separates aggregate hardware capacity from actual allocation and measured throughput. The hardware appears capable in principle, but the programme's usable capacity remains unproven.

Before a large allocation request, the team should produce a phase-specific compute and storage table containing model size, pair-token distributions, sequence and patch lengths, measured throughput, optimizer steps, evaluation overhead, seed and ablation counts, checkpoint volume, embedding volume, and mandatory versus optional experiments.

The qualification gate should include:

- PyTorch/CUDA and aarch64 compatibility;
- FlashAttention, xFormers, fused optimizers, and custom extensions;
- FAISS GPU, MMseqs2, and structural-alignment tools;
- checkpoint/restart behavior;
- supported container and launcher configuration;
- one- and four-GH200 measurements on short, median, long, and pathological pairs; and
- multi-node scaling only after the single-node workflow is stable.

Official launcher guidance and NAISS support for efficient inter-node container communication should be reflected in the implementation plan. Multi-node training should not be assumed to be beneficial until end-to-end scaling efficiency is measured.

---

## 11. Literature and strict-PLM positioning

The response correctly moves the principal novelty claim away from architecture alone and toward the coherent integration of evidence semantics, assay and selection modeling, strict evaluation, calibrated selection, and prospective validation.

Before Version 3 is circulated as a scientific blueprint, it should contain full and directly checkable references rather than only a generic source note. The corrections to references 23 and 33 should be made in the bibliography itself, and MSA Pairformer, SPPIDER-seq, and ReCLIP should be incorporated into an explicit novelty comparison.

The small strict-PLM track should be interpreted carefully. A smaller custom model differs from a public model in capacity, corpus size, optimization, and training compute as well as exposure. Its performance difference cannot be attributed solely to contamination. The track is useful as an exposure-sensitivity audit only when model scale, data, similarity, and training-history confounders are reported clearly.

---

## 12. Required operational appendix

Before full-programme approval, Version 3 should include a concise appendix with the following tables.

| Required table | Minimum content |
|---|---|
| Scientific scope | Organism, interaction class, treatment of homomers, assay, constructs, context, tested universe, candidate universe |
| Endpoint definitions | Selection, evaluability, context-dependent binding, observed outcome, compatibility score, intended calibration claim |
| Evidence schema | Required fields, missingness rules, mapping confidence, technical failures, conflicts, provenance, licensing |
| Benchmark specification | Primary split, sensitivity splits, temporal freeze, audit confidence, contamination checks, resampling unit |
| Decision metrics | Primary metric, precision/calibration constraints, retrieval budget, prospective endpoint |
| Go/no-go gates | Numerical or procedurally frozen thresholds, owners, decision dates, evidence required |
| Staffing and ownership | Named work-package lead, FTE allocation, dependencies, external commitments |
| Compute and storage | Allocation, measured throughput, experiment inventory, storage and checkpoint budget |
| Experimental protocol | Partner, assay capacity, constructs, controls, failure handling, orthogonal validation, analysis plan |

Thresholds do not need to be invented before the pilot distribution is understood. The procedure and date for selecting them must, however, be fixed, and the thresholds must be frozen before comparative model results are examined.

---

## 13. Feasibility judgment

| Programme component | Feasibility judgment |
|---|---|
| Six-month evidence and benchmark pilot | **Feasible with prerequisites**: requires an identified systematic source, four core FTE, specialist support, and early licensing resolution. |
| Assay-specific prediction and compatibility scoring | **Feasible and scientifically valuable**: should be treated as a planned deliverable. |
| Fully identified universal latent binding model | **High research risk**: cannot be promised; continuation must depend on recovery and prior-stability evidence. |
| Partner-aware sparse architecture | **Technically feasible, scientifically conditional**: continue only if oracle experiments demonstrate value and sparse routing reduces cost. |
| Proteome-scale retrieval and reranking | **Feasible after retrieval audit**: candidate recall, not reranker accuracy, may be the limiting factor. |
| Prospective validation | **Feasible only with early commitment**: likely to become the schedule-critical dependency if partner, constructs, and throughput are not secured at kickoff. |
| Reduced 24-month programme | **Feasible with disciplined staging and adequate staffing**. |
| Complete original programme | **Not credible as one 24-month critical path** without a large consortium and substantial experimental capacity. |

---

## 14. Editorial and governance comments

The response is clear, professional, and well structured. The Version 3 decision table and the oracle-routing interpretation are especially effective.

Before formal circulation or adoption:

- replace first-person "I agree" with either a named author or a working-group "we";
- distinguish clearly between a draft prepared for the group and an approved working-group position;
- add an approval/version table identifying authors, reviewers, date, and decision status;
- align the displayed date with the final circulation date;
- include a complete bibliography; and
- replace "where feasible" in the prospective-validation statement with a conditional but prespecified gate.

---

## 15. Final recommendation

The response strengthens iPIN-OpenPPI substantially. Its central scientific judgments should be adopted:

- make the programme evidence- and evaluation-first;
- use a context-conditional endpoint or compatibility score rather than a universal intrinsic probability;
- model both assay sensitivity and specificity;
- distinguish selection, technical success, binding, and observation;
- develop the statistical pilot first on a systematic tested universe;
- use partner-aware joint patch-pair routing only if oracle experiments justify it;
- retain a benchmark ladder with strict leakage audits and defined candidate universes;
- defer mechanism experts, triplets, broad affinity modeling, and large custom pretraining; and
- secure prospective experimental capacity at kickoff.

The expert group should approve the response as the foundation for Version 3 and authorize the six-month de-risking phase subject to the kickoff prerequisites. Full-programme authorization should follow only after the operational appendix is complete and the evidence, statistical, routing, retrieval, compute, and experimental gates have been passed.

### Suggested revised programme statement

> iPIN-OpenPPI will develop evidence-aware sequence models for prioritizing direct protein-protein interactions within explicitly defined assay and candidate universes. The programme will model assay reliability, technical failure, conditional negative evidence, and non-random testing; evaluate under strict biological and temporal novelty; and conduct a prespecified prospective validation pilot after the evidence, retrieval, model, compute, and assay-readiness gates are met.

---

## Document basis

This assessment is based on:

1. *Response to the iPIN-OpenPPI Independent Technical Review and Feasibility Assessment*, working-group discussion document, 2 August 2026.
2. *iPIN-OpenPPI Independent Technical Review and Feasibility Assessment*, 2 August 2026.
3. *iPIN-OpenPPI Expert Project Blueprint, Version 2*.

