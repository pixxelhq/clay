import os
import sys

from ramen.runners import JobRunner

from model import {{.ModelName}}

if __name__ == "__main__":
    args = sys.argv[1]

    specification_path = os.getenv("SPECIFICATION_PATH")
    if specification_path is None:
        specification_path = "../specifications/model_specification.yaml"

    server = JobRunner(
        "{{.ModelName}}",
        {{.ModelName}},
        {"config": specification_path},
    )
    server.start([args])
