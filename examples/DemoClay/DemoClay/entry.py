import os
from pathlib import Path

from model import DemoClay

import clay

if __name__ == "__main__":
    env = os.getenv("DEXTER_ENV", "dev")
    cwd = Path(__file__).parent.absolute()
    specification_path = cwd / f"specifications/model_specification_{env}.yaml"
    print(f"Using configuration located at: {specification_path}")
    clay.Run(model=DemoClay, name="DemoClay", cfg_path=specification_path)
