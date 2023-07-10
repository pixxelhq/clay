import os
import sys

from clay.runners import JobRunner
from model import {{.ModelName}}

if __name__ == "__main__":
    args = sys.argv[1]

    env = os.getenv("DEXTER_ENV", "dev")
    specification_path = f"specifications/model_specification_{env}.yaml"
    print(f"Using configuration located at: {specification_path}")

    server = JobRunner(
        "{{.ModelName}}",
        {{.ModelName}},
        {"config": specification_path},
    )
    server.start([args])
