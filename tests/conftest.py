from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT_DIR / "scripts"

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))
