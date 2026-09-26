**Supplementary Table S3 | Complete bounded search**

| Encoder / recipe | Head parameters | Screen, epoch 3 | Ensemble, epoch 4 | Ensemble, epoch 8 |
| --- | --- | --- | --- | --- |
| 150m / linear_slow | 1,922 | 0.7814 | — | — |
| 150m / linear_base_lr | 1,922 | 0.7902 | 0.7860 | 0.7841 |
| 150m / linear_fast | 1,922 | 0.7769 | — | — |
| 150m / linear_regularized | 1,922 | 0.7776 | — | — |
| 150m / mlp_small | 126,915 | 0.7897 | — | — |
| 150m / mlp_wide | 496,131 | 0.8021 | 0.7994 | 0.7912 |
| 150m / mlp_fast | 249,987 | 0.7527 | — | — |
| 150m / residual_small | 128,837 | 0.7761 | — | — |
| 150m / residual_wide | 498,053 | 0.8052 | 0.7994 | 0.7938 |
| 150m / residual_fast | 251,909 | 0.7397 | — | — |
| 150m / bilinear_small | 22,434 | 0.7845 | — | — |
| 150m / bilinear_wide | 83,970 | 0.7534 | — | — |
| 650m / linear_slow | 3,842 | 0.7787 | — | — |
| 650m / linear_base_lr | 3,842 | 0.7827 | — | — |
| 650m / linear_fast | 3,842 | 0.7791 | — | — |
| 650m / linear_regularized | 3,842 | 0.7792 | — | — |
| 650m / mlp_small | 253,635 | 0.7913 | 0.7944 | 0.7875 |
| 650m / mlp_wide | 991,491 | 0.7792 | — | — |
| 650m / mlp_fast | 499,587 | 0.7347 | — | — |
| 650m / residual_small | 257,477 | 0.7639 | — | — |
| 650m / residual_wide | 995,333 | 0.7810 | — | — |
| 650m / residual_fast | 503,429 | 0.7538 | — | — |
| 650m / bilinear_small | 44,834 | 0.7617 | — | — |
| 650m / bilinear_wide | 167,810 | 0.7430 | — | — |

Screen scores use one seed; promoted ensemble scores use three. Dashes indicate recipes not promoted. The CSV retains every individual-seed evaluation, exact hyperparameters and checkpoint identifiers. These development-selected comparisons are not protected head-to-head tests.
