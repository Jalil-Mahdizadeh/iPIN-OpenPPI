# ISSUE-0015: A new search finds homology links across frozen components

Opened: 2026-09-11. Status: open for broader transfer-claim resolution;
contained for the DEC-0047 homology-purged diagnostic.

The separately frozen DEC-0047 MMseqs2 search used only the 11,900 public
training endpoints, one high-sensitivity search without adaptive first-hit
termination, a shorter search-span floor and no search-coverage floor. An
additional integer postfilter recovered local alignments with both spans >=80,
both coverages >=20%, and E-value <=1e-3 that connect the accepted components.

At >=30% exact identity, 507 undirected links cross original components and 344
cross the three DEC-0046 internal folds. At >=40%, nine links cross both
components and folds. At >=20%, the corresponding counts are 11,085 and 7,843.
These are newly *detected* links; this audit does not establish whether the
difference is due to search parameters, database-size-dependent significance,
or another search heuristic. It is not proof of exhaustive homology coverage.

The old statement "component-disjoint under the frozen local_domain_union_30
graph" remains literally true. It cannot be strengthened into absence of all
alignments meeting the nominal threshold, unseen-family transfer, or an
exhaustive family split. Historical metrics are not arithmetically invalidated;
their homology interpretation is challenged. No hidden development or protected
endpoints/pairs were assessed here, and no original component assignment changed.

DEC-0047's prespecified purge removes the whole fitting component of every
outside endpoint linked to a heldout endpoint under the >=20% postfilter.
Direct cross-links remaining after that purge: zero in each of the three folds,
at all three reported identity thresholds. Models and normalizers are refit
after this removal. This containment addresses detected direct cross-links,
not all transitive remote families, short domains, or undetected homologues.

Evidence:
`artifacts/validation/homology_source_challenge_v1/HOMOLOGY_EDGE_AUDIT.json`.
The supporting audit was written after execution freeze and introduces no
new fitting rule, panel, metric, or success gate. The main numerical validator
also independently reconstructs every >=20% purge edge and all fitting masks.

Future stronger family-generalization claims require a separately governed
leakage definition and validation on fresh data. Do not silently overwrite the
accepted graph, regenerate spent splits, or rescore protected data as a fix.
