# Pre-fit launcher erratum, 2026-09-11

The first launch failed before fixture execution, baseline replay, `FIRST_FIT`
or any research fit/score. Pytest's auto-loaded `pytest_rerunfailures` plugin
tried to create a localhost socket and raised a DNS error in the isolated
container. This was an infrastructure failure, not a failed model, numerical
check, or observed development result. The aborted process used 1.990 seconds.

Disable external pytest plugin autoload (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`),
and persist captured fixture output before propagating subprocess failures.
No model, recipe, budget, ordering, input, promotion, metric or gate changes.
The original freeze SHA-256 is
`28b70556713145ade6b2ee59da900aca80395ab66f2b142ade8941a826e9cbb5`.
Preserve that complete bundle and its empty-result launch under
`.private/model_optimization_v1_prefit_plugin_failure`, and preserve the public
initial freeze as `SEARCH_FREEZE_PREFIT_PLUGIN_FAILURE.json`. Re-freeze the
launcher repair before the first actual fit. This is continuation of the
authorized experiment after a pre-fit tooling repair, not another scientific
search or a relaxation of the fail-closed result gate. Charge two seconds of
the two-hour budget to this failed launch.
