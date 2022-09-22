import pytest

from ramen.utils import read_yaml


def test_read_yaml_file_doesnt_exist() -> None:
    with pytest.raises(FileNotFoundError):
        read_yaml("tests/testrepo/notfound.yaml")


def test_read_yaml_path_isdir() -> None:
    with pytest.raises(IsADirectoryError):
        read_yaml("tests/testrepo/")
