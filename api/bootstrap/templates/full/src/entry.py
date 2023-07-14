import os
import sys

from model import {{.ModelName}}

from clay.runners import JobRunner, HTTPRunner

if __name__ == "__main__":
    args = sys.argv[1]

    env = os.getenv("DEXTER_ENV", "dev")
    runner_type = os.getenv("RUNNER_TYPE", "job")
    specification_path = f"specifications/model_specification_{env}.yaml"
    print(f"Using configuration located at: {specification_path}")

    runner_class = HTTPRunner if runner_type == "http" else JobRunner

    # TODO(@krtkvrm): args for constructor should be setters/getters
    #  and its config should be passed when starting the runner
    runner = runner_class(
        model_name="{{.ModelName}}",
        modelcls={{.ModelName}},
        model_args={"config": specification_path},
    )

    runner.start([args])
