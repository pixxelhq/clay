import json

from model import {{.ModelName}}

from ramen.runners import JobRunner  # type: ignore[import]

if __name__ == "__main__":
    server = JobRunner(
        "{{.ModelName}}",
        {{.ModelName}},
        {"config": "../specifications/model_specification.yaml"},
    )
    model_input = [
        {"name": "task_id", "type": "str", "format": "string", "value": "123456"}, # leave this as-is
        {"name": "input1", "type": "str", "format": "string", "value": "Please modify the "},
        {"name": "input3", "type": "str", "format": "string", "value": "Types, formats and values"},
        {"name": "input3", "type": "str", "format": "string", "value": "of your inputs appriately"},
    ]
    request = json.dumps(model_input)
    server.start([request])
