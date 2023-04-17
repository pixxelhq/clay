from pathlib import Path

from clay.runners import JobRunner  # type: ignore[import]
from model import {{.ModelName}}


def main() -> None:
    server = JobRunner(
        "{{.ModelName}}",
        {{.ModelName}},
        {"config": "../specifications/model_specification.yaml"},
    )

    with (Path(__file__).parent / "sample_model_inputs.json").open() as f:
        request = f.read()

    server.start([request])


if __name__ == "__main__":
    main()
