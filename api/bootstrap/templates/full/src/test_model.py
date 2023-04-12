from clay.runners import JobRunner  # type: ignore[import]

from model import {{.ModelName}}

if __name__ == "__main__":
    server = JobRunner(
        "{{.ModelName}}",
        {{.ModelName}},
        {"config": "../specifications/model_specification.yaml"},
    )

    with open("sample_model_inputs.json", "r") as f:
        request = f.read()

    server.start([request])
