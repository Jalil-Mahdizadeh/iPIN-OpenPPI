# ISSUE-0006: IM-30553 is preview-only in current IntAct services

**Opened:** 2026-08-04

**State:** Open; controlled for the bounded audit

The official IMEx study page reports that IM-30553 has been curated but is not
yet integrated into services. The editor-service HTML, PSI-MI XML 3.0 expanded,
MITAB 2.7, and MIJSON exports are therefore frozen as a dated provider preview,
not as part of IntAct Release 252.

Controls:

- preserve each provider representation and its own SHA-256;
- record the query-page status and retrieval timestamp;
- reconcile preview evidence against the paper/archive without silently
  selecting one representation as ground truth;
- never add preview rows to the frozen IntAct canonical tables; and
- revisit integration state only through a new versioned acquisition and
  governance decision.

This issue does not block the semantics audit. It blocks any claim that the
preview is a released or stable IntAct snapshot.

## Audit outcome

The completed bounded audit froze HTML, PSI-MI XML 3 expanded, MITAB 2.7, and
MI-JSON representations. XML and MITAB independently enumerate 9,595 unique
interaction records. All MITAB negative flags are missing, confirming that the
preview is not an attempted-negative ledger. The issue remains open for any
future integration-state refresh.
