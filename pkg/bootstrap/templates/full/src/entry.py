from clay import JobRunner
from model import {{.ModelName}}

if __name__ == "__main__":
    server = JobRunner(
        "{{.ModelName}}",
        {{.ModelName}},
        {"config": "../specifications/model_specification.yaml"},
    )
    server.start(["Request JSON Body Here"])
