import os

os.path.abspath(".venv/pyvenv.cfg")

with open(os.path.abspath(".venv/pyvenv.cfg"), "r+", encoding="utf-8") as f:
    content = f.read()
    lines = content.splitlines()
    new_path = os.path.abspath("cpython-3.8.20-windows-x86_64-none")
    lines = [
        line if not line.startswith("home = ") else f"home = {new_path}"
        for line in lines
    ]
    f.seek(0)
    f.write("\n".join(lines))
    f.truncate()
