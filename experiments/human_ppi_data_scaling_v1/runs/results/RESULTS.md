# Human PPI data scaling results

Selected 31,188 positives, epoch 1, using the frozen C3-dev-2 macro objective.

All numbers below are P-versus-unlabeled concordance. Test-2 is a disclosed historical follow-up, not independent replication.

| Panel | Selected | Fresh 17k control | Frozen PU-TUnA | Optimized iPIN | Original iPIN |
|---|---:|---:|---:|---:|---:|
| C1:test_1 | 0.900615 | 0.924111 | 0.948620 | 0.916037 | 0.843493 |
| C1:test_1_reconciled | 0.898639 | 0.893008 | 0.915955 | 0.886095 | 0.817226 |
| C1:test_added | 0.875191 | 0.712128 | 0.726456 | 0.701373 | 0.671418 |
| C1:test_2_macro | 0.886915 | 0.802568 | 0.821205 | 0.793734 | 0.744322 |
| C1:test_2_macro_no_dev_overlap | 0.887232 | 0.804448 | 0.823093 | 0.795303 | 0.745586 |
| C2:test_1 | 0.860617 | 0.885417 | 0.880401 | 0.851301 | 0.805299 |
| C2:test_1_reconciled | 0.859031 | 0.879631 | 0.874597 | 0.845643 | 0.800423 |
| C2:test_added | 0.795270 | 0.672003 | 0.669781 | 0.654900 | 0.637329 |
| C2:test_2_macro | 0.827151 | 0.775817 | 0.772189 | 0.750272 | 0.718876 |
| C3:test_1 | 0.844384 | 0.867272 | 0.815875 | 0.807948 | 0.789249 |
| C3:test_1_reconciled | 0.833256 | 0.846269 | 0.801141 | 0.791534 | 0.775274 |
| C3:test_added | 0.740192 | 0.693900 | 0.686601 | 0.693593 | 0.676974 |
| C3:test_2_macro | 0.786724 | 0.770085 | 0.743871 | 0.742563 | 0.726124 |

Paired component-bootstrap intervals and differences are in `RESULTS.json`; point estimates and intervals are in `metrics.csv`.

Training sizes and epoch curves are in `../SELECTION.json`. Legacy panels retain their original labels; reconciled panels explicitly incorporate new positive evidence.

- The corpus expansion changes source composition and protein coverage as well as size.
- Fresh 17k control and all larger budgets share regenerated, positive-reconciled U.
- Original C1 dev/test U identities overlap; reconciliation promotes 57 shared pairs to P.
- An additional C1 test-2 view excludes every development candidate identity; the complete requested panels remain reported.
- Homology separation uses the declared heuristic graph, not an exhaustive homology guarantee.
- One nested corpus ordering; three fitting seeds do not measure alternative dataset-sampling uncertainty.
