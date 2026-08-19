# iPIN-OpenPPI project status: local diagnostic revision 2 authorized

`DEC-0041` resolves one optional scorer ambiguity before any local embedding or
score exists. The bidirectional best-match diagnostic is removed. Exact matched
global, maximum-segment, and primary top-four segment cosine formulas are now
frozen by the revision-2 delta.

Everything else in `DEC-0040` remains unchanged: public training data only,
nested C3 primary evaluation, the permissive point trigger, conditional low-
capacity C1 fitting only if triggered, and no development/protected access.

The authoritative ledger is `governance/gates/gate_status_v40.yaml`.
