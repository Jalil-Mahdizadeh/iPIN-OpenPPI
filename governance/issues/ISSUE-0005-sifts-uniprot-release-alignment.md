# ISSUE-0005: Frozen SIFTS mappings and UniProt sequences are from different releases

**Status:** Open; non-blocking for source parsing, blocking for exact structural mapping and structure-derived labels
**Opened:** 2026-08-03
**Severity:** High structural-validity risk
**Owner:** Codex

## Observation

The frozen SIFTS chain files were observed on 2026-07-26. Their provider
headers state:

- `pdb_chain_uniprot.tsv.gz`: `PDB: 30.26 | UniProt: 2026.03`;
- `pdb_chain_taxonomy.tsv.gz`: `PDB: 30.26 | UniProt: 2026.03`; and
- `uniprot_segments_observed.tsv.gz`: the same 2026-07-26 snapshot family,
  although its first comment line does not name a UniProt release.

The independently frozen human reference proteome is UniProt release
`2026_02`. The files are individually intact and parse successfully, but they
are not release-aligned.

## Qualification diagnostics

The source-native parse retained 1,007,697 chain-to-UniProt mappings and
1,519,870 observed-segment mappings. It found 72 chain mappings whose reported
UniProt start coordinate is greater than the reported end coordinate; the
observed-segment file has zero such rows. These 72 records were preserved
verbatim. They may represent unusual constructs or circular permutations, but
that interpretation is not yet proven, so their endpoints must not be swapped
or normalized automatically.

A preliminary join through chains having at least one taxonomy row with
`taxid=9606` yielded 9,812 distinct SIFTS UniProt accessions. Of these, 8,947
match a frozen primary-accession field and another 84 match an explicitly
retained additional-sequence identifier, for a disjoint union of 9,031
accessions present in the `2026_02` sequence table; 781 are absent. This is a
diagnostic, not a final human-structure coverage estimate: a PDB chain can have
mixed or multiple taxonomy annotations, and identifier presence alone does not
prove sequence or residue-interval identity.

## Consequence

An accession or residue interval in SIFTS `2026.03` cannot automatically be
treated as an exact mapping onto a `2026_02` sequence. Between releases, an
entry may be added, removed, merged, split, re-versioned, or sequence-corrected.
Ignoring that possibility could shift interface residues or attach a structural
observation to the wrong sequence hash.

This is not a raw-integrity failure and does not block provenance-preserving
parsing. It blocks:

- declaring SIFTS residue mappings exact on the frozen `2026_02` proteome;
- admitting a PDB/SIFTS record as an interface-derived training label;
- using unmatched residue coordinates for construct-confidence A or B; and
- reporting structural coverage without an explicit release-alignment audit.

## Mandatory mitigation

- Preserve both source releases and their raw checksums independently.
- Do not silently remap, truncate, or shift residue coordinates.
- Treat every SIFTS-to-`2026_02` join as provisional until accession presence,
  sequence identity/version, and mapped-interval validity are checked.
- Exclude unresolved or sequence-conflicting mappings from structural label
  construction.
- Report missing accessions, sequence conflicts, invalid intervals, and the
  retained exact-match fraction.
- Individually adjudicate the 72 descending chain intervals; preserve their
  source direction and exclude them from exact mappings unless construct-aware
  evidence explains the coordinate semantics.

## Resolution paths

1. Acquire the matching UniProt `2026_03` human reference proteome through a
   new reviewed source manifest and use it for the structural mapping branch.
2. Obtain a checksum-frozen SIFTS snapshot explicitly generated against
   UniProt `2026_02`.
3. If neither aligned source is available, perform an accession- and
   sequence-hash-level cross-release audit and retain only mappings proven
   unchanged; this yields a restricted structural subset rather than full
   release alignment.

## Exit criteria

The issue closes only when one of the first two release-alignment paths is
completed and verified, or when the expert group approves the restricted
cross-release subset after a report demonstrates:

1. the fraction of SIFTS accessions present in each UniProt release;
2. exact sequence identity for retained accessions;
3. validity of every retained residue interval against the chosen sequence;
4. counts and reasons for every excluded mapping;
5. an explicit explanation or exclusion decision for all 72 descending
   chain-coordinate records; and
6. zero unresolved mappings in any structure-derived label set.

Source parsing and non-structural evidence reconciliation may proceed while
this issue remains open. Structural label construction and model training may
not.
