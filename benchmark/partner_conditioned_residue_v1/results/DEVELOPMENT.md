# Development comparison

All values are full C3-development weighted P-versus-U concordance.

| Recipe | Selected epoch | Three-seed ensemble | Promoted |
|---|---:|---:|---|
| mean_pool | 1 | 0.779090 | True |
| attention_pool | 1 | 0.795853 | False |
| cross_attention | 2 | 0.805475 | True |
| cross_attention_wide | 2 | 0.790064 | False |

Promotion reference: frozen PU-TUnA C3 development = 0.804455803538.

All three seeds were retained. Selection used development only. Development gains are post-selection and exploratory.
