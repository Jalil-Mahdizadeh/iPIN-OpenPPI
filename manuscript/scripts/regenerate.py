"""Offline artifact regeneration using only this manuscript package."""
import subprocess,sys
from pathlib import Path
S=Path(__file__).resolve().parent
for name in ['extract_results.py','extend_tables.py','build_bibliography.py','render_tables_references.py','plot_figures.py','prepare_docx_input.py','validate_package.py']:
 subprocess.run([sys.executable,'-X','utf8',str(S/name)],check=True)
