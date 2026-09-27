# Execution status

- Input preparation and historical-parent hashing: complete.
- Sequence identity checks and raw pooled-feature extension: complete, exact replay.
- All-sequence homology search: complete (918,272 reported alignments).
- Independent synthetic qualifications: 11 tests passed; macro oracle error 2.22e-16.
- Implementation and clarified protocol freeze: complete.
- Six endpoint-only train2 fits: complete, all six fixed five-pass runs.
- Candidate-only control scoring and prediction freeze: complete, 17 predictors across 12 cohorts.
- Dev2/test2 primary evaluation: complete, seven macro views with both constituent cohorts and 2,000 paired component draws.
- C3 within-anchor and partner-swap diagnostics: complete for both development/test cohorts and their equal-cohort macros; all support floors passed.
- Independent final validation: passed, 7,547,402 candidate rows and 1,089 interval/contrast checks.
- Existing selected-31k test2 point estimates and all paired bootstrap draws: exact replay.
- Historical preservation: all 54 frozen parent files unchanged; no train/evaluation candidate overlap.
- Reports, figures, interpretation and compact publication inventory: complete.

The selected 31k model remained frozen. No outcome-guided fitting, checkpoint
selection or score-direction changes were performed. This remains a follow-up
on previously examined test2 data, with pointwise intervals.

The original final validator stopped on a 1e-12 full-panel arithmetic tolerance.
The retained precision audit explains the maximum 1.49e-11 discrepancy through
FP64 summation order. The separate final validator passed with a documented
1e-10 tolerance for that comparison and the original 1e-12 tolerances elsewhere.
Scientific outputs were unchanged; see [the numerical audit](validation/README.md).
