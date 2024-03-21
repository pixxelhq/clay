import json
import logging
from unittest import TestCase

from clay.logger import ClayLogger


class TestClayLogger(TestCase):
    def test_logging_level(self):
        logger = ClayLogger("test_logger", False, logging.INFO)
        assert logger.name == "test_logger"
        with self.assertLogs("test_logger", level="INFO") as capture:
            logger.info("This is info")
            logger.critical("This is critical")
        self.assertEqual(capture.records[0].name, "test_logger")
        self.assertEqual(
            capture.output,
            [
                "INFO:test_logger:This is info",
                "CRITICAL:test_logger:This is critical",
            ],
        )


def test_json_formatter(capsys) -> None:
    logger = ClayLogger(logger_name="test")

    def assert_json_output():
        """
        reads the latest line in stdout, checks if it is valid JSON, then clears stdouts
        """
        json.loads(capsys.readouterr().out.strip())

    a = {"param1": 123, "nested_params": {"nested_param1": 3, "nested_param2": 5}}
    b = [1, 2, 3]
    logger.info("Plain log")
    assert_json_output()
    logger.info("log with nested dict as extra: %(param1)s,  %(nested_params)s", a)
    assert_json_output()
    logger.info("log msg list as extra: %s", b)
    assert_json_output()
    logger.info("log with random string as extra: %s", "a string")
    assert_json_output()


def test_exception_logging(capsys) -> None:
    print()
    logger = ClayLogger(logger_name="test-exceptions")
    try:
        1 + "a"  # type: ignore
    except Exception as exc:
        logger.error(exc, exc_info=exc)

    last_line = capsys.readouterr().out.strip().split("\n")[-1]
    assert last_line == "TypeError: unsupported operand type(s) for +: 'int' and 'str'"
