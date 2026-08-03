# Evidence warehouse schemas

The warehouse is evidence-record first. A provider pair list is a source view,
not an experimental record, and no schema field turns an unreported pair or a
technical failure into a biological negative.

Version 1 separates interaction evidence, participants, participant features,
provider pair views, sequences, identifier mappings, HuRI search-space/ORF
metadata, SIFTS mappings, and parse-audit records. Null scalar values are
permitted only when the record-level `missingness_json` states why the source
field is unavailable.
