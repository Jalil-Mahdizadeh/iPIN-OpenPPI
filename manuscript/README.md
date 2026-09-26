# iPIN-OpenPPI manuscript package

**Historical draft scope:** this package describes the original affine and
optimized pooled iPIN studies. It predates the 31k promotion and X-PAIR/test2
comparisons and is not a manuscript for the current default model. The authored
text, figures and scientific source data are preserved. See the repository's
[current model documentation](../docs/models/FROZEN_PAIR_MODELS_v3.md) and
[experiment index](../experiments/README.md) for later work.

This is a complete first manuscript draft with six main figures, one supplementary figure, two main tables, four supplementary tables and 34 verified references. All scientific plots reproduce frozen aggregate outputs. No models were fitted, no protected evaluation was rerun, and the existing repository was mounted read-only for computational work.

## Package contents

| Path | Content |
|---|---|
| `manuscript.md` | Main text, Methods, two embedded tables and a readable reference list; Pandoc citation keys retained |
| `supplementary.md` | Necessary reproducibility details, four supplementary tables and Supplementary Fig. S1 |
| `figure-legends.md` | Standalone full legends for all figures |
| `references.bib` | Full-author, DOI/URL-verified BibTeX bibliography |
| `figure-1.png` … `figure-6.png` | Main figures, 600 dpi PNG |
| `figure-1.csv` … `figure-6.csv` | Complete source data for the corresponding figure, including all quantitative panels |
| `figure-s1.png`, `figure-s1.csv` | Supplementary paired-control comparison and source data |
| `tables/` | Each table as a readable Markdown file and corresponding CSV |
| `source-data/snapshots/` | Portable, field-restricted copies of authoritative aggregate results/configuration |
| `source-data/source-manifest.csv` | Original source paths, SHA-256 hashes, byte counts and snapshot names |
| `source-data/implementation-provenance.csv` | Hashes and relevant symbols for inspected scientific code |
| `source-data/claim-values.csv`, `ancillary-claim-values.csv` | Exact numerical values supporting additional prose claims |
| `source-data/references/verified-references.json` | Checked citation metadata and primary verification links |
| `source-data/package-validation.json` | Latest package checks |
| `source-data/portable-regeneration.json` | Independent copied-package regeneration: 21 artifacts reproduced byte-for-byte |
| `scripts/` | Extraction, plotting, table/reference rendering, validation and DOCX preparation |
| `build/` | Conversion-ready main and supplementary Markdown with figure assembly |
| `result-provenance.md` | Internal source/key map for every figure, table, major claim and equation |
| `requirements.txt` | Exact plotting/data-library versions used in the dedicated model SIF |

The authoritative scientific roles remain explicit: the original affine evaluation is confirmatory; the optimized evaluation is a disclosed follow-up on the same previously examined test. Its primary C3 improvement interval crosses zero. Internal partner/homology/source fits are separate diagnostic models. Missing marginal intervals and development estimates have not been imputed.

Only the Data availability and Code availability deposit/access/licence fields are marked as submission placeholders. Author, affiliation and institutional sections were intentionally omitted. The package contains aggregates rather than protected pair identities, model weights or licensed source payloads.

## Figure and table generation

`extract_results.py` reads field-restricted snapshots (or, only when explicitly refreshing them, the original aggregate JSON files) and writes the long-form figure CSVs. The numerical source includes model, condition, dataset, metric, estimate, confidence limits where reported, sample counts and source keys. The schematic CSV records entities, labels, partition counts and processing relationships.

`plot_figures.py` reads each figure's same-basename CSV. All plots use Matplotlib with a consistent gold/purple/teal C1/C2/C3 encoding and 600 dpi PNG output. It does not create PDF or SVG figures. Component decomposition is arithmetic on the published subgroup summaries, not a new pair-level analysis. `extend_tables.py` derives model specifications and internal panel-support tables; `render_tables_references.py` generates readable tables and embeds them in the text. The full machine tables can contain more detail than their concise printed versions.

The main text's figure callouts refer to the separate PNGs. DOCX preparation appends the six main figures and full legends after the main bibliography, which keeps the scientific text easy to edit. The SI already contains its supplementary figure.

## Regenerate on the HPC

From the repository root:

```bash
bash manuscript/scripts/regenerate.sh
```

The wrapper uses `containers/images/ipin-model-arm64_0.1.0.sif`, with the repository mounted read-only and only `manuscript/` mounted writable. The recorded image SHA-256 is `c4bddf5f7b40cf7c5bbfba82f47ef2b1bbc5786c7bb36d98b020ca09761aad91`. All Python, plotting and data extraction for this draft ran in this dedicated SIF. Cache and temporary paths are under this package. No GPU is needed to regenerate figures from aggregates.

The command regenerates CSVs, tables, bibliography, PNGs, conversion inputs and validation output. It preserves authored prose outside the automatically managed table/reference blocks. It uses the included snapshots by default and makes no network calls. Do not use `--refresh-snapshots` to substitute new scientific results into this manuscript without a new editorial review. Refreshing is unnecessary for ordinary regeneration.

`record_provenance.py` is a repository-side inspection utility and is not part of offline regeneration: it reads original source/implementation files to record fingerprints. The graph was used for initial navigation, but was not rebuilt or updated because the task required the existing repository to remain read-only.

## Copy to Windows and prepare DOCX

Copy the entire `manuscript/` directory, preserving its subdirectories. The PNGs, CSVs, tables, reference metadata and scientific text are self-contained; Linux-only source paths in provenance are identifiers, not dependencies for conversion. There are no symlinked assets.

Conversion alone requires Python and Pandoc; it does not require PyTorch, ESM, the original repository or any protected data. From the copied package in PowerShell:

```powershell
python -X utf8 scripts/prepare_docx_input.py
pandoc build/manuscript-pandoc.md --from=markdown+tex_math_dollars --citeproc --bibliography=references.bib --resource-path=. --standalone --output=build/manuscript.docx
pandoc build/supplementary-pandoc.md --from=markdown+tex_math_dollars --citeproc --bibliography=references.bib --resource-path=. --standalone --output=build/supplementary.docx
```

Alternatively run `scripts/convert-docx.ps1`. For a journal-specific bibliography, add `--csl=journal-style.csl` after placing a chosen CSL file in the package. A journal reference DOCX can be applied with `--reference-doc=journal-template.docx`. Neither file is assumed or invented here.

Math is written in dollar-delimited LaTeX. The preparation script moves display-equation `\tag{...}` numbers to adjacent text, so native Word equation conversion does not depend on support for LaTeX display tags. Equation identifiers remain stable, and no mathematics is rasterized. Pandoc's DOCX writer converts supported math to native Office Math. Check final journal typography, pagination and equation-number placement in Word; a DOCX was not generated as part of this task.

To regenerate figures on Windows, install the packages listed in `requirements.txt` in a local environment and run:

```powershell
python -X utf8 scripts/regenerate.py
```

Exact font metrics can vary across platforms. Included PNGs are the reviewed publication artifacts. The HPC workflow remains SIF-based.

## Citation management and review

Citations use `[@Key]` syntax and a complete, readable bibliography is embedded in `manuscript.md`. All 34 entries were checked against Europe PMC records, DOI metadata or primary NeurIPS proceedings; full authors are retained in BibTeX. `build_bibliography.py` regenerates BibTeX offline from the checked metadata. The DOCX preparation removes the displayed reference block and allows Pandoc citeproc to generate the final bibliography once, avoiding duplicate entries.

Before submission, complete the marked deposit/access/licence fields, add the institutional sections you intend to supply, and review journal-specific formatting. These are publication metadata tasks; no scientific result needs to be reconstructed to use this draft.
