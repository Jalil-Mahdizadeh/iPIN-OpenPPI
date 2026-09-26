# Git publication scope

Published on 26 September 2026 with the [repository deposit](../../DEPOSIT.md).
The completed experiment is preserved; no training, selection or evaluation
was repeated for publication.

Git includes `scripts/`, configuration and launchers, the protocol and final
review, all `audit/` records, compact run qualification/freeze/selection records,
and the full aggregate tables and learning-curve figures in `runs/results/`.
Each of the 12 fits has its per-epoch JSON summaries, `events.jsonl` training
history and completion record. Residue-cache manifests identify the encoder
and local feature assets without redistributing those tensors.

Training/development matrices, protected test pairs and labels, curation
payloads, model checkpoints, residue/pooled embeddings, prediction arrays,
scratch files and scheduler logs stay local. Their recorded hashes, source
identities and construction code are retained. A public checkout supports
inspection of the design, selection and results; a full rerun additionally
requires the frozen inputs, model/runtime assets and protected-data access
described in the original records. There is no new public download claimed
for those local assets.

Start with [FINAL_REVIEW.md](FINAL_REVIEW.md), then
[RESULTS.md](runs/results/RESULTS.md) and
[SELECTION.json](runs/SELECTION.json). The original protocol, run artifacts and
promoted v3 evidence retain their existing bytes and scientific meaning.
