import os
from pathlib import Path

from clay.runners import JobRunner  # type: ignore[import]
from model import {{.ModelName}}


def main() -> None:
    env = os.getenv("DEXTER_ENV", "dev")
    specification_path = f"specifications/model_specification_{env}.yaml"
    print(f"Using configuration located at: {specification_path}")

    server = JobRunner(
        "{{.ModelName}}",
        {{.ModelName}},
        {"config": specification_path},
    )

    with (Path(__file__).parent / "sample_model_inputs.json").open() as f:
        request = f.read()

    server.start([request])


if __name__ == "__main__":
    main()
