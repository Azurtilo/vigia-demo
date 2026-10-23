#!/usr/bin/env python3
"""Compatibility entry point; all Django source lives in web/."""
import runpy
import sys
from pathlib import Path

if __name__ == "__main__":
    entry = Path(__file__).resolve().parent / "web" / "manage.py"
    sys.path.insert(0, str(entry.parent))
    runpy.run_path(str(entry), run_name="__main__")
