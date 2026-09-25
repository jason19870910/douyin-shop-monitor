from pathlib import Path
p = Path("/app/frontend/build/static").parent / "index.html"
print(p.exists(), p)