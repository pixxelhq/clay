import pytest
from {{.ModelName | ToSnake}}.test_model import main


def test_main() -> None:
    with pytest.raises(SystemExit, match="0"):
        main()
