# Exploratory sequence-similarity follow-up

After the primary diagnostics, original TUnA's EGFR retrieval was strongly
query-dependent and EGFR/GRB2/SHC1/CBL had no exact accession or sequence exposure
in the documented TRAIN/validation lists. This motivates a further diagnostic;
it was not specified before those results were observed.

Search every distinct query or nominated-positive endpoint against only original
public TRAIN/validation endpoints, using the already pinned MMseqs2 18-8cc5c
binary in the accepted data SIF. Use sensitivity 7.5, E-value <= 0.001, full
alignment identity, and allow all reference hits through count limits. Record
the strongest reported local match and strongest match covering >=80% of both
sequences, separately for TRAIN and validation. Report counts at >=30% and >=40%
identity with >=80% coverage of both sequences. These descriptive thresholds are
not a proof of independence or biological dissimilarity. The search is heuristic
and cannot rule out distant homology, shared domains, language-model exposure,
or undocumented checkpoint training/model-selection exposure. No original test
partition is opened, and no model is altered or selected.

For each nominated P pair, also report whether pairs between the >=30%-identity,
>=80%-coverage endpoint hits appear in the documented TRAIN/validation lists,
by their original labels. This is a source-overlap diagnostic, not a replacement
for the protein/component split used by the main benchmark.
