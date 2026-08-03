# iPIN-OpenPPI

## Independent Technical Review and Feasibility Assessment

**Document reviewed:** iPIN-OpenPPI: Research and engineering blueprint for robust sequence-based protein-protein interaction prediction, version 2.0  
**Review date:** 2 August 2026  
**Prepared for:** iPIN-OpenPPI expert working group  
**Status:** Independent technical assessment for discussion and project planning

---

## Executive assessment

The iPIN-OpenPPI blueprint is a strong and unusually thoughtful research programme. Its most important contribution is not a particular neural-network block. It is the decision to treat interaction meaning, evidence provenance, assay observability, negative-label uncertainty, data leakage, calibration, and prospective validation as parts of one scientific system.

The programme should be pursued, but it should not be executed exactly as currently written.

The evidence warehouse, leakage-controlled benchmark, baseline suite, and a restricted assay-aware statistical model are technically feasible and likely publishable. The complete 24-month programme is feasible only for a well-staffed consortium with committed biological curation, substantial compute allocation, and secured experimental capacity. For a smaller team, the current plan contains too many high-risk research branches to complete rigorously within two years.

Three changes are essential before implementation begins:

1. The primary target must be operationally defined. “Intrinsic capacity to interact under some compatible biochemical state” is not yet a measurable or calibratable quantity.
2. The observation model must represent assay false positives and the non-random process by which protein pairs are selected for testing.
3. Interface-region routing must be conditioned on both interaction partners. A protein-only router cannot reliably select among partner-specific interfaces.

The strongest near-term scientific opportunity is an evidence- and evaluation-first programme for direct PPI prediction under assay and selection bias. The sparse sequence architecture should be treated as one component of that programme, not as its sole novelty.

### Decision recommendation

Approve a six-month de-risking phase with explicit continuation gates. Do not commit at kickoff to every proposed auxiliary head, strict PLM pretraining run, mixture-of-experts model, three-protein extension, or large prospective campaign.

At the end of the de-risking phase, continue the full programme only if:

- the primary target and reference population have been agreed;
- construct and assay metadata are sufficiently complete for at least one systematic evidence subset;
- strict splits retain enough independent interaction families for meaningful evaluation;
- the assay-aware model is identifiable or demonstrably stable under plausible prior assumptions;
- partner-aware sparse routing shows value relative to simpler joint encoders; and
- an experimental collaborator, assay design, and realistic candidate budget are secured.

---

## 1. Review scope and document consistency

Both supplied formats were examined in full: the 26-page PDF and the editable DOCX. All sections, tables, equations, appendices, references, and five embedded figures were reviewed.

No substantive content difference was detected between the DOCX and PDF. The PDF is a direct presentation export of the DOCX. Apparent token differences arise from line wrapping, OOXML run boundaries, page headers and footers, and code-block formatting rather than changes in scientific content.

The visual presentation is professional. The diagrams communicate the causal decomposition, sparse architecture, benchmark ladder, Arrhenius workflow, and roadmap clearly. The document is internally coherent and generally distinguishes hypotheses from established design decisions.

This review assessed:

- scientific target validity;
- statistical identifiability;
- evidence and label semantics;
- architecture and training feasibility;
- leakage controls and benchmark design;
- proteome-scale inference;
- Arrhenius implementation;
- staffing and scheduling;
- novelty relative to literature available through 2 August 2026; and
- suitability of the proposed publication and validation strategy.

---

## 2. What the blueprint gets right

Several principles in the blueprint should be retained without dilution.

### 2.1 Evidence records rather than collapsed pair labels

Treating an evidence record as the primary stored object is the correct foundation. Assay, construct, orientation, publication, biological context, outcome, and curator provenance should be preserved before any consensus label is generated.

This makes it possible to:

- represent disagreement instead of silently averaging it away;
- distinguish assay failure from a biological negative;
- support assay-specific observation models;
- revise consensus policies without rebuilding source ingestion;
- perform temporal and source holdouts; and
- audit exactly which evidence influenced a prediction.

This is likely to be one of the project’s most durable contributions.

### 2.2 Direct binding must remain separate from association

The blueprint correctly distinguishes direct binary interaction, direct contact within a complex, co-complex membership, transient regulation, and functional association. HuRI, IntAct, BioPlex, STRING, PDB-derived resources, and tissue co-abundance atlases do not measure the same biological quantity and must not be collapsed into one undifferentiated target.

The recommended primary scope—direct physical heteromeric interaction, with co-complex association as an auxiliary task—is sensible for a first phase. Homomers, higher-order complexes, and context-dependent assemblies should be explicitly excluded or benchmarked separately.

### 2.3 Leakage control is a first-class contribution

The emphasis on C3 evaluation, sequence-cluster holdouts, interface-family holdouts, assay and species transfer, temporal evaluation, network diagnostics, and pretrained-model exposure is well justified.

Random pair splits and random negatives remain useful diagnostics, but they should not be headline evidence for novel partner discovery. The blueprint is correct that benchmark construction must precede large architecture searches.

### 2.4 Realistic prevalence and selective prediction matter

At proteome scale, a small false-positive rate can generate an impractical number of candidates. Precision at an experimental budget, retrieval recall, calibration, risk-coverage curves, and abstention are more decision-relevant than AUROC alone.

### 2.5 The phased and gated philosophy is sound

The proposed order—data, benchmark, assay-aware baseline, sparse architecture, mechanistic supervision, retrieval, then prospective validation—is appropriate. Oracle-window comparisons, matched-compute ablations, and explicit removal of components that fail strict gates are especially good design choices.

---

## 3. Feasibility summary

| Workstream | Feasibility assessment | Primary risk or dependency |
|---|---|---|
| Evidence warehouse | Feasible, but labor-intensive | Dedicated data engineering and biological curation |
| Leakage-controlled benchmark | Highly feasible and high scientific value | Strict splits may discard substantial data |
| Assay-aware PU baseline | Promising but statistically high risk | Identifiability and non-random pair selection |
| Sparse local-to-global encoder | Technically feasible | Router must be partner-conditioned |
| Contact and mutation supervision | Feasible on restricted subsets | Structural-family leakage and biased labels |
| Structure/MSA distillation | Feasible but contamination-prone | Teacher, template, and MSA provenance |
| Mechanism mixture of experts | Premature in phase one | Sparse and inconsistent mechanism labels |
| Strict PLM pretraining track | Feasible only at limited scale | Token budget, corpus filtering, and GPU allocation |
| Proteome retrieval and reranking | Feasible | Bi-encoder retrieval recall may cap the system |
| Prospective validation | Conditionally feasible | Assay throughput, construct success, and lab commitment |
| Entire programme in 24 months | Feasible only for a consortium | Staffing, experimental lead time, and accumulated research risk |

### 3.1 Practical staffing estimate

The blueprint lists responsibilities but not full-time effort. A practical planning estimate for the complete programme is:

- one to two data/benchmark engineers;
- one biological curator or protein scientist with substantial protected time;
- two model researchers or research engineers;
- one structural/co-evolution specialist;
- approximately half-time statistical leadership;
- approximately half-time HPC/MLOps support;
- scientific leadership; and
- a separate experimental team capable of construct design, primary screening, troubleshooting, and orthogonal follow-up.

This corresponds roughly to six to ten computational/biological full-time equivalents, plus experimental support. A team of two to four people can realistically deliver the warehouse, benchmark, baselines, and perhaps one primary model within 24 months, but not the entire blueprint at the proposed level of rigor.

---

## 4. Critical statistical and biological issues

### 4.1 The primary target is not yet operational

The proposed target is the “intrinsic capacity to form a direct physical interaction under some compatible biochemical state.” This is scientifically intuitive but difficult to falsify.

The phrase “under some compatible state” makes the claim existential. Interaction may depend on:

- concentration;
- pH, ionic strength, cofactors, or ligands;
- isoform;
- cleavage or maturation state;
- post-translational modification;
- conformational state;
- oligomeric assembly;
- membrane environment;
- competing partners; and
- construct boundaries and tags.

If any compatible condition qualifies, a negative intrinsic label becomes nearly impossible to establish. If a specific biochemical condition is intended, that condition must be defined.

A calibrated target should instead be tied to an explicit reference distribution:

\[
p_{\mathrm{ref}}(A,B)
=
\mathbb{E}_{c\sim q_{\mathrm{ref}}}
P(\mathrm{direct\ binding}\mid S_A,S_B,c)
\]

Here, \(q_{\mathrm{ref}}\) defines the biochemical contexts over which the probability is interpreted. If no defensible reference distribution can be specified, the primary sequence-only output should be called a compatibility or prioritization score rather than a universal intrinsic probability.

### 4.2 The observation equation excludes false positives

The blueprint proposes:

\[
z_{AB}\sim\mathrm{Bernoulli}(p_\theta(S_A,S_B))
\]

\[
y_{ABm}\sim\mathrm{Bernoulli}(z_{AB}\rho_\phi(S_A,S_B,m,c,\ldots))
\]

When \(z=0\), this model forces \(P(y=1)=0\). It therefore assumes that an assay can miss a real interaction but cannot report an artifactual one.

Real evidence can contain:

- assay artifacts;
- indirect or bridged associations;
- contamination;
- auto-activation;
- construct-induced binding;
- mapping errors;
- incorrect biological-assembly assignments; and
- curation errors.

A more appropriate observation model contains both sensitivity and specificity:

\[
P(y=1\mid b,m,x)
=
b\,\mathrm{Se}_m(x)
+
(1-b)\,[1-\mathrm{Sp}_m(x)]
\]

Here, \(b\) is binding in a specified context, \(m\) is the assay, and \(x\) contains orientation, construct, expression, and other design features.

Orthogonally supported interactions and strong non-binding evidence can constrain this model, but they should generally be treated as highly reliable probabilistic anchors rather than deterministic truth.

### 4.3 Pair selection must be modeled separately

The blueprint treats untested pairs as positive-unlabeled examples, but the tested and published pairs are not selected randomly.

Selection depends on:

- protein popularity and publication history;
- pathway hypotheses;
- known domains or homologues;
- abundance and expression;
- subcellular localization;
- availability of clones and constructs;
- assayability;
- previous computational predictions; and
- institutional or disease priorities.

Introduce a tested/selected variable:

\[
t_{ABm}
\sim
P(t=1\mid A,B,m,\mathrm{study\ history},\mathrm{assayability})
\]

The resulting system should distinguish:

1. whether a pair is selected and successfully tested;
2. whether binding exists in the relevant biological/biochemical context; and
3. whether the assay reports a positive result.

Classical PU methods often assume that labeled positives are selected completely at random, or selected at random conditional on observed features. Those assumptions are unlikely to hold globally for PPI databases. A systematic assay search space, such as an explicitly defined all-by-all or matrix screen, is therefore the best initial setting for an identifiable pilot.

### 4.4 Context can affect binding, not only observability

The current causal decomposition places context mainly in biological realization and assay observability, while \(z\) depends only on canonical sequences. This is too strong.

PTMs, isoforms, cleavage, ligands, and assembly state can change the physical binding relation itself. The model should either:

- define \(b_{ABc}\), a context-dependent binding variable; or
- define an explicit marginal over a reference distribution of contexts.

Otherwise, the sequence-only model may be useful for ranking, but its output should not be interpreted as a context-free biochemical truth.

### 4.5 Identifiability needs a dedicated work package

The blueprint recognizes identifiability as a risk, but it should be elevated from a mitigation note to a central experimental programme.

Before applying the latent model to the full warehouse:

- test recovery on synthetic data with known assay sensitivity, specificity, and selection mechanisms;
- evaluate posterior or parameter stability under alternative assay priors;
- fit simpler nested models and compare them;
- quantify how much repeated and cross-assay evidence is actually available;
- perform negative-control fits where assay labels or protein identities are permuted; and
- report partial-identification intervals if point identification is unsupported.

If the intrinsic and assay components cannot be separated reliably, the project should fall back to calibrated assay-specific prediction plus an evidence-integrated compatibility score.

---

## 5. Architecture review

### 5.1 The router must be partner-aware

The proposed system encodes each protein and lets an interface router select candidate regions before expensive inter-chain attention.

The problem is that interfaces are often partner-specific. A hub protein may use distinct domains, motifs, or disordered regions for different partners. A router that sees only protein A can learn generic interface propensity, solvent exposure proxies, domain boundaries, or frequently used surfaces, but it cannot reliably determine which surface is relevant to protein B.

A more defensible design is:

1. Encode each chain with shared weights.
2. Pool residue embeddings into overlapping coarse patches.
3. Compute an inexpensive partner-aware patch-pair compatibility matrix.
4. Select joint patch pairs rather than independent top-\(k\) patches.
5. Apply high-resolution sparse cross-attention to selected patch pairs.
6. Retain a global interaction path and a full-attention path for short pairs.
7. Aggregate the intrinsic head with exact swap symmetry.

This design still provides sparse computation, but routing is informed by the proposed partner.

### 5.2 Oracle and routing controls

The following ablations are essential:

- full attention versus sparse attention at matched parameters and compute;
- fixed windows versus independent learned routers;
- independent routers versus joint partner-aware routing;
- predicted windows versus oracle structural-interface windows;
- global-only versus local-only versus combined paths;
- single-scale versus motif-scale plus domain-scale windows; and
- routing stability across seeds and closely related partners.

If oracle windows do not materially improve strict interaction prediction, the contact-routing hypothesis may not justify the added complexity. If oracle windows help but learned routing does not, the problem is the proposer rather than the cross-attention module.

### 5.3 Multi-task scope is too broad

The proposed heads cover intrinsic interaction, assay observation, interaction type, interface residues, contacts, affinity, mutation effects, mechanism experts, and uncertainty.

These tasks use different datasets, conditions, units, and missingness patterns. Activating them together creates risks of:

- negative transfer;
- domination by the largest evidence source;
- inconsistent calibration;
- misleading gains on easy mixed splits;
- overfitting to structurally characterized complexes; and
- excessive ablation cost.

Recommended order:

1. intrinsic/reference interaction score plus assay observation;
2. interface-region supervision;
3. mutation ranking;
4. optional contact distillation;
5. affinity only on conditionally coherent subsets; and
6. mechanism experts only after label sufficiency has been demonstrated.

The three-protein competition/cooperation extension should remain outside the initial 24-month critical path.

### 5.4 Affinity and mutation supervision require careful semantics

Affinity measurements vary with temperature, buffer, constructs, method, stoichiometry, and reporting units. Combining \(K_d\), \(pK_d\), and \(\Delta G\) without condition-aware modeling can create an apparently large but scientifically incoherent target.

Mutation labels are also biased toward known interfaces and disease-relevant proteins. Ranking within the same experiment or complex is generally safer than global regression across laboratories.

Counterfactual consistency is a strong idea, but generic protein destabilization must be separated from partner-specific disruption. Where possible, include:

- monomer stability controls;
- expression/abundance controls;
- partner-swapped mutations;
- neutral variants from the same scan; and
- compensatory double mutants.

### 5.5 Uncertainty claims must be empirically demonstrated

Temperature scaling can improve average calibration on an in-distribution validation set, but it does not establish epistemic uncertainty or guarantee calibration on novel families, interfaces, assays, or species.

The project should evaluate:

- calibration within each major domain;
- risk-coverage under domain shift;
- deep ensembles or other uncertainty baselines for finalists;
- uncertainty correlation with nearest-training similarity;
- uncertainty on intentionally corrupted or partner-swapped inputs; and
- whether abstention increases prospective validation yield.

The terms epistemic and aleatoric should be used only when the modeling assumptions and validation support that distinction.

### 5.6 Retrieval may become the system bottleneck

The two-stage retrieval/reranking plan is appropriate. However, a single dot-product embedding imposes a restrictive geometry on a relationship that can be multi-interface, motif-specific, and non-transitive.

Candidate generation should compare:

- one global vector per protein;
- several learned query/key projections;
- multiple region or domain embeddings;
- late interaction over compact patch sets; and
- hybrid biological filters where appropriate.

Retrieval recall at the intended candidate budget must be measured before reranker precision. A strong reranker cannot recover a true partner that was never retrieved.

---

## 6. Evidence warehouse and label programme

### 6.1 Negative evidence should remain conditional

The categories “confirmed noninteractor” and “strong intrinsic negative” should be used cautiously. Most negative evidence supports:

> no interaction detected for these constructs, in this orientation, under these conditions, using this assay.

It rarely proves that the canonical sequences cannot bind in any compatible biochemical state.

Recommended representation:

- technical failure;
- assay-negative with complete construct/expression checks;
- assay-negative with incomplete technical metadata;
- orthogonally supported non-binding under specified conditions;
- biological incompatibility hypothesis;
- untested/unlabeled.

These records can receive different likelihood weights without being collapsed into hard universal negatives.

### 6.2 Construct resolution is likely to dominate curation effort

The blueprint correctly emphasizes constructs, but systematic construct-to-sequence mapping may be the hardest data-engineering task.

The warehouse needs explicit handling of:

- fragments and domain constructs;
- isoforms;
- signal-peptide and propeptide removal;
- tags and fusion partners;
- engineered mutations;
- ambiguous residue numbering;
- sequence discrepancies between publication and database;
- orientation; and
- constructs described only in supplementary material.

Before promising full coverage, the team should manually audit representative samples from each major source and report mapping completeness and ambiguity.

### 6.3 Structural contacts are not automatically biological direct interactions

PDB-derived chain contacts can include crystal-packing interfaces, engineered assemblies, antibodies, repeated subunits, and uncertain biological-unit assignments. Structural positives should include:

- biological-assembly provenance;
- interface size and quality filters;
- experimental method and resolution;
- chain-to-UniProt mapping confidence;
- symmetry and oligomeric state; and
- explicit exclusion or tagging of engineered constructs.

PINDER and PPIRef are valuable resources, but their split and interface definitions should be versioned and independently audited for the project’s target.

### 6.4 Source licensing and redistribution need an explicit matrix

The release plan says “subject to source licenses,” but this should become a formal deliverable before ingestion.

For every source, record:

- license and permitted redistribution;
- whether raw records, transformed records, identifiers, sequences, and derived labels may be released;
- required attribution;
- version and access date;
- restrictions on commercial use; and
- whether model weights trained on the data can be redistributed.

This may determine whether the public contribution is a full evidence warehouse, reproducible ingestion code plus manifests, or controlled-access derived subsets.

---

## 7. Benchmark and evaluation review

### 7.1 Correct the C2 definition

The blueprint defines:

- C2 as at least one test protein absent from training; and
- C3 as both test proteins absent from training.

This makes C3 a subset of C2. Define C2 as exactly one protein unseen, or clearly label C2 as a cumulative category and report the exclusive subgroups separately.

### 7.2 Do not intersect every strict condition prematurely

The recommended default combines C3, 30% sequence clustering, publication-time holdout, and interface analysis. This is scientifically strict, but a single intersection may become too small and unrepresentative.

Recommended benchmark organization:

- an identity-based C1/C2/C3 ladder;
- sequence-cluster tests at several thresholds;
- publication-time tests;
- assay/source holdouts;
- species holdouts;
- structural interface-cluster tests on the structural subset; and
- one prespecified combined stress test.

Report how many proteins, pairs, families, positive anchors, assay negatives, and interaction mechanisms survive each restriction.

### 7.3 Interface-cluster status should have confidence levels

Resolved interface clustering is possible only for a subset. For other pairs, predicted structures or homology may provide evidence, but using predictions to define a benchmark can create circularity.

Classify examples as:

- experimentally interface-audited;
- computationally interface-audited;
- sequence-audited only; or
- interface status unknown.

Primary claims about novel binding modes should be restricted to the experimentally audited subset unless the prediction-based audit is independently validated.

### 7.4 Temporal evaluation requires full information cutoffs

The first publication date of the interaction is only one component of a temporal split.

The freeze should cover:

- source database releases;
- sequence database snapshots;
- PDB and structure-template releases;
- MSA databases;
- teacher-model versions;
- PLM pretraining corpora;
- text-mined or predicted sources; and
- any candidate-generation heuristics.

Later evidence is not a genuine discovery test if the pair, a close homologue, or the same interface was exposed through another source.

### 7.5 Precision at realistic prevalence cannot be measured from incomplete labels alone

Treating all unknown proteome pairs as negatives will count undiscovered positives as false positives and bias precision estimates.

Proteome-scale precision should be estimated using:

- systematic assay universes with known tested sets;
- strict later-evidence evaluation;
- prospective experiments; or
- sensitivity analyses over plausible prevalence and missing-positive rates.

Calibration must be reported for a defined organism, candidate universe, assay, and retrieval policy. It should not be presented as one universal property of the model.

### 7.6 Graph metrics are secondary diagnostics

Network density, degree distribution, clustering, complexes, and pathway coherence are useful diagnostics, but interactomes are incomplete and historically biased. Optimizing a model to resemble the known graph can reward those biases.

Sequence-only pair scores must remain the primary output. Graph-constrained decoding should be reported separately, and graph plausibility should not be used as proof that individual novel PPIs are correct.

### 7.7 Replace the composite selection score

The proposed geometric mean combines:

- AUPRC values evaluated at potentially different prevalences;
- recall at a selected precision threshold; and
- an undefined normalized Brier transformation.

This can obscure trade-offs and produce unstable rankings.

Use:

1. one prespecified primary decision metric;
2. a hard minimum precision and calibration constraint;
3. a secondary dashboard; and
4. explicit compute, coverage, and mechanism diagnostics.

### 7.8 Statistical uncertainty must reflect graph dependence

Pairs are not independent because proteins, families, complexes, assays, and publications recur.

Clustered bootstrap or resampling should consider:

- sequence family;
- interaction-network component;
- publication or study;
- assay batch; and
- structural interface family.

Report effect sizes and confidence intervals for key ablations. A hidden final test is desirable if operationally possible.

---

## 8. Novelty and literature positioning

The blueprint correctly recognizes that joint pair encoding, multi-chain context, local interaction grammars, mutation-specific modeling, and uncertainty-aware prediction already exist. The recent cornerstone references are real and broadly characterized accurately.

The strongest novelty is therefore the coherent combination of:

- evidence-record semantics;
- assay and selection modeling;
- partner-aware sparse local reasoning;
- strict pretraining and supervised leakage audits;
- calibrated candidate selection; and
- prospective validation.

Architecture alone is unlikely to support the strongest novelty claim.

### 8.1 Recent work that should be added

The stated literature review date is 2 August 2026, but the landscape section omits several directly relevant works available by then:

- **MSA Pairformer**, published online in July 2026, introduces an efficient coevolutionary pair representation and reports strong interface-contact and variant-effect performance. It should be considered as a teacher and benchmark.
- **SPPIDER-seq**, published in 2026, specifically addresses partner-aware sequence-only interface localization with cross-attention.
- **ReCLIP**, a June 2026 preprint, develops residue-specific partner context for mutation, PTM, and peptide-MHC interaction tasks.

These works do not invalidate iPIN-OpenPPI, but they narrow claims around residue-level pair context and partner-aware interface modeling.

### 8.2 Reference corrections

- Reference 23 is not a separate publication. It is the mutation dataset and analysis within the PLM-interact paper and duplicates reference 1.
- Reference 33 gives an inaccurate title. The published title is “Atlas of predicted protein complex structures across kingdoms.”
- PINDER should remain explicitly labeled as a versioned preprint/resource unless a version of record is cited.
- The tissue-specific atlas concerns protein associations and should not be described or ingested as a direct-binding atlas.

### 8.3 Public-PLM versus strict-track interpretation

The public-PLM leakage concern is well supported. However, a strict track does not automatically become contamination-free merely because held-out supervised families are removed.

The audit must consider:

- exact pretraining sequences;
- homologous families;
- database release dates;
- training-corpus preprocessing;
- sequence fragments and isoforms;
- paired interaction data used during pair-language pretraining; and
- structure/MSA teachers.

ESM-2 public models were trained on a documented UniRef50 release, which helps temporal auditing, but family-level exposure still requires explicit similarity analysis.

A strict custom model should be small enough to train and repeat. Its role is to estimate the contribution of exposure, not necessarily to beat the public model.

---

## 9. Arrhenius and engineering assessment

The hardware description in the blueprint agrees with current official NAISS documentation. Arrhenius has sufficient aggregate GPU memory, CPU capacity, local NVMe, shared storage, and interconnect for the proposed workloads.

The limiting distinction is:

- **hardware capacity:** sufficient;
- **project allocation and measured throughput:** not yet demonstrated.

### 9.1 A compute formula is not yet a compute budget

Before a large allocation request, provide a phase-specific table containing:

- model parameter count;
- trainable parameter count;
- sequence and pair-token totals;
- sequence-length distribution;
- window and selected-patch distribution;
- measured tokens/s/GPU;
- number of epochs or optimizer steps;
- evaluation and teacher-generation overhead;
- seeds and ablation count;
- expected checkpoint and embedding storage;
- one-node and multi-node efficiency; and
- mandatory versus optional experiments.

Profiling should cover short, median, long, and pathological pairs. Pair-language training cost depends heavily on the length distribution and attention implementation, not only parameter count.

### 9.2 The software stack is a real early risk

Arrhenius GPU nodes are aarch64 GH200 systems, and the HPC service became available to users only recently in 2026. Validate early:

- PyTorch and CUDA versions;
- FlashAttention and xFormers;
- fused optimizers;
- FAISS GPU;
- MMseqs2;
- structural alignment packages;
- custom CUDA/C++ extensions;
- distributed checkpointing; and
- Apptainer networking.

Use supported components where possible and avoid making an unmaintained custom kernel part of the critical path.

### 9.3 Launcher and multi-node validation

Official NAISS guidance recommends mpprun for many applications and advises contacting support for efficient inter-node container communication.

The single-node Slurm example is acceptable as an illustrative skeleton, but it is not a production recipe:

- task counts and CPU binding are unspecified;
- torch.distributed.run with standalone is a single-node configuration;
- multi-node rendezvous needs a separate recipe;
- NCCL/Slingshot behavior must be measured; and
- the exact container launch path should be validated with NAISS.

### 9.4 Storage strategy is sound

The recommendations to use Parquet/Arrow-style canonical stores, sharded token data, node-local staging, and replication of irreplaceable artifacts are appropriate.

Add:

- an estimated storage budget per data version;
- retention policy for checkpoints and logits;
- checksum verification after local staging;
- explicit recovery drills; and
- a storage/redistribution plan for model-derived pseudo-labels and teacher outputs.

---

## 10. Roadmap and publication strategy

### 10.1 Credible first half

With adequate staffing, the following milestones are credible:

- month 3: evidence ontology and pilot ingestion;
- month 6: evidence warehouse v1 and initial immutable split manifests;
- month 10: leakage audit and benchmark manuscript;
- month 14: assay-aware baseline decision.

Month 6 remains aggressive if exact construct mapping is required across all major sources. A warehouse v1 should be explicitly scoped rather than implying complete curation.

### 10.2 Overloaded second half

Months 14–24 currently contain:

- sparse routing;
- contact and mutation learning;
- structure and MSA distillation;
- mechanism experts;
- strict PLM experiments;
- proteome retrieval;
- graph evaluation;
- model freeze;
- candidate selection;
- prospective testing;
- orthogonal validation;
- release engineering; and
- two further papers.

These risks compound. Delays in data or statistical modeling propagate into architecture, candidate selection, and laboratory work.

For the complete scope, 30–36 months is more credible. For a 24-month programme, defer:

- mechanism MoE;
- three-protein competition/cooperation;
- broad affinity regression;
- large strict-PLM pretraining beyond a small audit model; and
- either structural or MSA distillation until the other has passed a gate.

### 10.3 Experimental lead time must begin at kickoff

The model freeze at month 22 and prospective readout at month 24 leave insufficient contingency for many wet-lab workflows.

The experimental plan must be defined early:

- assay and expected detection profile;
- constructs and cloning route;
- expression system;
- throughput;
- technical failure criteria;
- positive and negative controls;
- orthogonal validation method;
- expected turnaround;
- candidate budget; and
- pre-registration and blinding procedure.

A target of 200–500 tested pairs may be plausible for a systematic high-throughput assay, but not necessarily for low-throughput co-immunoprecipitation or purified-protein biophysics. The number must follow from the chosen assay.

### 10.4 Publication expectations

The benchmark paper is the lowest-risk and potentially most influential output. It should be designed to stand independently of the final model.

The model paper should make a focused claim about the statistical observation model and partner-aware sparse architecture. It should not require every auxiliary head to succeed.

The prospective paper should proceed only after a frozen selection rule and credible laboratory design exist. Temporal validation is a useful fallback, but it is not equivalent to a genuinely prospective experiment.

---

## 11. Recommended version 3 revisions

The following changes should be made before the blueprint becomes an execution plan.

1. Replace the universal “intrinsic probability” with a precisely defined context-conditional or reference-distribution target.
2. Add assay specificity/false-positive terms to the observation model.
3. Add an explicit pair-selection/testing process.
4. Treat all negative evidence as conditional and reliability-weighted.
5. Make sparse routing partner-conditioned through coarse patch-pair scoring.
6. Correct the C2/C3 definitions.
7. Organize strict tests as a ladder plus one combined stress test rather than one universal intersection.
8. Restrict interface-family claims to examples with a documented audit confidence level.
9. Replace the composite geometric model-selection score with one primary metric and hard constraints.
10. Make calibration conditional on the candidate universe and prevalence.
11. Add quantitative data-coverage, compute, storage, staffing, and allocation tables.
12. Add an explicit licensing and redistribution matrix.
13. Update the literature landscape with MSA Pairformer, SPPIDER-seq, and ReCLIP.
14. Correct references 23 and 33.
15. Remove mechanism MoE and the three-protein extension from the initial critical path.
16. Secure the experimental assay, partner, and timeline at kickoff rather than near model freeze.

---

## 12. Recommended six-month de-risking programme

### Months 0–1: operational definition and assay commitment

Deliver:

- primary organism and interaction type;
- explicit treatment of homomers and co-complex associations;
- target estimand and reference context;
- primary assay/search space;
- laboratory commitment;
- evidence ontology;
- source licensing matrix; and
- prespecified pilot success criteria.

### Months 1–3: evidence MVP

Ingest one systematic binary source plus selected orthogonal and structural evidence.

Report:

- pair and protein counts;
- exact construct-mapping rate;
- missing metadata;
- repeated measurements;
- cross-assay overlap;
- positive, negative, failed, ambiguous, and untested outcomes;
- publication and release-date completeness;
- conflict rates;
- sequence-cluster statistics; and
- redistribution constraints.

### Months 2–4: frozen pilot benchmark

Build:

- C1, exclusive C2, and C3 splits;
- sequence-cluster splits;
- one temporal split;
- assay/source holdout where possible;
- structural interface subset;
- interolog, metadata, degree, frozen-PLM, and simple pair baselines; and
- archived logits and contamination reports.

### Months 3–5: statistical identifiability pilot

Compare on identical data:

- random-negative BCE;
- matched-negative BCE;
- non-negative PU;
- selection-aware PU; and
- assay sensitivity/specificity latent model.

Test recovery on synthetic data and stability across plausible priors.

### Months 4–6: architecture proof of concept

Compare:

- pooled bi-encoder;
- simple joint pair encoder;
- full attention for short pairs;
- independent sparse routing;
- partner-aware sparse routing; and
- oracle interface windows.

Profile memory, throughput, retrieval recall, strict AUPRC, calibration, and long-sequence behavior on one and four GH200 GPUs.

### Month 6 decision

Proceed to the full programme only if the evidence, benchmark, statistical, architecture, compute, and experimental gates are all credible. Otherwise narrow the target to an assay-specific predictor and benchmark contribution.

---

## 13. Proposed go/no-go criteria

Exact numerical thresholds should be selected after the pilot data distribution is known, but the logical criteria can be fixed now.

### Evidence gate

Proceed only if:

- construct mapping is sufficiently complete for the primary subset;
- technical failure is distinguishable from biological negative;
- repeated or orthogonal evidence exists at a scale capable of constraining assay reliability; and
- strict splits retain multiple independent families and mechanisms.

### Statistical gate

Proceed with a universal latent model only if:

- parameters or posterior quantities are stable under reasonable priors;
- simulations demonstrate recoverability under comparable missingness;
- the model improves strict calibration or ranking over matched-negative and simpler PU baselines; and
- results are not driven entirely by assay/source identification.

Otherwise publish and deploy assay-specific predictions plus evidence integration.

### Sparse-routing gate

Proceed only if:

- oracle regions improve strict performance;
- learned partner-aware routing approaches the oracle benefit;
- sparse routing reduces memory or runtime for long pairs;
- gains survive sequence/interface holdouts; and
- selected regions are stable and biologically meaningful.

### Teacher gate

Proceed only if:

- every teacher input is generated within the permitted training partition;
- MSA, template, structure, and checkpoint provenance are auditable;
- improvements survive strict held-out evaluation; and
- the teacher does not merely reproduce public-data exposure.

### Retrieval gate

Proceed to proteome candidate selection only if retrieval recall at the intended budget is high enough that reranking remains meaningful. If not, revise retrieval before optimizing the reranker.

### Prospective gate

Proceed only with:

- frozen weights and data;
- a frozen candidate-selection rule;
- predefined positive, negative, and uncertainty controls;
- technical-failure handling;
- adequate construct throughput;
- orthogonal validation for key positives; and
- blinded or otherwise bias-controlled analysis where feasible.

---

## 14. Prioritized issue register

| Priority | Issue | Consequence if unresolved | Recommended action |
|---|---|---|---|
| Critical | Intrinsic target is not operational | Probability is not falsifiable or calibratable | Define context/reference distribution |
| Critical | False positives absent from observation model | Assay reliability and latent state are biased | Add sensitivity and specificity |
| Critical | Pair-selection process omitted | PU assumptions are violated | Model testing/selection explicitly |
| High | Router is partner-independent | Wrong interface may be selected | Use joint patch-pair routing |
| High | Negative anchors are overstated | Conditional negatives become false truth | Use reliability-weighted evidence |
| High | Full 24-month scope is overloaded | Quality and validation are compromised | Defer MoE, triplets, broad affinity |
| High | Wet-lab capacity is not secured | Strongest endpoint may not occur | Commit assay and partner at kickoff |
| High | Strict split intersections may be too small | Results become unstable or selected | Use split ladder plus stress test |
| Medium | Interface auditing is incomplete outside structures | Novel-interface claims become circular | Report audit confidence levels |
| Medium | Composite score is hard to interpret | Model selection may be unstable | Primary metric plus constraints |
| Medium | Strict PLM track is under-budgeted | Allocation and schedule risk | Train a smaller audit model |
| Medium | Retrieval embedding may be too restrictive | True partners never reach reranker | Compare multi-vector/late interaction |
| Medium | Arrhenius stack is new and aarch64 | Dependency and scaling delays | Early one-/multi-node validation |
| Low | Bibliographic inconsistencies | Reduces confidence in review currency | Update landscape and references |

---

## 15. Overall conclusion

iPIN-OpenPPI is scientifically worthwhile and has the potential to make an important contribution. Its strongest insight is that robust PPI prediction cannot be separated from the way interaction evidence is generated, selected, measured, curated, and evaluated.

The project should be positioned as:

> An evidence- and evaluation-first programme for direct protein-protein interaction prediction under assay and selection bias, using partner-aware sparse sequence modeling and prospective validation.

It should not yet be presented as a solved estimator of universal intrinsic interaction probability.

With a corrected estimand, a sensitivity/specificity and selection-aware observation model, partner-conditioned routing, a reduced critical path, and early experimental commitment, the programme becomes credible. Without those changes, the principal risk is not failure to train a sufficiently large neural network. It is producing a technically impressive model whose probability does not correspond to a well-defined biological quantity.

---

## Selected sources checked during this review

1. Liu D, et al. PLM-interact: extending protein language models to predict protein-protein interactions. Nature Communications, 2025. https://www.nature.com/articles/s41467-025-64512-w
2. Liu J, et al. A paired sequence language model for protein-protein interaction modeling. Nature Communications, 2026. https://www.nature.com/articles/s41467-026-70457-5
3. Ullanat V, et al. Learning the language of protein-protein interactions. Nature Communications, 2026. https://www.nature.com/articles/s41467-025-67971-3
4. Siwek JC, et al. Sliding Window Interaction Grammar. Nature Methods, 2025. https://www.nature.com/articles/s41592-025-02723-1
5. Szymborski J, Emad A. A flaw in using pretrained protein language models in protein-protein interaction inference models. Nature Machine Intelligence, 2026. https://www.nature.com/articles/s42256-025-01176-7
6. Lambourne L, et al. Experimental assessment of AI-based interactome mapping. Nature Communications, 2026. https://www.nature.com/articles/s41467-026-70942-x
7. Joeres R, et al. Data splitting to avoid information leakage with DataSAIL. Nature Communications, 2025. https://www.nature.com/articles/s41467-025-58606-8
8. SPPIDER-seq: sequence-based partner-aware predictor of protein-protein interaction sites. Bioinformatics, 2026. https://pmc.ncbi.nlm.nih.gov/articles/PMC13330928/
9. Expanding the scope of protein language modeling to protein-protein interactions with MSA Pairformer. Cell, 2026. https://www.sciencedirect.com/science/article/pii/S009286742600749X
10. Zhang Z, et al. Learning residue-level context for modeling protein-protein interactions. bioRxiv, 2026. https://www.biorxiv.org/content/10.64898/2026.06.01.729118v1
11. Bekker J, Davis J. Learning from Positive and Unlabeled Data under the Selected At Random Assumption. PMLR, 2018. https://proceedings.mlr.press/v94/bekker18a/bekker18a.pdf
12. Gerych W, et al. Recovering the Propensity Score from Biased Positive Unlabeled Data. AAAI, 2022. https://ojs.aaai.org/index.php/AAAI/article/view/20624
13. NAISS. Arrhenius technical description. https://www.naiss.se/resources/arrhenius-technical-description/
14. NAISS. Arrhenius HPC Quick Start. https://hpc.pages.naiss.se/user-documentation/support-docs/arrhenius_hpc/quickstart/
15. Qi X, et al. Atlas of predicted protein complex structures across kingdoms. Nature Communications, 2026. https://www.nature.com/articles/s41467-026-70884-4

---

**End of independent review**
