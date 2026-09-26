"""Regenerate BibTeX offline from the checked, full-author metadata records.
Initial verification used Europe PMC, DOI content negotiation, and primary
NeurIPS proceedings; each record retains its verification URL.
"""
import json
from pathlib import Path
M=Path(__file__).resolve().parents[1]
entries=json.loads((M/'source-data/references/verified-references.json').read_text(encoding='utf-8'))
def escape(value):return str(value).replace('&',r'\&').replace('_',r'\_').replace('%',r'\%')
lines=[]
for x in entries:
 lines.append('@'+x['type']+'{'+x['key']+',')
 for key in ['author','title','journal','year','volume','number','pages','doi','url']:
  if x.get(key):
   field='booktitle' if key=='journal' and x['type']=='inproceedings' else key
   val=x[key] if key in ['url','doi'] else escape(x[key]);val='{'+val+'}' if key=='title' else val
   lines.append('  '+field+' = {'+val+'},')
 lines.append('}\n')
(M/'references.bib').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(len(entries),'reference entries generated')
