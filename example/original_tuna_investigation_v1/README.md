# Original TUnA investigation

Start with the [report](REPORT.md) and [figure](investigation.png)
([PDF](investigation.pdf), [SVG](investigation.svg)). This is an exploratory,
read-only-model investigation of the completed
[twelve-target comparison](../twelve_target_comparison_v2/REPORT.md).

The evidence supports a reproducible query-dependent strength, especially on
EGFR. Original TRAIN contains positive pairs between the closest reported local
sequence relatives of all three EGFR positives; the analogous pairs are absent
from the retraining TRAIN/development inputs. EGFR dominates the net macro lead.
This suggests transfer from related proteins, without proving training-example
causality or general superiority.

The [protocol](PROTOCOL.md), [input freeze](INPUT_FREEZE.json),
[post hoc homology protocol](HOMOLOGY_FOLLOWUP.md), and
[final manifest](FINAL_MANIFEST.json) document scope, sequence/cache reuse, input
hashes, and preservation. [Independent validation](INDEPENDENT_VALIDATION.json)
checks 1,800 diagnostic metric rows with scikit-learn and independent fractional
top-K calculations. All 107 parent scientific artifacts remain unchanged.

## Reproduction

Run in a **new output copy** of this folder with no completed freezes/outputs;
do not overwrite this completed record. Keep the same directory depth beneath
the repository's `example/` folder, because scripts locate their inputs relative
to that layout. Copy the Python scripts, Markdown documents, and the two
`relative_protein_names` source snapshot files into that new folder. Scripts require the parent run's ignored arrays, original public
TRAIN/validation sources, frozen checkpoints, and the pinned local MMseqs binary.

Use `ipin-data-arm64_0.1.2.sif` for preparation, statistical analyses, homology,
validation, and figures. Use `benchmark/containers/images/tuna-arm64-v1.sif`
with one allocated GPU, `--nv`, and `PYTHONPATH=/opt/tuna/vendor` for native
checkpoint verification and query replacement. Bind the repository read-only
and only the new output copy writable; set `PYTHONDONTWRITEBYTECODE=1` and a
writable `MPLCONFIGDIR`.

Run the following Python entry points in order:

1. `investigate.py prepare`
2. `investigate.py analyze`
3. `gpu_diagnostics.py`
4. `investigate.py swaps`
5. `homology_followup.py`
6. `relative_pair_audit.py`
7. `summarize.py`
8. `validate.py`
9. `validate_followups.py`
10. `finalize.py`

The core protocol was recorded after seeing the parent scores. The homology and
relative-pair diagnostics were added after inspecting the first audit results;
all are descriptive. Query-replacement labels remain those of the original
target and are not biological labels for the new pairs. All U remain unlabeled.

Compact scientific CSV/JSON outputs and figures are public. The full replacement
score array, MMseqs temporary databases, upstream sequences, and embeddings stay
local and are hash-recorded. No frozen model is retrained, tuned, or re-registered.
