import os
from pathlib import Path

from model import {{.ModelName}}

import clay

if __name__ == "__main__":
    env = os.getenv("DEXTER_ENV", "dev")
    cwd = Path(__file__).parent.absolute()
    specification_path = cwd / f"specifications/model_specification_{env}.yaml"
    print(f"Using configuration located at: {specification_path}")
    clay.Run(model={{.ModelName}}, name="{{.ModelName}}", cfg_path=str(specification_path))
