"""Write the final reference-study report and bind its completed artifacts."""
from collections import Counter

from evaluation_utils import *


def fmt(value, digits=3):
    return f"{float(value):.{digits}f}" if value not in (None, "") else "not estimable"


def estimate(row, metric):
    text = fmt(row[metric])
    if row[metric + "_ci_low"] is not None:
        text += f" [{fmt(row[metric + '_ci_low'])}, {fmt(row[metric + '_ci_high'])}]"
    return text


def main():
    container()
    require(not (OUT / "FINAL_MANIFEST.json").exists(), "Refusing to replace a finalized study")
    validation = read(OUT / "RESULT_VALIDATION.json")
    require(validation["status"] == "passed", "Independent result validation required")
    verify(validation["analysis"])
    analysis = read(OUT / "ANALYSIS.json")
    freeze = read(OUT / "INPUT_FREEZE.json")
    for item in freeze["files"] + analysis["outputs"] + analysis["model_outputs"]:
        verify(item)
    ipin, tuna = read(OUT / "IPIN_RUN.json"), read(OUT / "TUNA_RUN.json")
    for item in (ipin["score_artifact"], tuna["output"]):
        verify(item)
    for item in ipin["verified_model_inputs"] + tuna["verified_model_inputs"]:
        verify(item)
    metrics = analysis["metrics"]
    full = [r for r in metrics if r["cohort"] == "all_mapped_assays"]
    sensitivity = [r for r in metrics if r["cohort"] == "no_exact_train_or_development_endpoint"]
    mapping = read(OUT / "PANEL_SELECTION.json")["comparison"]
    exposure = read(OUT / "EXPOSURE_AUDIT.json")
    endpoints = {r["sequence_sha256"]: r for r in table(OUT / "exact_endpoint_exposure.csv")}
    similarity = {r["sequence_sha256"]: r for r in table(OUT / "training_sequence_similarity.csv")}
    by_species = []
    for taxid, name in ((559292, "S288C"), (9606, "Human")):
        proteins = [r for r in table(OUT / "published_proteins.csv") if int(r["taxid"]) == taxid]
        by_species.append({"taxid": taxid, "organism": name, "proteins": len(proteins),
            "exact_train": sum(boolean(endpoints[r["sequence_sha256"]]["exact_TRAIN_endpoint"]) for r in proteins),
            "exact_development": sum(boolean(endpoints[r["sequence_sha256"]]["exact_DEV_endpoint"]) for r in proteins),
            "train_homolog_30pct_both80": sum(boolean(similarity[r["sequence_sha256"]]["TRAIN_homolog_30pct_both80"]) for r in proteins),
            "similarity_bins": dict(Counter(similarity[r["sequence_sha256"]]["similarity_bin"] for r in proteins))})
    write_json(OUT / "EXPOSURE_SUMMARY.json", {"organisms": by_species,
        "exact_pair_counts": exposure["exact_pair_counts"], "pretraining_exposure_audited": False})
    lines = [
        "# Frozen human PPI models on published human–S288C assay confirmation", "",
        "Completed reference-organism evaluation. All three registered ensembles were applied unchanged to 1,555 published pairs.", "",
        "## Findings", "",
        f"The primary comparison contains {full[0]['pairs']} published assay outcomes: {full[0]['confirmed']} confirmed and {full[0]['unconfirmed']} unconfirmed.",
        "The endpoint is the authors' orthogonal-assay confirmation call. Unconfirmed pairs are not established biological noninteractions.", "",
        "| Frozen model | AUROC [95% interval] | Average precision [95% interval] | Spearman with assay score |",
        "|---|---:|---:|---:|",
    ]
    for row in full:
        lines.append(f"| {MODEL_NAMES[row['model']]} | {estimate(row, 'AUROC')} | {estimate(row, 'AP')} | {fmt(row['Spearman_assay_score'])} |")
    lines += ["", f"The AUROC chance reference is 0.5. The AP prevalence reference is {fmt(full[0]['AP_prevalence_reference'])}.", ""]
    above = [MODEL_NAMES[r["model"]] for r in full if r["AUROC_ci_low"] is not None and r["AUROC_ci_low"] > .5]
    below = [MODEL_NAMES[r["model"]] for r in full if r["AUROC_ci_high"] is not None and r["AUROC_ci_high"] < .5]
    if above:
        lines.append("The exploratory AUROC interval is above 0.5 for " + ", ".join(above) + ". This supports signal for this fixed assay-confirmation endpoint within this study.")
    elif below:
        lines.append("No model has an AUROC interval wholly above 0.5. The interval is below 0.5 for " + ", ".join(below) + ", indicating reversed ordering for this assay endpoint.")
    else:
        lines.append("No model's exploratory AUROC interval is wholly above 0.5. This evaluation does not provide clear evidence of above-chance assay-confirmation ranking on the fixed cohort.")
    lines += ["", "These results do not establish performance on human pathogens, discovery of new interactions, or performance against verified biological noninteractions.", "",
              "![Assay-confirmation results](assay_confirmation.png)", "",
              "## Exposure sensitivity", "",
              f"Excluding pairs with either exact TRAIN or development endpoint leaves {sensitivity[0]['pairs']} assay pairs ({sensitivity[0]['confirmed']} confirmed, {sensitivity[0]['unconfirmed']} unconfirmed).", "",
              "| Frozen model | AUROC [95% interval] | Average precision [95% interval] |",
              "|---|---:|---:|"]
    for row in sensitivity:
        lines.append(f"| {MODEL_NAMES[row['model']]} | {estimate(row, 'AUROC')} | {estimate(row, 'AP')} |")
    retained_signal = [MODEL_NAMES[r["model"]] for r in sensitivity if
                       r["AUROC_ci_low"] is not None and r["AUROC_ci_low"] > .5]
    if retained_signal:
        lines += ["", "The exposure-filtered AUROC interval remains above 0.5 for " +
                  ", ".join(retained_signal) + ". This sensitivity is smaller and has wider uncertainty."]
    lines += ["", "Exact endpoint exposure across the complete published dataset:", "",
              "| Organism | Proteins | Seen in TRAIN | Seen in development | TRAIN homolog ≥30% identity, ≥80% coverage of both |",
              "|---|---:|---:|---:|---:|"]
    for row in by_species:
        lines.append(f"| {row['organism']} | {row['proteins']} | {row['exact_train']} | {row['exact_development']} | {row['train_homolog_30pct_both80']} |")
    lines += ["", "TRAIN and development endpoint counts may overlap. Exact pair overlap counts: " + ", ".join(f"{k}={v}" for k,v in exposure["exact_pair_counts"].items()) + ".",
              "The audit used actual human TRAIN/development files and pinned MMseqs2. Protected test-pair identities and truth were not opened. Protein-language-model pretraining exposure was not audited.", "",
              "## Paired model comparisons", "", "Primary-cohort differences; model A minus model B:", "",
              "| Model A | Model B | AUROC difference [95% interval] |", "|---|---|---:|"]
    for row in analysis["paired_differences"]:
        if row["cohort"] == "all_mapped_assays" and row["metric"] == "AUROC":
            lines.append(f"| {MODEL_NAMES[row['model_a']]} | {MODEL_NAMES[row['model_b']]} | {fmt(row['difference_a_minus_b'])} [{fmt(row['ci_low'])}, {fmt(row['ci_high'])}] |")
    primary_differences = [r for r in analysis["paired_differences"] if r["cohort"] == "all_mapped_assays" and r["metric"] == "AUROC"]
    if all(r["ci_low"] is not None and r["ci_low"] <= 0 <= r["ci_high"] for r in primary_differences):
        lines += ["", "Every primary paired AUROC interval includes zero. The observed model ordering does not establish a clear difference between models on this cohort."]
    lines += ["", "## Source, mapping and limitations", "",
              "The source is the published human–yeast study by Zhong et al. (2016), [PMID 27107014](https://pubmed.ncbi.nlm.nih.gov/27107014/), and archived IntAct release 252.",
              f"Table EV7 has {mapping['published_assay_rows']} calls ({mapping['published_calls']['yes']} yes, {mapping['published_calls']['no']} no). The same source-identity rule retained {mapping['included_assay_rows']} rows and excluded 16 rows (11 yes, 5 no) that did not map to exactly one verified eligible sequence pair through Table EV2's identifiers.",
              "See [comparison_mapping_audit.csv](comparison_mapping_audit.csv) for every decision. Unequal attrition by outcome limits representativeness; no sequence or isoform was selected using model scores.",
              "All retained assay pairs are within the previously reported positive network. The comparison asks whether model scores track confirmation in a different assay; it does not estimate retrieval among arbitrary human partners. The other published-pair scores are descriptive outputs.",
              "Reference-sequence taxonomy is supported by archived records; every historical construct or culture was not independently authenticated. K-12 was reviewed but omitted from the primary cohort because only four published pairs were available.", "",
              "## Uncertainty and validation", ""]
    for name, details in analysis["bootstrap"].items():
        lines.append(f"- `{name}`: {details['components']} connected components, largest component {details['largest_component_pairs']} pairs, {details['valid_draws']} valid draws from 10,000.")
    lines += ["", "Intervals resample connected components of the shared-endpoint graph, with identical draws across models and seed 20260921. They are exploratory and conditional on one publication and assay context; they do not demonstrate replication across studies. Spearman values are descriptive.",
              "All 4,216 selected source evidence records were checked against original XML. The independent result audit used a separate worksheet reader, explicit repeated-observation bootstraps, sklearn metrics, and independently reconstructed graph components.",
              f"Independent validation passed; maximum checked metric/interval error was {validation['maximum_point_or_interval_error']:.3g} (tolerance 1e-12). Both iPIN models passed pair-order checks. TUnA passed native-path agreement, pair-order symmetry, and parameter/buffer preservation for all three ensemble members.", "",
              "## Artifacts and reproduction", "",
              "[Input freeze](INPUT_FREEZE.json) · [Evaluation protocol](EVALUATION_PROTOCOL.md) · [Independent validation](RESULT_VALIDATION.json) · [Final checksums](FINAL_MANIFEST.json)", "",
              "- [All published-pair scores](all_model_scores.csv)",
              "- [Assay outcomes, exposure flags and model scores](assay_model_scores.csv)",
              "- [Metrics](metrics.csv) and [paired differences](paired_differences.csv)",
              "- [PDF figure](assay_confirmation.pdf) and [SVG figure](assay_confirmation.svg)",
              "- [Reproduction commands](REPRODUCE.md)", "",
              "Data attribution: EMBL-EBI IntAct / IMEx and original authors, [CC BY 4.0](https://www.ebi.ac.uk/intact/about). No model was retrained, recalibrated or selected using these outcomes.", ""]
    with (OUT / "REPORT.md").open("x") as handle:
        handle.write("\n".join(lines))
    write_json(OUT / "RUNTIMES.json", {"data_image_lock": record(ROOT / "containers/locks/ipin-data-arm64_0.1.2.sif.sha256"),
        "data_image_qualification": record(ROOT / "containers/manifests/ipin-data-arm64_0.1.2.qualification.json"),
        "ipin_image_sha256": ipin["SIF_sha256"], "tuna_image_sha256": tuna["SIF_sha256"],
        "ipin_seconds": ipin["elapsed_seconds"], "tuna_seconds": tuna["elapsed_seconds"],
        "ipin_device": ipin["device"], "tuna_device": tuna["device"]})
    # Include every public study artifact; large reproducible feature caches stay local.
    files = [p for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "FINAL_MANIFEST.json" and
             not p.name.endswith(".npz")]
    write_json(OUT / "FINAL_MANIFEST.json", {"at_utc": now(), "status": "complete_reference_assay_evaluation",
        "study_id": "reference_organism_transfer_v1", "published_pairs_scored": analysis["published_pairs_scored"],
        "primary_assay_pairs": full[0]["pairs"], "unexposed_assay_pairs": sensitivity[0]["pairs"],
        "models": list(MODELS), "source_metadata_only": False, "validation_status": validation["status"],
        "model_retraining_or_calibration": False, "protected_test_records_read": False,
        "biological_noninteraction_claim": False, "files": [record(p) for p in files],
        "local_features": [ipin["embedding_artifact"], tuna["residues"]]})
    print("Final report and checksum manifest written", flush=True)


if __name__ == "__main__":
    main()
