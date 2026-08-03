# iPIN-OpenPPI

## Final Computational Blueprint and Execution Workflow

### Version 3.0: evidence-aware direct PPI prioritization on Arrhenius through Apptainer

**Prepared for:** The iPIN-OpenPPI expert working group  
**Execution owner:** OpenAI Codex  
**Scientific governance:** Project sponsor and iPIN-OpenPPI expert working group  
**Mandatory platform:** NAISS Arrhenius  
**Mandatory runtime:** Apptainer SIF containers  
**Programme duration:** 24 months, with a binding six-month continuation gate  
**Date:** 3 August 2026  
**Status:** Final blueprint; project execution has not started and is not authorized by this document

---

## Executive decision

iPIN-OpenPPI will be a computational-only research programme for evidence-aware prioritization of direct human heteromeric protein-protein interactions from amino-acid sequence. It will not conduct, commission, or depend on laboratory experiments. The strongest deliverables will therefore be a provenance-preserving evidence warehouse, a leakage-controlled benchmark, calibrated assay-outcome models, an evidence-integrated sequence compatibility score, a gated partner-aware pair architecture, and a reproducible human-proteome hypothesis catalogue.

The project will not claim that sequence alone yields a universally calibrated probability that two proteins bind under any compatible biochemical condition. The primary calibrated endpoint will be tied to a defined systematic assay and tested universe. A separate sequence-derived compatibility score may support transfer and ranking, but it will remain a score unless identifiability and calibration analyses justify a stronger interpretation.

Codex is the execution owner. Once a separate start authorization is given, Codex will implement the repository, build the Apptainer environments, acquire and version public data, construct the warehouse and benchmark, submit and monitor Arrhenius jobs, train and evaluate models, maintain decision records, and prepare releases and manuscripts. Human involvement is restricted to resource and account authority, scientific governance, stage-gate approval, external communications that require a person or institution, and approval of public claims.

All project computation will run on Arrhenius through Apptainer. Native Python environments, Docker daemons, alternative HPC systems, local workstations, and cloud training are outside the production execution path. Host commands may be used only to obtain a Slurm allocation, launch Apptainer, move authorized files, inspect scheduler state, and perform other unavoidable platform orchestration.

> **Final programme decision:** Authorize only the blueprint now. When execution is separately authorized, begin with a six-month computational de-risking phase. Continue the complete programme only if the evidence, benchmark, statistical, container, compute, and architecture gates in this document are passed.

---

## 1. Locked programme decisions

| Decision | Final choice |
|---|---|
| Primary biological scope | Direct human heteromeric binary protein-protein interactions |
| Primary inference input | Two amino-acid sequences; canonical human sequences for proteome retrieval |
| Label resolution | Exact experimental constructs where available; canonical mapping is a documented derived view |
| Primary calibrated endpoint | Probability of an observed positive in a defined systematic binary assay/search space, conditional on an evaluable test |
| General sequence output | Evidence-integrated compatibility/prioritization score, not automatically a biochemical probability |
| Primary evidence setting | HuRI/HI-III systematic human binary Y2H search space, subject to reconstruction and metadata audit |
| Supporting human evidence | IntAct/IMEx direct molecular evidence, HuRI/Lit-BM, and audited structural interfaces |
| Supporting organisms | Yeast and Escherichia coli for external transfer tests where suitable systematic data exist |
| Homomers | Excluded from the primary task and primary headline metrics |
| Co-complex and functional association | Preserved as separate evidence types; excluded from primary direct-binding labels |
| Wet-lab or prospective experimental work | Not available and not part of the programme |
| Proteome-scale output | Ranked computational hypothesis catalogue with uncertainty and evidence provenance; not a validated interactome |
| Core model order | Evidence model and simple pair encoders before partner-aware sparse routing |
| Deferred scope | Mechanism mixture of experts, three-protein modeling, broad affinity regression, large custom PLM pretraining, and simultaneous structure/MSA teacher branches |
| Infrastructure | Arrhenius only, using immutable ARM64 Apptainer SIF images |
| Programme duration | 24 months with a binding month-six gate |
| Execution status | Not started |

### 1.1 Why this is the reasonable scope

Human direct heteromeric PPIs provide the most coherent combination of scientific importance, systematic binary-screen evidence, curated molecular evidence, structural anchors, and proteome-scale application. Excluding homomers removes a biologically and statistically distinct task that is vulnerable to trivial sequence-identity shortcuts. Excluding co-complex and functional association from the primary label prevents indirect proximity, pathway membership, and literature bias from being treated as direct contact.

Yeast and E. coli remain valuable as transfer tests, but a multi-species primary model would mix assay systems, proteome organization, evolutionary distances, and label densities before the human estimand is stable. They are therefore external evaluation domains rather than co-equal primary targets.

### 1.2 Explicit claim ceiling

The project may claim:

- prediction of assay-positive outcomes within a named tested universe;
- ranking of direct-PPI compatibility supported by heterogeneous evidence;
- generalization under specified protein, sequence-family, assay, source, species, interface, and temporal holdouts;
- calibrated selective prediction within the candidate universe used for calibration;
- improved retrieval of later or independently recorded evidence; and
- computational prioritization of previously undocumented pairs.

The project may not claim:

- universal context-free biochemical binding probability;
- experimental validation of novel pairs;
- in-vivo interaction from sequence alone;
- that an undocumented pair is a verified negative;
- that a structurally predicted complex is independent experimental confirmation;
- that graph plausibility proves an individual PPI;
- that a small strict PLM causally isolates pretraining leakage without accounting for capacity and corpus confounding; or
- that the final hypothesis catalogue is a completed or validated human interactome.

---

## 2. Scientific target and estimands

### 2.1 Evidence-generation variables

The final statistical semantics distinguish four processes:

- **s_ABm:** pair A-B is part of the intended search space and selected or attempted in assay m;
- **e_ABm:** the attempted test is technically evaluable;
- **b_ABc:** direct physical binding exists in specified biochemical/construct context c; and
- **y_ABm:** the evaluable assay reports a positive result.

The observation model must allow both false negatives and false positives:

P(y = 1 | b, m, x, e = 1) = b Se_m(x) + (1 - b) [1 - Sp_m(x)]

Here x contains recorded construct, orientation, expression, assay version, batch, and other design variables. Technical failure is represented by e = 0 and is never converted into y = 0.

The selection model is separate:

P(s = 1 | A, B, m, search space, study design, assayability, recorded history)

The full historical literature does not support reconstruction of one universal selection mechanism. Selection-aware estimation will therefore be developed first in systematic screens with a declared search space. Heterogeneous literature evidence will be used for anchors, transfer, sensitivity analysis, and external evaluation, not for a claim that historical selection bias has been completely corrected.

### 2.2 Required model outputs

| Output | Meaning | Calibration status |
|---|---|---|
| Assay-positive probability | P(y = 1 given s = 1, e = 1, sequences, assay, constructs, orientation, context) | Calibrated only within the specified assay and candidate universe |
| Sequence compatibility score | Symmetric evidence-integrated ranking score derived from two sequences | Not called a probability unless later gates justify it |
| Selective-prediction uncertainty | Empirical confidence or abstention score evaluated under domain shift | Must be demonstrated; not assumed from model form |
| Interface-region score | Partner-conditioned residue/patch relevance | Optional and activated only after the oracle-routing gate |
| Retrieval score | Fast candidate-generation score for proteome ranking | Evaluated by recall at a fixed candidate budget |

### 2.3 Symmetry

The biological compatibility score must satisfy exact swap symmetry:

f(A, B) = f(B, A)

Assay-observation heads may be asymmetric because bait/prey orientation, tag position, construct design, and assay version can affect detection. Symmetry will therefore be enforced in the biological head and explicitly withheld from orientation-dependent observation heads.

### 2.4 Primary scientific hypotheses

1. Evidence records that retain assay, selection, construct, and outcome semantics will produce more reliable strict generalization and calibration than collapsed pair labels.
2. Assay-aware or restricted reliability models will outperform random-negative binary classification under protein-disjoint and sequence-cluster holdouts.
3. Partner-aware joint patch routing will help only if relevant local regions contain predictive signal not captured by global pair representations.
4. Leakage-controlled evaluation will substantially reduce apparent performance relative to random pair splits and will better predict temporal and cross-assay transfer.
5. Selective prediction will improve precision among retained candidates under strict computational validation.

---

## 3. Definition of programme success

### 3.1 Minimum successful programme

The programme is scientifically successful if it releases:

- a versioned evidence ontology and ingestion system;
- a construct- and assay-aware human evidence warehouse or reproducible source manifests where redistribution is restricted;
- immutable C1/C2/C3, sequence-cluster, assay/source, temporal, species, and structural-interface benchmark manifests;
- contamination and public-PLM exposure audits;
- reproducible sequence, interolog, metadata, bi-encoder, and joint-encoder baselines;
- a calibrated assay-specific predictor on a systematic tested universe;
- uncertainty and graph-dependence-aware evaluation; and
- an Apptainer-contained Arrhenius workflow capable of reproducing the results.

This minimum remains publishable even if the latent binding model, sparse router, strict PLM, or proteome retrieval branches fail.

### 3.2 Target successful programme

The target outcome additionally includes:

- an evidence-integrated symmetric sequence compatibility score;
- a partner-aware sparse model that passes the oracle, performance, and efficiency gates;
- a high-recall human-proteome retrieval and reranking system;
- strict temporal and cross-assay improvement over the strongest simple baseline;
- a risk-coverage policy that improves precision by abstaining; and
- a ranked, versioned human PPI hypothesis catalogue with evidence, uncertainty, nearest-training similarity, and prohibited-use warnings.

### 3.3 Stretch outcomes

The following are optional and may proceed only after their gates:

- a small strict-pretraining exposure-audit model;
- structure-derived interface supervision generated entirely within training partitions;
- mutation ranking within coherent studies;
- multi-vector or patch-level late-interaction retrieval; and
- partial-identification intervals for a restricted latent binding model.

Mechanism experts, triplet competition/cooperation, broad affinity regression, and large custom PLM pretraining are not part of Version 3.

---

## 4. Evidence warehouse

### 4.1 Core principle

The primary stored object is an evidence record, not a consensus pair. Raw source records are immutable. Every consensus label, training view, and benchmark is a derived, versioned policy output. Conflicts are preserved rather than silently resolved.

### 4.2 Initial source plan

| Source | Role | Primary treatment |
|---|---|---|
| HuRI/HI-III and published test-space screens | Primary systematic human binary screen and assay-positive universe | Reconstruct search-space membership, assay versions, orientation, constructs, positives, and available technical exclusions |
| HuRI Lit-BM and earlier CCSB screens | Independent human binary evidence and historical transfer | Separate by publication and assay generation; prevent overlap leakage |
| IntAct/IMEx | Fine-grained molecular evidence, assay terms, constructs, mutations, and publications | Filter for protein-protein evidence; distinguish direct interaction from expanded n-ary or association records |
| UniProtKB/UniParc/UniRef | Versioned sequences, canonical/isoform mapping, taxonomy, and clustering inputs | Freeze release and sequence hashes; never update silently |
| PDB with SIFTS mappings | Experimentally resolved direct-contact anchors and interface audits | Use biological assemblies with explicit assembly, method, resolution, mapping, and engineered-construct controls |
| Negatome and curated non-binding reports | Conditional negative evidence | Never universal negatives; retain assay, construct, context, and literature provenance |
| Yeast and E. coli systematic screens | Species-transfer evaluation | External evaluation only unless a later amendment promotes them |
| STRING, AP-MS, BioPlex, tissue association atlases | Association and co-complex context | Excluded from primary direct-binding labels; diagnostic or auxiliary evidence only |

Every source requires a source-specific license and redistribution decision before ingestion. The public product may be complete transformed data, manifests plus ingestion code, or controlled subsets depending on source terms.

### 4.3 Required evidence schema

Each evidence record must support the following fields or an explicit missing-value code:

| Field family | Required information |
|---|---|
| Identity | Evidence ID, source record ID, unordered biological pair ID, ordered assay pair ID |
| Protein mapping | Source identifiers, UniProt/Ensembl mapping, taxonomy, canonical sequence hash |
| Construct mapping | Exact sequence where available, isoform, residue boundaries, mutations, tags, fusion partners, signal/propeptide handling |
| Search and selection | Intended search-space membership, selected/attempted status, selection source |
| Technical outcome | Clone availability, expression or assayability status, evaluable flag, failure reason |
| Assay | PSI-MI method term, assay family/version, batch, bait/prey orientation, tag location |
| Context | Organism of assay, compartment or biochemical conditions where recorded, cofactor/PTM/ligand information |
| Observation | Positive, negative, ambiguous, technical failure, or untested |
| Interaction semantics | Direct binary, direct within complex, co-complex, functional association, or unknown |
| Provenance | Publication, figure/table/supplement where available, database release, acquisition date, parser version |
| Reliability | Repeated evidence, orthogonal support, mapping confidence, interface-audit confidence |
| Governance | License, attribution, redistribution permission, embargo/moratorium, checksum |

### 4.4 Negative and unknown categories

The warehouse will use the following non-interchangeable categories:

- technical failure;
- assay-negative with complete technical checks;
- assay-negative with incomplete metadata;
- repeated or orthogonally supported non-binding under specified conditions;
- biological-incompatibility hypothesis;
- unlabeled pair inside a declared search space;
- pair outside the declared search space; and
- truly untested or status unknown.

No category will be called a universal noninteraction label.

### 4.5 Construct-mapping policy

Exact construct sequences are preferred. When only identifiers or boundaries are available, the mapping receives a confidence level:

- **A:** exact submitted construct sequence;
- **B:** unambiguous isoform and boundaries;
- **C:** canonical mapping with documented uncertainty;
- **D:** ambiguous or conflicting mapping; excluded from the strict construct benchmark.

Construct mapping completeness, ambiguity, and failure rates are first-class deliverables.

### 4.6 Data-version policy

Every acquisition creates:

- source URL and release identifier;
- acquisition timestamp;
- raw-file checksum;
- license and attribution snapshot;
- parser commit and Apptainer image digest;
- record count and schema-validation report; and
- immutable manifest linking raw inputs to derived tables.

Later source releases create new versions. They never overwrite the snapshot used for a frozen benchmark.

---

## 5. Benchmark and evaluation design

### 5.1 Exclusive protein-novelty categories

- **C1:** both proteins appeared in training, but the test pair is unseen.
- **C2:** exactly one test protein is unseen in training.
- **C3:** both test proteins are unseen in training.

The unit of assignment is the protein sequence cluster, not merely the current accession. Isoforms, fragments, construct variants, and close homologues must follow the parent cluster into one partition.

### 5.2 Benchmark ladder

| Axis | Required tests |
|---|---|
| Pair/protein novelty | C1, exclusive C2, and C3 |
| Sequence novelty | 40%, 30%, and 20% clustering sensitivity; 30% is the primary threshold |
| Time | Publication and complete information-cutoff split |
| Assay/source | Held-out assay version and held-out evidence source |
| Species | Human primary; yeast and E. coli external transfer where data permit |
| Interface | Experimentally audited, computationally audited, sequence-audited, and unknown |
| Combined stress | One prespecified C3 plus 30% cluster stress test if minimum data criteria are met |

The combined stress test is a headline result only if it retains at least 500 positive assay observations, 50 independent sequence clusters, and meaningful assay/mechanism diversity. Otherwise, the separate axes remain primary and the combined result is descriptive.

### 5.3 Complete temporal freeze

A temporal evaluation freeze must cover:

- interaction-database releases;
- source publication dates and supplement availability;
- UniProt, UniRef, and sequence snapshots;
- PDB and template releases;
- MSA databases;
- public PLM checkpoints and documented corpora;
- teacher-model versions and pseudo-label dates;
- text-mined or predicted sources; and
- candidate-generation heuristics.

Later evidence is not a discovery test if the pair, close homologue, or same interface entered through another source.

### 5.4 Candidate universe and prevalence

The primary calibrated benchmark is the reconstructed systematic HuRI search space, restricted to evaluable assay opportunities and the frozen sequence universe. If negatives are subsampled for computation, metrics must use deterministic prevalence-preserving sampling or inverse-probability weights.

Unknown proteome pairs are not treated as negatives. Proteome-wide precision is reported only through:

- systematic tested-universe evaluation;
- locked later-evidence evaluation;
- sensitivity analysis over plausible hidden-positive prevalence; and
- clearly labelled retrieval metrics.

### 5.5 Primary and secondary metrics

The primary retrospective metric is AUPRC for the assay-positive endpoint on the primary strict benchmark at its declared prevalence.

Hard constraints are:

- positive Brier skill relative to the prevalence baseline;
- calibration slope between 0.8 and 1.2 on the declared calibration domain;
- no material degradation in log loss relative to the strongest calibrated baseline;
- clustered 95% confidence intervals for all key comparisons; and
- no model selection using the hidden final test.

Secondary metrics include log loss, Brier score, calibration intercept, adaptive calibration error, recall at fixed precision, precision/recall at fixed candidate budgets, risk-coverage, retrieval recall, per-assay performance, per-family performance, long-sequence performance, memory, runtime, and storage.

AUROC and graph metrics are diagnostics only.

### 5.6 Dependence-aware uncertainty

Confidence intervals and hypothesis tests must account for repeated proteins, sequence families, publications, assay batches, complexes, and interface families. The default procedure is clustered bootstrap at the sequence-family level, supplemented by study or assay-batch resampling. Key ablations report effect sizes and confidence intervals, not only best point estimates.

### 5.7 Protected final evaluation

The model-selection test and the final test are distinct. Final labels and manifests will be kept in a protected read-only location or exposed through a one-way evaluation command where practical. If technical secrecy cannot be guaranteed, the final test remains procedurally locked: no label inspection, hyperparameter change, or split revision after first evaluation without a documented new version and full rerun.

---

## 6. Model programme

### 6.1 Baseline ladder

Every complex model must beat the strongest applicable simpler baseline on identical data and splits:

1. prevalence-only and protein-degree controls;
2. sequence-similarity/interolog scoring;
3. domain-pair or motif-pair baseline where annotations are available;
4. frozen public-PLM bi-encoder with a symmetric classifier;
5. simple symmetric joint pair encoder;
6. random-negative and matched-negative BCE models;
7. non-negative positive-unlabeled learning;
8. hierarchical assay-specific heads;
9. restricted sensitivity/specificity model;
10. partner-aware sparse pair model, only after its gate.

Metadata and degree models are shortcut diagnostics and will never be used as sequence-only deployment models.

### 6.2 Reference sequence encoder

The initial reference backbone is a medium, openly available ESM-2-class sequence encoder, with the 650M-parameter ESM-2 checkpoint as the default candidate and a smaller checkpoint for rapid iteration. The pilot begins with frozen embeddings and LoRA or similarly parameter-efficient adaptation. Full fine-tuning is reserved for finalists after memory and throughput profiling.

This choice is based on auditability, maturity, sequence-only operation, and manageable Arrhenius cost rather than a claim that it is the newest possible backbone. A newer model may replace it only through a documented amendment demonstrating compatible licensing, ARM64 execution, training-corpus provenance, and benchmark benefit.

### 6.3 Statistical model ladder

The full latent model is not the mandatory path. Models are introduced in this order:

1. assay-specific discriminative prediction;
2. matched-negative and nnPU learning;
3. hierarchical assay heads with shared sequence representation;
4. restricted sensitivity/specificity model on repeated/systematic evidence;
5. selection-aware model inside a known tested universe;
6. full latent formulation only if recovery and prior-stability gates pass.

If the full model is not identifiable, the programme freezes the assay-specific predictor and compatibility score as the final statistical outputs.

### 6.4 Core pair architecture

The mandatory core architecture contains:

- shared encoder weights for both proteins;
- global pooled representations;
- a symmetric joint interaction path;
- assay-specific observation heads;
- explicit swap averaging or commutative feature construction; and
- calibrated output and abstention policy.

This core must be trained and evaluated before sparse routing.

### 6.5 Partner-aware sparse routing

If oracle interface regions improve strict prediction, the optional sparse architecture will:

1. encode both chains with shared weights;
2. pool residue embeddings into overlapping motif- and domain-scale patches;
3. compute an inexpensive partner-conditioned patch-pair compatibility matrix;
4. select joint patch pairs rather than independent per-chain windows;
5. apply high-resolution sparse cross-attention to the selected pairs;
6. retain a global path and full attention for short pairs; and
7. aggregate the biological head with exact swap symmetry.

Initial patch widths of 48-96 residues, 50% overlap, and a small top-k patch-pair budget are hypotheses, not fixed truths. The pilot must measure patch counts, peak HBM, wall time, routing stability, and oracle recovery across length strata.

### 6.6 Oracle routing experiments

The required comparison is:

- global-only;
- full attention at matched parameter count;
- fixed windows;
- independent learned routers;
- partner-aware joint routing; and
- experimentally defined oracle interface windows on an audited structural subset.

If oracle regions do not help, routing is removed. If oracle regions help but learned routing does not, proposer research may continue only outside the critical path. Learned sparse routing becomes core only if it captures at least half of the oracle gain and meets the efficiency gate.

### 6.7 Staged heads

The activation order is:

1. assay-positive probability and compatibility score;
2. empirical uncertainty and abstention;
3. partner-conditioned interface-region score;
4. mutation ranking within coherent scans, optional;
5. contact distillation, optional.

Affinity, mechanism experts, triplet interactions, and broad multi-task activation are excluded.

### 6.8 Uncertainty

Temperature scaling is a calibration baseline, not an epistemic-uncertainty solution. Finalists will compare calibration, three-seed ensembles, and at least one efficient uncertainty baseline. Evaluation includes:

- calibration within each major domain;
- risk-coverage under family, assay, interface, and species shift;
- uncertainty versus nearest-training similarity;
- corrupted-sequence and partner-swapped controls; and
- whether abstention increases precision on temporal/external tests.

The terms epistemic and aleatoric are used only if justified by the model and evidence.

### 6.9 Retrieval and hypothesis catalogue

Proteome-scale inference uses two stages:

1. a fast symmetric bi-encoder or multi-vector retriever; and
2. joint-model reranking of a limited candidate set.

Global dot product, multiple query/key projections, region embeddings, and compact patch-level late interaction are compared. Retrieval recall is measured before reranker precision.

The final catalogue must include:

- pair and sequence identifiers;
- score and calibrated domain;
- uncertainty and abstention status;
- retrieval rank;
- nearest training similarities;
- known and conflicting evidence;
- assay/source coverage;
- interface-audit status; and
- a prominent statement that the pair is a computational hypothesis, not experimental confirmation.

---

## 7. Mandatory Arrhenius and Apptainer architecture

### 7.1 Platform facts relevant to the project

Arrhenius GPU nodes provide four NVIDIA GH200 Grace Hopper superchips, each with 96 GB HBM and 128 GB LPDDR memory, Arm CPUs, Slingshot interconnect, and approximately 1.8 TB node-local NVMe. Shared storage is divided into Disk and high-IOPS Flash tiers. Arrhenius uses Slurm, supports Apptainer, and recommends mpprun for many parallel applications. Efficient multi-node container communication requires validation with NAISS guidance.

### 7.2 Non-negotiable container policy

Every data-processing, clustering, training, evaluation, retrieval, and release computation must execute inside a versioned Apptainer SIF image on Arrhenius.

Production policy:

- build from version-controlled definition files, never from manually modified sandboxes;
- build ARM64 images on Arrhenius or explicitly with the arm64 architecture;
- use immutable SIF images;
- pin base image, operating-system packages, Python packages, and compiled dependencies;
- include labels, help text, and CPU-safe tests in the definition file;
- store SHA-256 digest, definition file, dependency lock, and inspection output;
- use the standard NVIDIA --nv path by default;
- treat --nvccli as experimental and do not use it in production unless Arrhenius testing supports it;
- run with --cleanenv and explicit bind mounts;
- keep data, checkpoints, and secrets outside the image;
- do not use writable production overlays;
- do not download dependencies, models, or data during scheduled training jobs; and
- rebuild and requalify rather than mutating an accepted image.

### 7.3 Container set

| Image | Purpose | Required contents |
|---|---|---|
| ipin-data-arm64.sif | Ingestion, schema validation, clustering, leakage audits, CPU evaluation | Python, Arrow/Parquet, DuckDB, MMseqs2 or validated equivalent, XML/JSON tools, statistical stack |
| ipin-gpu-arm64.sif | PLM embedding, training, routing, uncertainty, retrieval | PyTorch/CUDA-compatible ARM64 stack, Transformers/ESM implementation, distributed stack, FAISS or validated replacement |
| ipin-release-arm64.sif | Reproduce final benchmark and catalogue from frozen artifacts | Minimal pinned inference/evaluation stack |
| Optional teacher image | Structural or MSA processing after teacher gate | Created only if the teacher branch is authorized |

Two main images are preferred to one oversized image because CPU curation and GPU modeling have different compiled dependencies and update cycles. They share a common Python lock and schema package where possible.

### 7.4 Definition-file contract

Every definition file must contain:

- a pinned ARM64 base;
- package installation with fixed versions or hashes;
- project version and source-commit labels;
- a minimal, deterministic environment;
- a help section;
- a runscript or named applications where useful;
- CPU-safe package and import tests;
- separate GPU qualification tests executed on a GPU allocation; and
- no embedded credentials, source data, model tokens, or mutable project outputs.

Illustrative structure only:

~~~text
Bootstrap: docker
From: <approved-arm64-base-by-digest>

%labels
    Project iPIN-OpenPPI
    ImageRole gpu
    BlueprintVersion 3.0

%post
    <install pinned system and Python dependencies>

%environment
    export PYTHONNOUSERSITE=1
    export TOKENIZERS_PARALLELISM=false

%test
    <CPU-safe imports and version assertions>

%runscript
    exec python -m ipin_workflow "$@"
~~~

This is a blueprint example and is not an instruction to build the image now.

### 7.5 Runtime contract

The production runtime has:

- a clean inherited environment;
- explicit read-only binds for raw data and containers;
- explicit read/write binds for run outputs and scratch;
- NVIDIA device exposure through --nv;
- a recorded Slurm job ID and image digest;
- one immutable configuration file per run; and
- a run manifest written before computation begins.

Illustrative invocation:

~~~bash
apptainer exec --cleanenv --nv \
  --bind <project-data>:/data:ro \
  --bind <run-output>:/output:rw \
  --bind <node-scratch>:/scratch:rw \
  <image>.sif \
  python -m ipin_workflow <task> --config <frozen-config>
~~~

No command in this document has been executed.

### 7.6 Slurm and launcher policy

Single-GPU and single-node profiling comes first. Four-GPU single-node training is the default production unit. Multi-node execution is optional and begins only after:

- the single-node image and workflow pass qualification;
- NCCL all-reduce and end-to-end scaling are measured;
- the launch recipe is validated against current Arrhenius guidance;
- NAISS support guidance is obtained where efficient Slingshot-aware container communication is required; and
- scaling is more cost-effective than independent single-node runs.

mpprun is the preferred Arrhenius launcher where compatible with the workload and container arrangement. srun may be used where it is the validated method for the PyTorch launcher. A multi-node torchrun recipe will not be improvised from a single-node standalone command.

### 7.7 ARM64 and GPU qualification

The following dependencies must pass inside the GPU image on an actual GH200 allocation:

- PyTorch, CUDA, NCCL, and BF16;
- FlashAttention and xFormers if used;
- fused optimizers and any custom CUDA/C++ extension;
- FAISS GPU or its replacement;
- MMseqs2 and structural-alignment tools;
- distributed checkpoint write/read;
- deterministic CPU/GPU fixtures;
- one-, two-, and four-GPU correctness; and
- short, median, long, and pathological protein-pair workloads.

An unavailable or unstable dependency is replaced, isolated, or removed. Native execution outside Apptainer is not the fallback.

### 7.8 Storage design

| Tier | Use |
|---|---|
| Project Disk | Raw source snapshots, canonical Parquet evidence, sequence tables, immutable manifests, durable checkpoints, reports |
| Project Flash | Token shards, embeddings, retrieval indexes, small random-read workloads, active high-throughput training data |
| Node-local NVMe | Temporary decompression, epoch shards, scratch embeddings, transient checkpoints |
| External institutional storage | Backup of irreplaceable manifests, source metadata, final checkpoints, releases, and manuscripts |

Arrhenius Disk and Flash are active storage rather than backup. No irreplaceable artifact may exist only on Arrhenius or in the current no-backup workspace.

Avoid one file per protein or pair. Use partitioned Parquet, Arrow, memory-mapped arrays, or tar shards. Sequences are stored once and referenced by integer ID and sequence hash.

### 7.9 Cache and temporary storage

Apptainer cache and temporary build space must be placed in project-approved storage with sufficient capacity, not allowed to grow silently in the user home directory. Build caches are disposable; accepted SIF images and their checksums are durable artifacts. Node-local scratch is cleaned by the job and is never treated as persistent data.

### 7.10 Reproducibility manifest

Every run records:

- source commit;
- SIF path, SHA-256 digest, and Apptainer inspection metadata;
- Slurm job ID, allocation, nodes, GPU topology, and launcher;
- data and split manifest hashes;
- model and tokenizer identifiers;
- configuration hash;
- random seeds and determinism flags;
- CUDA, NCCL, PyTorch, and driver-visible versions;
- tokens per second, HBM, CPU memory, I/O wait, and communication time;
- checkpoint and metric locations; and
- exit state, retry reason, and parent run where applicable.

---

## 8. Codex execution and governance workflow

### 8.1 Operating model

Codex is responsible for the technical execution of all work packages after start authorization. The expert group does not need to supply an implementation team. Scientific governance remains human because resource ownership, institutional commitments, public release, authorship, and scientific claims require accountable human approval.

| Activity | Codex | Project sponsor/expert group |
|---|---|---|
| Repository, code, tests, schemas, and documentation | Execute and maintain | Review at gates |
| Public-data acquisition and versioning | Execute under approved terms | Confirm institutional/legal constraints if raised |
| Apptainer definitions and qualification | Execute | Provide Arrhenius account/allocation authority |
| Slurm job preparation, submission, monitoring, and recovery | Execute within guardrails | Approve material allocation changes |
| Benchmark and model experiments | Execute | Approve frozen primary design and stage gates |
| Routine technical decisions | Decide and document | No intervention required |
| Target, primary metric, split, or claim change | Propose only | Approve or reject |
| NAISS support or other external communication | Draft and diagnose | Send/authorize where a human identity is required |
| Public release, manuscript submission, and authorship | Prepare artifacts and drafts | Final approval and submission |

### 8.2 Autonomous execution loop

After authorization, each bounded unit of work follows:

1. read the current gate, budget, data, and container manifests;
2. create a versioned plan and expected outputs;
3. implement code and tests without changing frozen benchmark semantics;
4. run unit and integration tests inside the relevant SIF;
5. perform a small Arrhenius smoke job;
6. estimate cost and submit the bounded production job;
7. monitor scheduler state, logs, checkpoints, and resource use;
8. diagnose and retry only within predefined safe retry rules;
9. evaluate on development data;
10. write a run report and update the decision ledger;
11. proceed automatically when the gate is clearly passed within authority; or
12. stop and request governance input when a frozen target, large budget, external communication, or public claim must change.

### 8.3 Required project ledgers

Codex will maintain:

- decision log;
- risk register;
- source and license register;
- container register;
- data-manifest register;
- split register;
- run/experiment ledger;
- compute and storage ledger;
- issue and failure ledger;
- milestone/gate reports; and
- release checklist.

No material scientific decision may exist only in conversational history.

### 8.4 Change control

The following require a numbered blueprint amendment:

- changing the primary organism or interaction definition;
- adding homomers or co-complex labels to the primary task;
- changing the primary metric after model results are available;
- altering a frozen split;
- changing the candidate universe used for calibration;
- promoting a teacher, routing, affinity, or strict-pretraining branch to the critical path;
- moving production computation outside Arrhenius/Apptainer; or
- making stronger biological claims than the claim ceiling permits.

Routine dependency updates require a new image version and regression qualification, but not a scientific amendment unless results change materially.

### 8.5 Current no-start boundary

Creation of this blueprint does not authorize:

- downloading a dataset;
- creating a repository structure;
- building or pulling a container;
- logging into Arrhenius;
- submitting a Slurm job;
- training or evaluating a model; or
- contacting NAISS or a data provider.

A distinct user instruction is required to start execution.

---

## 9. Work packages

| WP | Title | Months | Core deliverables |
|---|---|---:|---|
| WP0 | Scientific governance and claim control | 0-24 | Locked semantics, decision log, risk register, gate reports |
| WP1 | Arrhenius/Apptainer platform | 0-4; maintenance thereafter | ARM64 data/GPU SIFs, qualification suite, Slurm launch recipes, run manifests |
| WP2 | Evidence warehouse | 1-9 | Source snapshots, schema, construct mapping, assay/selection/technical-state tables, license matrix |
| WP3 | Benchmark and leakage audit | 2-11 | Frozen split ladder, temporal freeze, interface audits, contamination reports, baseline harness |
| WP4 | Statistical and baseline models | 4-14 | BCE/PU/assay models, identifiability study, calibration and uncertainty baselines |
| WP5 | Core and sparse pair architecture | 7-18 | Joint encoder, oracle studies, partner-aware routing if gated, long-sequence profiling |
| WP6 | Retrieval and computational validation | 12-22 | Retriever/reranker, temporal and cross-assay validation, hypothesis catalogue |
| WP7 | Reproducibility, release, and publication | 18-24 | Release SIF, data/model cards, reproducibility audit, manuscripts and final report |

There is no experimental work package.

---

## 10. Twenty-four-month roadmap

### Months 0-1: authorization and operational freeze

After a separate start instruction:

- confirm Arrhenius project paths, allocation, quotas, and backup destination;
- freeze the scope and primary systematic source;
- freeze evidence ontology version 1;
- create source/license and decision ledgers;
- define the run-manifest format;
- draft ARM64 Apptainer definition files;
- fix month-six gate thresholds before model results exist.

### Months 1-3: container qualification and evidence MVP

- build and sign or checksum data and GPU SIFs;
- validate CPU and GH200 software stacks;
- ingest frozen HuRI, UniProt, and selected IntAct/PDB snapshots;
- construct exact sequence and construct mappings;
- distinguish search-space, attempted, technical, and observed states;
- publish data coverage, missingness, conflict, and license reports;
- profile one- and four-GPU representative workloads.

### Months 2-4: frozen pilot benchmark

- construct C1/C2/C3 and 30% cluster splits;
- create temporal, assay/source, species, and interface subsets;
- create contamination and public-PLM exposure audits;
- implement prevalence, metadata, degree, interolog, and frozen-PLM baselines;
- freeze pilot manifests and evaluation code.

### Months 3-5: statistical identifiability pilot

- generate synthetic data with known selection, evaluability, sensitivity, and specificity;
- compare random-negative BCE, matched-negative BCE, nnPU, assay heads, and restricted reliability models;
- perform prior-sensitivity, permutation, and source-prediction controls;
- define the fallback if latent separation fails.

### Months 4-6: pair-model and routing proof of concept

- compare pooled bi-encoder, simple joint encoder, and full attention for short pairs;
- run fixed, independent, partner-aware, and oracle routing experiments;
- profile memory, wall time, failure behavior, and retrieval recall;
- complete the month-six gate report.

### Month 6: binding continuation decision

Possible decisions:

- **Continue full reduced programme:** all mandatory gates pass.
- **Continue benchmark plus assay-specific model:** evidence/benchmark pass, but latent or routing gates fail.
- **Continue evidence resource only:** modeling claims are not supported, but warehouse/benchmark remain valuable.
- **Pause and amend:** Apptainer, data rights, systematic tested-universe reconstruction, or compute access is inadequate.

### Months 7-10: evidence warehouse and benchmark version 1

- extend construct and conflict curation;
- freeze warehouse and benchmark v1;
- complete leakage audit and baseline reevaluation;
- release an internal benchmark report suitable for Paper 1 drafting.

### Months 10-14: final statistical core

- train calibrated assay-specific and evidence-integrated models;
- finalize compatibility-score semantics;
- complete uncertainty and abstention evaluation;
- decide whether the restricted latent model is retained.

### Months 13-18: architecture and efficiency

- refine the simple joint model;
- continue partner-aware routing only if gated;
- complete long-sequence, compute-matched, and seed-stability ablations;
- freeze the model family before retrieval optimization.

### Months 16-20: retrieval and hypothesis generation

- train and evaluate global, multi-vector, and patch-level retrieval candidates;
- achieve retrieval gate at the fixed candidate budgets;
- rerank the human proteome;
- construct a provisional catalogue with evidence and uncertainty annotations.

### Months 19-22: locked computational validation

- run temporal later-evidence evaluation;
- run assay/source and species transfer tests;
- audit structural-interface enrichment without treating predictions as experimental truth;
- execute the protected final evaluation once;
- freeze weights, calibration, thresholds, and candidate-generation policy.

### Months 22-24: release and closeout

- reproduce key results from the release SIF and frozen manifests;
- finalize warehouse or ingestion manifests subject to licenses;
- finalize model and data cards;
- publish the hypothesis catalogue with claim warnings;
- prepare two primary manuscripts and final technical report;
- archive checksums, containers, code, manifests, metrics, and governance decisions.

---

## 11. Binding gates

Numerical values below are Version 3 defaults. They may be changed only by a documented amendment made before the relevant comparative result is inspected.

### 11.1 Container gate

Pass only if:

- all required computation runs inside accepted ARM64 SIF images on Arrhenius;
- definition files, locks, inspection metadata, and SHA-256 digests exist;
- CPU and GPU qualification tests pass;
- two repeated smoke runs produce matching fixture outputs within tolerance;
- one- and four-GPU jobs complete without unexplained NaN, deadlock, or silent fallback;
- four-GPU scaling efficiency is at least 70% of single-GPU throughput for the representative training fixture; and
- checkpoint/restart recovers the expected model, optimizer, scheduler, and data position.

Multi-node training is not required to pass month six.

### 11.2 Evidence gate

Pass only if:

- at least 95% of ingested records have source, release, checksum, parser, and licensing provenance;
- the primary systematic subset distinguishes search-space membership, assay attempt/evaluability, and outcome for at least 90% of usable records or explicitly narrows the estimand where the source cannot;
- at least 80% of primary strict evidence has construct confidence A or B;
- technical failures are not encoded as biological negatives;
- conflict, repeated-measurement, and missingness reports are complete; and
- the source-license matrix permits the planned internal processing and defines the public-release form.

### 11.3 Benchmark gate

Pass only if:

- C1, exclusive C2, C3, and 30% sequence-cluster assignments are immutable and leakage-audited;
- the primary strict test retains at least 500 positive assay observations and 50 independent sequence clusters;
- every test reports surviving proteins, pairs, families, assays, sources, and mechanisms;
- the complete temporal freeze is documented;
- interface-audit confidence is present; and
- the strongest baseline suite runs end to end from frozen manifests.

If the combined stress test falls below the size criteria, it is demoted without weakening the separate primary axes.

### 11.4 Statistical gate

The restricted latent model passes only if:

- pilot-like simulations estimate aggregate assay sensitivity and specificity with mean absolute error no greater than 0.10;
- nominal 90% intervals achieve at least 85% empirical coverage in those simulations;
- plausible prior changes preserve held-out ranking with Spearman correlation of at least 0.90;
- the model improves strict AUPRC by at least 10% relative to the strongest simpler sequence baseline and the clustered 95% confidence interval for the difference excludes zero;
- Brier skill is positive and calibration slope is between 0.8 and 1.2; and
- improvement is not explained by assay/source identification alone.

If these conditions fail, the full latent interpretation is removed and the assay-specific predictor plus compatibility score becomes final.

### 11.5 Routing gate

Sparse routing proceeds only if:

- oracle regions improve strict AUPRC by at least 5% relative or provide a prespecified significant gain in the long-pair subset;
- learned partner-aware routing captures at least half of the oracle improvement;
- gains survive C3 and interface-family audits;
- selected regions are stable across seeds and relevant alternative partners;
- peak HBM falls by at least 30% or wall time falls by at least 20% in the longest sequence decile; and
- strict performance is not more than 1% relatively worse than matched full attention.

Otherwise, the final system uses the simpler joint encoder.

### 11.6 Retrieval gate

Proteome-scale catalogue generation proceeds only if:

- retrieval recall@1000 is at least 95% on the locked held-out positives;
- retrieval recall@100 is at least 80%;
- performance survives sequence-cluster stratification;
- the reranker improves candidate ordering beyond the retriever; and
- the complete human-proteome run fits the approved compute and storage budget.

If retrieval fails, the project releases pair scoring and benchmark tools without a proteome catalogue.

### 11.7 Uncertainty gate

Selective prediction is retained only if:

- precision rises monotonically over a prespecified useful coverage range;
- abstention improves temporal/external precision relative to raw score selection;
- corrupted and partner-swapped inputs receive higher uncertainty than matched valid examples;
- uncertainty is reported by similarity and assay domain; and
- the final method beats or matches calibrated probability and ensemble baselines at comparable cost.

### 11.8 Computational-validation gate

Final discovery-oriented claims require:

- locked later-evidence evaluation with no post-test tuning;
- improvement over the strongest baseline with a clustered 95% confidence interval excluding zero;
- consistent direction of effect across at least two independent evidence domains, such as temporal plus assay/source transfer;
- explicit public-PLM and teacher exposure audits;
- no description of candidates as experimentally validated; and
- a hypothesis catalogue that exposes evidence conflicts and model limitations.

### 11.9 Release gate

Release requires:

- clean reproduction of headline metrics from release SIFs and frozen manifests;
- no unresolved critical license or provenance issue;
- data and model cards;
- container, code, data, split, configuration, and result checksums;
- final risk and claim audit; and
- expert-group approval of public wording.

---

## 12. Compute and storage budgeting

### 12.1 Budget principle

GPU-hour requests are derived from measured throughput:

GPU-hours = processed tokens / (measured tokens per second per GPU x 3600) x inefficiency factor x repetitions

The inefficiency factor includes evaluation, checkpointing, data stalls, failed jobs, and scaling loss.

### 12.2 Allocation distribution

The initial allocation is divided by percentage until measured GPU-hour figures are available:

| Category | Allocation share |
|---|---:|
| Container qualification, smoke tests, and profiling | 8% |
| Frozen embeddings and baseline ladder | 18% |
| Statistical-model comparisons | 18% |
| Core joint model and routing experiments | 28% |
| Retrieval, uncertainty, and locked validation | 18% |
| Strict-pretraining exposure audit, if gated | 5% |
| Failure and reproducibility reserve | 5% |

No single experiment may consume more than 5% of the total approved GPU allocation without a written preflight estimate and governance approval.

### 12.3 Scale policy

- Prefer one four-GH200 node for core training.
- Prefer independent single-node runs over multi-node training when scaling efficiency is below 60%.
- Use CPU nodes for clustering, schema joins, provenance processing, and bootstrap evaluation.
- Use fat nodes only when demonstrated memory requirements justify them.
- Do not use large-scale pretraining as a substitute for completing the benchmark and baseline programme.

---

## 13. Risk register

| Risk | Likelihood | Impact | Mitigation and fallback |
|---|---|---|---|
| No laboratory validation | Certain | High | Limit claims; use systematic, temporal, cross-assay, species, and structural computational validation; release hypotheses only |
| Single AI execution owner | Medium | High | Artifact-first workflow, automated tests, immutable manifests, decision ledger, human stage-gate governance |
| Target remains semantically ambiguous | Medium | High | Separate assay probability from compatibility score; prohibit universal binding claim |
| Selection or latent model is not identifiable | High | High | Systematic-screen pilot, simulations, nested models, partial identification, assay-specific fallback |
| Technical failure is confused with negative | Medium | High | Separate selection, evaluability, and observation in schema and likelihood |
| Construct mapping is incomplete | High | High | Confidence classes; strict subset; report coverage; never silently canonicalize |
| Strict splits become too small | Medium | Medium | Separate benchmark axes; size threshold for combined stress test; report uncertainty |
| Public PLM leakage dominates | High | High | Corpus/date audit, similarity strata, small strict exposure audit, conservative temporal claims |
| Partner-aware routing does not help | Medium | Medium | Oracle gate; retain simple joint encoder |
| Retrieval misses true partners | Medium | High | Measure recall before reranking; compare global, multi-vector, and late interaction; omit catalogue if gate fails |
| ARM64 dependency failure | Medium | High | Early SIF qualification; replace unstable dependency; no native fallback |
| Multi-node container communication fails | Medium | Medium | Single-node default; mpprun/validated srun; NAISS support; independent runs |
| Disk/Flash data loss | Medium | High | Institutional backup of irreplaceable artifacts; checksums; no sole copy on Arrhenius |
| Licensing restricts redistribution | Medium | High | Early matrix; release ingestion code/manifests or controlled subsets |
| Compute allocation is insufficient | Medium | Medium | Baseline-first priorities; parameter-efficient tuning; optional branches gated; measured budgeting |
| Temporal test is contaminated | High | High | Complete information cutoff and exposure audit; qualify claims or use strict small model |
| AI makes an undocumented scientific choice | Medium | High | Change-control rules and mandatory decision log; stop at scope/claim/budget boundaries |

---

## 14. Publication and release strategy

### 14.1 Primary manuscripts

**Paper 1: Evidence and benchmark**

Working focus: a construct-, assay-, selection-, time-, and homology-controlled benchmark for sequence-based direct PPI prediction.

Core contributions:

- evidence-record warehouse;
- conditional-negative semantics;
- C1/C2/C3 and sequence-cluster ladder;
- temporal and pretraining-exposure audit;
- baseline reevaluation; and
- dependence-aware uncertainty.

**Paper 2: Model and computational discovery**

Working focus: assay-aware sequence modeling with gated partner-aware local reasoning and locked computational validation.

Core contributions:

- assay-specific and compatibility outputs;
- identifiability experiments;
- simple versus sparse pair architecture;
- calibration and selective prediction;
- retrieval/reranking; and
- temporal and cross-assay hypothesis prioritization.

A third paper is not promised. It may be proposed only if the retrieval catalogue or strict-exposure audit becomes a distinct, sufficiently supported contribution.

### 14.2 Release package

Subject to licensing:

- evidence ontology and schema;
- source manifests, acquisition code, and license matrix;
- canonical derived tables or reproducible recipes;
- frozen split manifests;
- contamination and exposure audits;
- baseline and final-model code;
- accepted Apptainer definition files and image digests;
- release SIFs where distribution is permitted;
- model checkpoints;
- calibration objects and abstention policy;
- retrieval recipes and hypothesis catalogue;
- run manifests and headline result bundles;
- data card, model card, and claim-limit statement.

### 14.3 Required hypothesis warning

Every catalogue and network visualization must state:

> These pairs are computationally prioritized hypotheses. They have not been experimentally tested or validated by the iPIN-OpenPPI project. Scores are conditional on the stated training evidence, assay/search spaces, and model assumptions.

---

## 15. Deliverable acceptance checklist

The programme is complete only when:

- every production result was generated on Arrhenius through Apptainer;
- the primary assay and compatibility outputs are not conflated;
- no technical failure is encoded as a biological negative;
- the evidence warehouse preserves source conflicts and construct provenance;
- primary splits are immutable and contamination-audited;
- the baseline ladder is complete;
- every optional architecture branch has passed its gate;
- uncertainty improves selective prediction under shift;
- retrieval meets fixed recall budgets before a catalogue is released;
- the temporal test was run once after freeze;
- the final claims remain within the computational claim ceiling;
- final artifacts are reproducible from release SIFs and manifests; and
- the expert group approves the release wording.

---

## 16. Final programme statement

> iPIN-OpenPPI will develop evidence-aware, assay- and selection-conscious sequence models for prioritizing direct human heteromeric protein-protein interactions. The programme will distinguish testing, technical evaluability, context-dependent binding, and assay observation; evaluate under strict protein, homology, assay, source, species, interface, and temporal novelty; and produce a calibrated computational hypothesis catalogue. All computation will be executed by Codex on NAISS Arrhenius through immutable ARM64 Apptainer containers. The programme will make no claim of experimental validation and will proceed beyond month six only if its evidence, benchmark, statistical, container, compute, and architecture gates are passed.

---

## Appendix A. Intended repository and storage layout

The following layout is prescribed for execution but is not created by this document:

~~~text
ipin-openppi/
  blueprint/
  containers/
    definitions/
    locks/
    manifests/
    images/
  data/
    source_manifests/
    raw/
    staging/
    canonical/
    derived/
    splits/
  src/
    ingestion/
    warehouse/
    benchmark/
    models/
    retrieval/
    evaluation/
  configs/
  slurm/
  tests/
  artifacts/
    runs/
    checkpoints/
    embeddings/
    metrics/
    reports/
  releases/
  governance/
    decisions/
    risks/
    gates/
    licenses/
~~~

Raw and large generated data will reside on approved Arrhenius storage and will not be committed to source control.

---

## Appendix B. Minimum run-manifest fields

| Group | Fields |
|---|---|
| Identity | Run ID, parent run, task, start/end time, status |
| Source | Git commit, dirty-state flag, configuration hash |
| Container | SIF path, digest, definition/lock versions, Apptainer version |
| Scheduler | Slurm job ID, account, partition, nodes, tasks, GPUs, CPUs, walltime |
| Data | Source, canonical, evidence-policy, and split manifest hashes |
| Model | Backbone, checkpoint, trainable parameters, pair head, routing mode |
| Optimization | Seed, precision, batch tokens, optimizer, steps, schedule |
| Performance | Tokens/s/GPU, HBM, CPU memory, I/O wait, communication, checkpoint time |
| Outputs | Checkpoints, logits, calibration object, metrics, logs, report |
| Decision | Gate targeted, result, next authorized action |

---

## Appendix C. Selected official platform and data references

Platform and container guidance checked for this blueprint:

1. [NAISS Arrhenius technical description](https://www.naiss.se/resources/arrhenius-technical-description/).
2. [NAISS Arrhenius Quick Start](https://hpc.pages.naiss.se/user-documentation/support-docs/arrhenius_hpc/quickstart/).
3. [NAISS Arrhenius programming environments and mpprun guidance](https://hpc.pages.naiss.se/user-documentation/support-docs/arrhenius_hpc/software_development/programming_environment/).
4. [Apptainer User Guide](https://apptainer.org/docs/user/latest/).
5. [Apptainer GPU support](https://apptainer.org/docs/user/main/gpu.html).
6. [Apptainer support for Docker/OCI images and ARM64 architecture](https://apptainer.org/docs/user/latest/docker_and_oci.html).
7. [Apptainer definition-file guidance](https://apptainer.org/user-docs/master/definition_files.html).
8. [Apptainer signing and verification](https://apptainer.org/docs/user/latest/signNverify.html).

Primary data-resource guidance:

9. [HuRI downloads and terms](https://interactome-atlas.org/download).
10. [HuRI assay and search-space description](https://www.interactome-atlas.org/about/).
11. [IntAct data scope, licensing, and IMEx participation](https://www.ebi.ac.uk/intact/about).
12. [IntAct user guide and direct-interaction semantics](https://www.ebi.ac.uk/intact/documentation/user-guide).
13. [UniProt release-aware downloads](https://www.uniprot.org/help/regular_downloads).
14. [UniProt license](https://www.uniprot.org/help/license/).
15. [RCSB PDB data policy](https://www.rcsb.org/pages/policies).

Selected scientific basis:

16. [A reference map of the human binary protein interactome](https://www.nature.com/articles/s41586-020-2188-x).
17. [Data splitting to avoid information leakage with DataSAIL](https://www.nature.com/articles/s41467-025-58606-8).
18. [A flaw in using pretrained protein language models in PPI inference](https://www.nature.com/articles/s42256-025-01176-7).
19. [PLM-interact](https://www.nature.com/articles/s41467-025-64512-w).
20. [Paired sequence language modeling for PPI](https://www.nature.com/articles/s41467-026-70457-5).
21. [MINT](https://www.nature.com/articles/s41467-025-67971-3).
22. [SWING](https://www.nature.com/articles/s41592-025-02723-1).
23. [Experimental assessment of AI-based interactome mapping](https://www.nature.com/articles/s41467-026-70942-x).
24. [MSA Pairformer](https://www.sciencedirect.com/science/article/pii/S009286742600749X).
25. [SPPIDER-seq](https://pmc.ncbi.nlm.nih.gov/articles/PMC13330928/).
26. [ReCLIP preprint](https://www.biorxiv.org/content/10.64898/2026.06.01.729118v1).

---

## Document provenance

This final Version 3 blueprint incorporates:

1. the iPIN-OpenPPI Expert Project Blueprint, Version 2;
2. the Independent Technical Review and Feasibility Assessment;
3. the working-group response to that review;
4. the subsequent expert-group comments and feasibility memorandum;
5. confirmation that the expert group had no additional comments;
6. the decision that no laboratory or experimental work is possible;
7. the decision that Codex is the execution owner;
8. confirmation of Arrhenius compute and public-data authorization;
9. retention of the 24-month horizon and six-month gate; and
10. the requirement that all project computation use Apptainer on Arrhenius.

