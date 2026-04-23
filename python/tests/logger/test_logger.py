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


def test_exception_logging_includes_traceback(capsys) -> None:
    logger = ClayLogger(logger_name="test-exceptions-trace")
    try:
        raise ValueError("boom")
    except Exception as exc:
        logger.error("failed", exc_info=exc)

    out = capsys.readouterr().out
    assert "Traceback" in out
    assert "ValueError: boom" in out


def test_json_formatter_non_serializable_extra(capsys) -> None:
    """Non-JSON-serializable extras should fall back to str() rather than crash."""

    class NotSerialisable:
        def __repr__(self) -> str:
            return "<NotSerialisable instance>"

    logger = ClayLogger(logger_name="test-non-serializable")
    logger.info("payload: %s", NotSerialisable())
    entry = json.loads(capsys.readouterr().out.strip().split("\n")[-1])
    assert "NotSerialisable" in entry["message"]


def test_json_formatter_utf8_message(capsys) -> None:
    logger = ClayLogger(logger_name="test-utf8")
    logger.info("héllo — 世界 🌍")
    entry = json.loads(capsys.readouterr().out.strip().split("\n")[-1])
    assert entry["message"] == "héllo — 世界 🌍"


def test_existing_logger_is_reused_with_warning(capsys) -> None:
    """ClayLogger called twice with same name returns the existing logger."""
    first = ClayLogger(logger_name="test-reuse")
    capsys.readouterr()  # discard first logger's setup output

    second = ClayLogger(logger_name="test-reuse")
    assert first is second
    out = capsys.readouterr().out
    assert "Using existing logger without re-initialising" in out
