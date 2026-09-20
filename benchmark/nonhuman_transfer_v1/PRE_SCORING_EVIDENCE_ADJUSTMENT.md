# Evidence adjustment before any model scoring

The initial metadata-only filter required MI:0407 and excluded every recorded
participant feature. It yielded only 10 eligible mouse targets, 7 fly, 1 worm,
77 yeast, 41 Arabidopsis, and 33 E. coli targets with at least two positives.
Those counts and exclusion reasons remain in `source_feasibility.csv`,
`SOURCE_PARSING.json`, and the original `*_SOURCE_AUDIT.json` files. The exact
original parser is retained as `initial_strict_parser.py` (the checksum matches
the first audit's parser record, whose original filename was `parse_sources.py`).
The acquisition-time protocol is retained byte-for-byte as `initial_protocol.md`;
its checksum matches the historical `SOURCES.json` protocol entry. `PROTOCOL.md`
is the revised protocol that will be bound by the inference input freeze.

This filter discarded standard reporter/affinity tags and binary two-hybrid
records curated under physical association rather than MI:0407. Before any
panel selection or model inference, revise the evidence eligibility to:

- MI:0407, or MI:0407/MI:0915/MI:0914 supported by a two-hybrid method under
  MI:0018 in the archived IntAct controlled vocabulary;
- allow features under the experimental tag term MI:0507; reject every other
  participant feature, including annotated mutations and binding fragments;
- retain all other taxid, protein, sequence, negative/modelled/expansion,
  publication, and deduplication requirements.

The PSI-MI ontology and original XML determine these categories. Neither model
scores nor human test pair labels informed this change. The revised parser
emits distinct `_v2` files and does not replace the initial feasibility audit.
This is a reference-sequence PU ranking study with assay-specific evidence,
not a claim that all source experiments measured full-length native binding.
