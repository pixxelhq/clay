import pytest

from {{.ModelName}}.test_model import main


def test_main() -> None:
    with pytest.raises(SystemExit, match="0"):
        main()
