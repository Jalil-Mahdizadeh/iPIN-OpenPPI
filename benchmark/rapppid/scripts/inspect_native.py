"""Pre-build CPU smoke check; no candidate pairs, truth, or fitting."""
from pathlib import Path
import numpy as np
import torch
from pytorch_lightning.callbacks import ModelCheckpoint
import infer
from common import read
from native_model import load_model, learned_digest, tokenizer, encode, CHECKPOINT

model=load_model('cpu');spp=tokenizer()
with torch.serialization.safe_globals([ModelCheckpoint]):
    reference=infer.load_chkpt(str(CHECKPOINT)).eval().requires_grad_(False)
assert learned_digest(model)==learned_digest(reference)
meta=read('/sequences.json')
values=[encode(spp,s) for s in meta['sequence']]
print({'native_checkpoint_loaders_agree':True,'learned_state_sha256':learned_digest(model),
       'parameters':sum(p.numel() for p in model.parameters()),'sequences_tokenized':len(values),
       'max_effective_tokens':max(np.count_nonzero(x) for x in values),
       'min_effective_tokens':min(np.count_nonzero(x) for x in values),
       'training_performed':False,'test_pairs_read':False,'test_truth_read':False},flush=True)
