import os

from clay import create_dockerfile
from tests.data.docker import docker_opts_valid


def test_dockerfile_creation() -> None:
    test_content = create_dockerfile("tests/testrepo", docker_opts_valid)
    with open("./tests/data/Test-Dockerfile", "r") as f:
        valid_dockerfile = f.read()

    assert test_content == valid_dockerfile
    assert os.path.exists("./tests/testrepo/Dockerfile")
    os.remove("./tests/testrepo/Dockerfile")
