#!/usr/bin/env bash
set -euo pipefail
python3 -m venv --system-site-packages /work/runtime/venv
/work/runtime/venv/bin/pip install --disable-pip-version-check --no-index --find-links /work/runtime/wheels \
  'pytorch-lightning==2.5.1' 'torchmetrics==1.7.1' \
  'transformers==4.50.3' 'sentencepiece==0.2.0'
/work/runtime/venv/bin/pip freeze > /work/runtime/requirements.freeze.txt
/work/runtime/venv/bin/python - <<'PY'
import torch, transformers, pytorch_lightning, torchmetrics
print({'torch':torch.__version__, 'transformers':transformers.__version__,
       'pytorch_lightning':pytorch_lightning.__version__, 'torchmetrics':torchmetrics.__version__})
from xpair.model import XPairModel
print('Released X-PAIR import passed')
PY
