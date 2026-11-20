from pathlib import Path

import clay
from block import {{.Class}}

if __name__ == "__main__":
    cwd = Path(__file__).parent.absolute()
    specification_path = (cwd / "../clay.yaml").resolve()
    if not specification_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {specification_path}")

    print(f"Using configuration located at: {specification_path}")
    # --input and --input-uri flags are parsed automatically by clay.Run()
    clay.Run(block={{.Class}}, name="{{.Class}}", cfg_path=str(specification_path))
