# Git publication scope

Git includes the completed implementation, protocol, original report and
interpretation, input/prediction/final manifests, validation records, comparison
figures, and all public score, metric, exposure and rank tables. These are the
existing within-species and laboratory-yeast reference panels described in
the [report](REPORT.md). No inference or analysis was repeated for deposition.

In each of `nonhuman_transfer_v1/` and `reference_organism_pu_transfer_v1/`,
three large tables are stored as lossless gzip files:

- `all_model_scores.csv.gz`
- `default_model_scores.csv.gz`
- `exact_pair_exposure.csv.gz`

All other public tables retain their original filenames and bytes. Standard
gzip readers and `pandas.read_csv` read the compressed tables directly. To
restore the original `.csv` names in a fresh checkout, run from this directory:

```bash
python3 - <<'PY'
from pathlib import Path
import gzip
import shutil
for source in Path('.').glob('*/*.csv.gz'):
    with gzip.open(source, 'rb') as src, source.with_suffix('').open('xb') as dst:
        shutil.copyfileobj(src, dst)
PY
```

Exclusive creation prevents overwriting an existing CSV. The original local
CSVs remain unchanged and their SHA-256 hashes in `FINAL_MANIFEST.json` still
apply after decompression. The [deposit manifest](../../artifacts/reports/repository_deposit_v1/PUBLICATION_MANIFEST.json)
records both compressed and original hashes and sizes.

Generated endpoint embeddings, logs and runtime caches remain local. The
historical input/model/image dependencies also remain in their original
locations. `FINAL_MANIFEST.json` describes the complete local scientific run,
including those omitted products; it is not a claim that every listed local
file is in Git. See the [repository deposit inventory](../../DEPOSIT.md).
