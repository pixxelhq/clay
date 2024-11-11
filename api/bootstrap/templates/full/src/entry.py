from pathlib import Path

from model import {{.ModelName}}

import clay

if __name__ == "__main__":
    cwd = Path(__file__).parent.absolute()
    specification_path = (cwd / f"../clay.yaml").resolve()
    if not specification_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {specification_path}")
    
    print(f"Using configuration located at: {specification_path}")
    clay.Run(model={{.ModelName}}, name="{{.ModelName}}", cfg_path=str(specification_path))
