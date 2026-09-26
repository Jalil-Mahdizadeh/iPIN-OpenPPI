"""Create portable Pandoc inputs with native-math-compatible equation numbers.
Does not require Pandoc and does not modify manuscript prose. Run Pandoc on the
resulting build files; image/resource paths are resolved relative to the package.
"""
import re
from pathlib import Path
M=Path(__file__).resolve().parents[1];out=M/'build';out.mkdir(exist_ok=True)
for filename in ['manuscript','supplementary']:
 s=(M/(filename+'.md')).read_text(encoding='utf-8')
 # Replace the human-readable bibliography with a citeproc insertion point.
 s=re.sub(r'<!-- REFERENCES -->.*?<!-- /REFERENCES -->','::: {#refs}\n:::',s,flags=re.S)
 s=re.sub(r'<!-- /?TABLE-[A-Z0-9-]+ -->','',s)
 # Keep all math native, with equation numbers as adjacent text. This avoids
 # conversion dependence on support for LaTeX display-environment tags.
 def equation(m):
  body=m.group(1);tag=re.search(r'\\tag\{([^}]+)\}',body)
  if not tag:return m.group(0)
  return '$$'+re.sub(r'\\tag\{[^}]+\}','',body).rstrip()+'\n$$\n\n('+tag.group(1)+')'
 s=re.sub(r'\$\$(.*?)\$\$',equation,s,flags=re.S)
 if filename=='manuscript':
  legends=(M/'figure-legends.md').read_text(encoding='utf-8')
  sections=re.split(r'(?=^## )',legends,flags=re.M)
  s+='\n\n# Main figures\n\n'
  for i,section in enumerate(sections[1:7],1):
   title,body=section.split('\n',1)
   s+=title+'\n\n'+f'![Figure {i}](figure-{i}.png){{width=7in}}\n\n'+body.strip()+'\n\n'
 (out/(filename+'-pandoc.md')).write_text(s,encoding='utf-8')
print('Prepared build/manuscript-pandoc.md and build/supplementary-pandoc.md')
