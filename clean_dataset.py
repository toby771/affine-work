import re, sys
from pathlib import Path

p = Path("/mnt/d/Exercise/Affine_work/make_dataset.jsonl")
text = p.read_text(encoding="utf-8-sig")
clean = re.sub(r',(\s*[\]}])', r'\1', text)
p.write_text(clean, encoding="utf-8")
print("cleaned")