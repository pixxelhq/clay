from pathlib import Path

from clay.runners.job_runner import JobRunner
from model import {{.ModelName}}


def main() -> None:
    specification_path = Path(__file__).parent / "../clay.yaml"
    specification_path = specification_path.resolve()
    if not specification_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {specification_path}")
        
    print(f"Using configuration located at: {specification_path}")
    with (Path(__file__).parent / "sample_model_inputs.json").open() as f:
        request = f.read()

    j = JobRunner(
        model_name="{{.ModelName}}",
        modelcls={{.ModelName}},
        model_args={"config": specification_path},
        cfg_path=specification_path,
    )

    j.start(args=request)


if __name__ == "__main__":
    main()
