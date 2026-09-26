# Run from the manuscript package directory after installing Pandoc on Windows.
$ErrorActionPreference = "Stop"
python -X utf8 scripts/prepare_docx_input.py
pandoc build/manuscript-pandoc.md --from=markdown+tex_math_dollars --citeproc --bibliography=references.bib --resource-path=. --standalone --output=build/manuscript.docx
if ($LASTEXITCODE -ne 0) { throw "Manuscript DOCX conversion failed" }
pandoc build/supplementary-pandoc.md --from=markdown+tex_math_dollars --citeproc --bibliography=references.bib --resource-path=. --standalone --output=build/supplementary.docx
if ($LASTEXITCODE -ne 0) { throw "Supplementary DOCX conversion failed" }
