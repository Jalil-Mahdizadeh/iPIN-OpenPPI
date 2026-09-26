# Pre-fit execution refinement

Before any formal training, new development evaluation, or job submission, the
initial execution snapshot was archived under `runs/prefit_v0/` rather than
overwritten. The final prospective configuration adds:

- Per-recipe file locking so the interactive GPU can start the mean control
  while the four-GPU job is queued, without duplicate fits or concurrent writes.
- An epoch-1 development checkpoint to detect early overfitting. The new batch
  of 256 has more optimizer updates per epoch than the historical pooled-head
  search's batch of 8,192; later checkpoints remain 2, 4, 6 and 8.
- Eight-hour training and four-hour comparison reservations, based on discarded
  TRAIN-only pilots, to improve scheduling while retaining a generous margin.

No new candidate development or test outcome informed these changes. The model
definitions, optimizer, loss, seeds, promotion threshold, and test estimand are
unchanged. Qualification records predate formal fitting; the final execution
freeze records the exact source and configuration actually used.
