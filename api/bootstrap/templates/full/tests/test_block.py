import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from clay.runners.runner import JobRunner # noqa: E402

from {{.BlockName | ToLower}}.block import {{.BlockName}} # noqa: E402

def main() -> None:
    specification_path = Path(__file__).parent / "../clay.yaml"
    specification_path = specification_path.resolve()
    if not specification_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {specification_path}")
        
    print(f"Using configuration located at: {specification_path}")
    with (Path(__file__).parent / "sample_block_inputs.json").open() as f:
        request = f.read()
        os.environ["INPUT_JSON"] = request
    server = JobRunner(
        "{{.BlockName}}",
        {{.BlockName}},
        block_args={"config": specification_path},
        cfg_path=str(specification_path),
    )
    
    server.start()

if __name__ == "__main__":
    main()