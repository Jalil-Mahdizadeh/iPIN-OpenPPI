# DEC-0034: Authorize nullability-only development loader correction

**Date:** 2026-08-19

**Status:** Accepted and effective only for the exact technical correction in
`ISSUE-0009`; development scoring is paused pending repeated production and
independent qualification

**Controlling records:** `DEC-0028`, `DEC-0032`, `DEC-0033`, gate v32, and
`ISSUE-0009`

## Decision

Authorize a single implementation-only correction to the released-development
row loader: pass `promote_options="permissive"` to `pyarrow.concat_tables` so
positive and U tables whose fields differ only in nullable metadata can be
concatenated. Authorize one focused regression fixture and the minimum audit/
independent-validator revision needed to requalify the corrected source.

The option delegates only Arrow schema unification. The loader must continue to
select the exact frozen columns, positive rows first and U rows second, and must
retain every value, row, logical type, state, rational weight, and within-state
order. Every existing census, uniqueness, finiteness, and hash guard remains.

## Incident boundary

The first scoring attempt at commit
`fad57a76e2c956eda29aaa8b673de53773d5d07b` stopped in `load_cell_rows` before
`deterministic_scores` was called. Its recoverably preserved private tree has no
files. The development release itself passed and is not repeated.

No score, metric, model selection, bootstrap, or scientific result exists from
the failed attempt. No checkpoint, embedding, pair package, ciphertext, or
configuration changed. Protected candidates, truth, and keys remain sealed.

## Requalification requirement

Before scoring resumes:

1. freeze the exact corrected source and focused fixture in a clean commit;
2. rerun the no-key production pre-release audit to a new immutable report;
3. only after that evidence is committed, implement a new clean-room validator
   fixed to the corrected source hash;
4. freeze its passing report; and
5. record a numbered acceptance reactivating scoring from the already released,
   hash-verified development package.

Neither validator may inspect development pair identities, scores, or private
keys. A requalification failure stops execution. A second development
decryption is prohibited.

## Continuing prohibitions

All `DEC-0032`/`DEC-0033` scientific boundaries remain: no training, tuning,
checkpoint change, scorer addition, benchmark alteration, negative or pseudo-
negative construction, protected access, external panel, structure/residue/
interface work, or adaptive criterion.
