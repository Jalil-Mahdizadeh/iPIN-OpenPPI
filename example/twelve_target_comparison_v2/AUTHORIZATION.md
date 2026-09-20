# Application extension scope

On 2026-09-20 the user requested:

> just add the best low plausibility U pairs carefully, then re-apply all 3 frozen ipin models + original tuna model. the compare all previous metrics for P + 50 context-matched U, P + 50 background U, P + low-plausibility U, P + context-matched and backround U, P + all U.

The preceding request defined 50 additional U per positive, bringing each
positive's matched pool to 150 U. This version preserves the twelve targets,
37 nominated positives, and 3,700 existing U. It adds 1,850 distinct
target–candidate pairs with score-independent biological selection and records
the evidence strength separately from the U label. No U is called a verified
noninteraction. The selection protocol records the final quota and any
clarification before new inference. The user subsequently selected:

> Keep 50 with explicit evidence tiers (recommended)

The authorized predictors are the unchanged three-model iPIN registry v2 and
the already preserved published original TUnA comparator. No checkpoint,
normalizer, encoder, GP covariance, or ensemble rule is trained or selected.
All sequences are fetched again and both embedding pipelines run afresh.
The five requested candidate sets receive the complete previous retrieval
metric suite. Prior completed applications and their checksum-bound records
are preserved in their original locations; this folder is a new version.

This is descriptive application analysis on previously examined targets, not a
new protected benchmark evaluation. Protected test pairs, scores, truth, and
quarantined negative evidence are not inputs. Existing TRAIN/development and
documented original-TUnA training/validation records are used solely to exclude
new exposed U and to disclose exposure sensitivity.
