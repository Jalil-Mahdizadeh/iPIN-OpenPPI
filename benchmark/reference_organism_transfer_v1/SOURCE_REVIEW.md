# Published reference-organism source review

The primary dataset contains 1,555 published positive pairs,
545 S288C proteins, 466 human proteins,
and 4,216 original evidence records from
[PMID 27107014](https://pubmed.ncbi.nlm.nih.gov/27107014/).
Every selected record was checked against the original XML for participant
identity, reference sequence, publication, method, assay host, and features.

K-12 is an eligible reference label but has only four available positive pairs
across three nonhuman proteins. It is not part of this primary pilot.

The explicit negative-member review covered 46 archive
members and 939 interaction records. It found
0 exact reference/human binary candidates.
This is not an exhaustive audit of all published comparison data.

Source preparation is complete. Ranking evaluation is not ready: an appropriate
published comparison set, TRAIN/development exposure audit, and inference input
freeze remain required. No scores were read or generated, and no missing pair
was assigned a negative label. All retained pairs come from a single study.
See [PROTOCOL.md](PROTOCOL.md) for scope and interpretation.
