import os
from pathlib import Path

from clay.runners.job_runner import JobRunner
from model import DemoTest


def main() -> None:
    env = os.getenv("DEXTER_ENV", "dev")
    specification_path = Path(__file__).parent / f"specifications/model_specification_{env}.yaml"
    print(f"Using configuration located at: {specification_path}")
    with (Path(__file__).parent / "sample_model_inputs.json").open() as f:
        request = f.read()

    j = JobRunner(
        model_name="DemoTest",
        modelcls=DemoTest,
        model_args={"config": specification_path},
        cfg_path=str(specification_path),
    )

    j.start(args=request)


if __name__ == "__main__":
    main()
