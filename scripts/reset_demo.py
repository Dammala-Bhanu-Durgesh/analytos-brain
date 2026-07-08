from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from brain.storage import STATE_DIR, ensure_state


def main() -> None:
    if STATE_DIR.exists():
        shutil.rmtree(STATE_DIR)
    ensure_state()
    print(f"Reset local graph state at {STATE_DIR}")


if __name__ == "__main__":
    main()

