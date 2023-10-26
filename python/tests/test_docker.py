import os

from clay import create_dockerfile
from tests.data.docker import docker_opts_valid


def test_dockerfile_creation() -> None:
    test_content = create_dockerfile("python/tests/testrepo", docker_opts_valid)
    with open("./python/tests/data/Test-Dockerfile", "r") as f:
        valid_dockerfile = f.read()

    assert test_content == valid_dockerfile
    assert os.path.exists("./python/tests/testrepo/Dockerfile")
    os.remove("./python/tests/testrepo/Dockerfile")
