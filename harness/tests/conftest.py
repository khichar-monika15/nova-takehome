import sys
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS.parent / "grader"))
sys.path.insert(0, str(HARNESS))
