from pathlib import Path

from block import {{.BlockName}}

import clay

if __name__ == "__main__":
    cwd = Path(__file__).parent.absolute()
    specification_path = (cwd / f"../clay.yaml").resolve()
    if not specification_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {specification_path}")

    print(f"Using configuration located at: {specification_path}")
    # --input and --input-uri flags are parsed automatically by clay.Run()
    clay.Run(block={{.BlockName}}, name="{{.BlockName}}", cfg_path=str(specification_path))

