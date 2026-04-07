import os
from pathlib import Path
from clay.runners.runner import JobRunner

from block import {{.BlockName}}

def main() -> None:
    specification_path = Path(__file__).parent / "../clay.yaml"
    specification_path = specification_path.resolve()
    if not specification_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {specification_path}")
        
    print(f"Using configuration located at: {specification_path}")
    server = JobRunner(
        "{{.BlockName}}",
        {{.BlockName}},
        block_args={"config": specification_path},
        cfg_path=str(specification_path),
    )

    with (Path(__file__).parent / "sample_block_inputs.json").open() as f:
        request = f.read()
        os.environ["INPUT_JSON"] = request
    
    server.start()

if __name__ == "__main__":
    main()