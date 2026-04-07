from pathlib import Path

from block import RasterVectorClipper

import clay

if __name__ == "__main__":
    cwd = Path(__file__).parent.absolute()
    specification_path = (cwd / "../clay.yaml").resolve()
    if not specification_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {specification_path}")
    
    print(f"Using configuration located at: {specification_path}")
    clay.Run(block=RasterVectorClipper, name="RasterVectorClipper", cfg_path=str(specification_path))
