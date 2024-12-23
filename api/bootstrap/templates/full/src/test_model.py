import os
from pathlib import Path

from clay.runners.job_runner import JobRunner
from model import {{.ModelName}}

def set_required_env_vars() -> None:
    env_vars = {
        "TASK_ID": "task123", 
        "WORKFLOW_ID": "wf123",  
        "JOB_ID": "job123", 
        "LOCAL_WORKING_DIR": "/runs"
    }
    for var, value in env_vars.items():
        os.environ.setdefault(var, value)

def main() -> None:
    specification_path = Path(__file__).parent / "../clay.yaml"
    specification_path = specification_path.resolve()
    if not specification_path.exists():
        raise FileNotFoundError(f"Configuration file not found at: {specification_path}")
        
    print(f"Using configuration located at: {specification_path}")
    with (Path(__file__).parent / "sample_model_inputs.json").open() as f:
        request = f.read()
    set_required_env_vars()
    
    j = JobRunner(
        model_name="{{.ModelName}}",
        modelcls={{.ModelName}},
        model_args={"config": specification_path},
        cfg_path=specification_path,
    )

    j.start(args=request)


if __name__ == "__main__":
    main()
