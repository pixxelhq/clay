import sys

from model import {{.ModelName}}

from ramen import JobRunner

if __name__ == "__main__":
    args = sys.argv[1]
    server = JobRunner(
        "{{.ModelName}}",
        {{.ModelName}},
        {"config": "../specifications/model_specification.yaml"},
    )
    server.start([args])
