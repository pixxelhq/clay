import logging
from unittest import TestCase

from ramen.logger import RamenLogger


class TestRamenLogger(TestCase):
    def test_logging_level(self):
        logger = RamenLogger(
            "test_logger", False, logging.INFO, create_console_handler=True
        )
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
