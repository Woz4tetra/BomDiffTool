# setup virtual environment

```bash
conda create -n bomdiffui python=3.8
conda activate bomdiffui
pip install -r requirements.txt
```

# run pyinstaller

```bash
conda activate bomdiffui

pyinstaller --onefile --noconsole --windowed --icon=app.ico main.py -n BomDiffTool
```

When recursion error happens, paste the following in main.spec

```python
# -_- mode: python ; coding: utf-8 -_-

import sys
sys.setrecursionlimit(5000)
```

```bash
conda activate bomdiffui

pyinstaller --onefile --noconsole --windowed --icon=app.ico main.py -n BomDiffTool
```
