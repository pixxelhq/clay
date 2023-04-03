import pytest

from clay.utils import Converters, read_yaml


def test_read_yaml_file_doesnt_exist() -> None:
    with pytest.raises(FileNotFoundError):
        read_yaml("tests/testrepo/notfound.yaml")


def test_read_yaml_path_isdir() -> None:
    with pytest.raises(IsADirectoryError):
        read_yaml("tests/testrepo/")


def test_converters_to_int() -> None:
    converted_val = Converters.type_int("1")
    assert converted_val == 1


def test_converters_to_float() -> None:
    converted_val = Converters.type_float("1.3")
    assert converted_val == 1.3


def test_converters_to_array_valid() -> None:
    converted_val = Converters.type_array([1, 2, 3])
    assert converted_val == [1, 2, 3]


def test_converters_to_array_invalid() -> None:
    with pytest.raises(TypeError):
        Converters.type_array(str([1, 2, 3]))


def test_converters_to_string() -> None:
    converted_val = Converters.type_str("a")
    assert converted_val == "a"

    converted_val = Converters.type_str("1.3")
    assert converted_val == "1.3"

    converted_val = Converters.type_str(1)
    assert converted_val == "1"

    converted_val = Converters.type_str(1.3)
    assert converted_val == "1.3"


def test_converters_to_string_invalid() -> None:
    with pytest.raises(TypeError):
        Converters.type_str([1, 2, 3])
