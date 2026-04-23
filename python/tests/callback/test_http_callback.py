import logging
import unittest
from http import HTTPStatus
from unittest import TestCase
from unittest.mock import Mock, patch

from clay.callback.callback import BlockStates, CallbackData, ErrorType
from clay.callback.http_callback import HTTPCallback


def test_block_states_values():
    assert BlockStates.CREATED.value == "created"
    assert BlockStates.INPROGRESS.value == "inprogress"
    assert BlockStates.COMPLETED.value == "completed"
    assert BlockStates.FAILED.value == "failed"


class TestHTTPCallback(TestCase):
    """Tests for HTTP callback implementation."""

    def setUp(self):
        """Set up test fixtures."""
        self.callback_url = "https://api.example.com/block"
        self.test_headers = {"X-API-Key": "test-key"}
        self.callback = HTTPCallback(
            callback_endpoint=self.callback_url,
            headers=self.test_headers,
            retry_total=2,
            retry_backoff_factor=0.1,
            retry_status_forcelist=[500]
        )
        
        # Set up a test logger
        self.logger = logging.getLogger("test_logger")
        self.logger.setLevel(logging.DEBUG)
        self.log_handler = logging.StreamHandler()
        self.logger.addHandler(self.log_handler)

    def test_init(self):
        """Test initialization of HTTP callback."""
        # Test URL handling
        self.assertEqual(self.callback.callback_endpoint, self.callback_url)
        
        # Test with trailing slash
        callback2 = HTTPCallback(callback_endpoint=self.callback_url + "/")
        self.assertEqual(callback2.callback_endpoint, self.callback_url + "/")
        
        # Test headers
        self.assertEqual(self.callback.headers["X-API-Key"], "test-key")
        self.assertEqual(self.callback.headers["Content-Type"], "application/json")
        
        # Test without content-type header
        callback3 = HTTPCallback(
            callback_endpoint=self.callback_url,
            headers={"Content-Type": "text/plain"}
        )
        self.assertEqual(callback3.headers["Content-Type"], "text/plain")
        
        # Test session setup
        self.assertIsNotNone(self.callback.session)

    def test_log_method(self):
        """Test the log helper method."""
        with patch.object(self.logger, 'info') as mock_info:
            self.callback._log(self.logger, "info", "Test message")
            mock_info.assert_called_once_with("Test message")
        
        with patch.object(self.logger, 'error') as mock_error:
            self.callback._log(self.logger, "error", "Error message")
            mock_error.assert_called_once_with("Error message")
        
        # Test with None logger
        self.callback._log(None, "info", "Should not raise error")
        
        # Test with invalid level
        self.callback._log(self.logger, "invalid_level", "Should not raise error")

    @patch('requests.Session.post')
    def test_send_callback_success_status_codes(self, mock_post):
        """_send_callback treats 200, 202, and 204 as success."""
        callback_data = CallbackData(
            id="test-123",
            progress=50.0,
            inputs=[{"name": "input1", "value": "test"}],
            metadata={"version": "1.0"}
        )

        for status in (HTTPStatus.OK, HTTPStatus.ACCEPTED, HTTPStatus.NO_CONTENT):
            with self.subTest(status=status):
                mock_post.reset_mock()
                mock_response = Mock()
                mock_response.status_code = status
                mock_response.text = "OK"
                mock_post.return_value = mock_response

                result = self.callback._send_callback(callback_data, self.logger)

                self.assertTrue(result, f"status {status} should be treated as success")
                mock_post.assert_called_once()
                call_args = mock_post.call_args
                self.assertEqual(call_args[1]["url"], self.callback_url)
                self.assertEqual(call_args[1]["headers"], self.callback.headers)
                payload = call_args[1]["json"]
                self.assertEqual(payload["data"]["id"], "test-123")
                self.assertEqual(payload["data"]["progress"], 50.0)

    @patch('requests.Session.post')
    def test_send_callback_failure(self, mock_post):
        """Non-success HTTP status codes cause _send_callback to return False."""
        mock_response = Mock()
        mock_response.status_code = HTTPStatus.BAD_REQUEST
        mock_response.text = "Error"
        mock_post.return_value = mock_response

        callback_data = CallbackData(
            id="error-test",
            inputs=[{"name": "input1", "value": "test"}],
            metadata={}
        )

        result = self.callback._send_callback(callback_data, self.logger)

        self.assertFalse(result)
        mock_post.assert_called_once()

    @patch('requests.Session.post')
    def test_send_callback_exception(self, mock_post):
        """Exceptions from the transport are caught and yield False."""
        mock_post.side_effect = Exception("Connection error")

        callback_data = CallbackData(
            id="exception-test",
            inputs=[{"name": "input1", "value": "test"}],
            metadata={}
        )

        result = self.callback._send_callback(callback_data, self.logger)

        self.assertFalse(result)
        mock_post.assert_called_once()

    @patch('clay.callback.http_callback.HTTPCallback._send_callback')
    def test_send_unified(self, mock_send):
        """Test the unified send method."""
        # Setup mock
        mock_send.return_value = True
        
        # Test data for progress callback
        test_id = "unified-test"
        test_progress = 25.0
        test_inputs = [{"name": "input1", "value": "test"}]
        test_outputs = [{"name": "output1", "value": "result"}]
        test_start_time = "2024-01-01T10:00:00Z"
        test_end_time = "2024-01-01T10:10:00Z"
        test_failure_type = ErrorType.RUNTIME_EXCEPTION
        test_err_msg = "Test error"
        test_metadata = {"version": "1.0"}
        
        # Call send with progress data
        result = self.callback.send(
            id=test_id,
            inputs=test_inputs,
            metadata=test_metadata,
            logger=self.logger,
            progress=test_progress
        )
        
        # Verify result
        self.assertTrue(result)
        
        # Verify callback data for progress
        mock_send.assert_called_once()
        callback_data = mock_send.call_args[0][0]
        self.assertEqual(callback_data.id, test_id)
        self.assertEqual(callback_data.progress, test_progress)
        self.assertEqual(callback_data.inputs, test_inputs)
        self.assertEqual(callback_data.metadata, test_metadata)
        
        # Reset mock
        mock_send.reset_mock()
        
        # Call send with success data
        result = self.callback.send(
            id=test_id,
            inputs=test_inputs,
            metadata=test_metadata,
            logger=self.logger,
            outputs=test_outputs,
            start_time=test_start_time,
            end_time=test_end_time
        )
        
        # Verify result
        self.assertTrue(result)
        
        # Verify callback data for success
        mock_send.assert_called_once()
        callback_data = mock_send.call_args[0][0]
        self.assertEqual(callback_data.id, test_id)
        self.assertEqual(callback_data.inputs, test_inputs)
        self.assertEqual(callback_data.outputs, test_outputs)
        self.assertEqual(callback_data.start_time, test_start_time)
        self.assertEqual(callback_data.end_time, test_end_time)
        self.assertEqual(callback_data.metadata, test_metadata)
        
        # Reset mock
        mock_send.reset_mock()
        
        # Call send with error data
        result = self.callback.send(
            id=test_id,
            inputs=test_inputs,
            metadata=test_metadata,
            logger=self.logger,
            failure_type=test_failure_type,
            err_msg=test_err_msg,
            start_time=test_start_time,
            end_time=test_end_time
        )
        
        # Verify result
        self.assertTrue(result)
        
        # Verify callback data for error
        mock_send.assert_called_once()
        callback_data = mock_send.call_args[0][0]
        self.assertEqual(callback_data.id, test_id)
        self.assertEqual(callback_data.failure_type, test_failure_type)
        self.assertEqual(callback_data.err_msg, test_err_msg)
        self.assertEqual(callback_data.inputs, test_inputs)
        self.assertEqual(callback_data.start_time, test_start_time)
        self.assertEqual(callback_data.end_time, test_end_time)
        self.assertEqual(callback_data.metadata, test_metadata)
        
        # Test with all parameters
        mock_send.reset_mock()
        result = self.callback.send(
            id=test_id,
            inputs=test_inputs,
            metadata=test_metadata,
            logger=self.logger,
            progress=test_progress,
            outputs=test_outputs,
            start_time=test_start_time,
            end_time=test_end_time,
            failure_type=test_failure_type,
            err_msg=test_err_msg
        )
        
        # Verify result
        self.assertTrue(result)
        
        # Verify all fields are set
        mock_send.assert_called_once()
        callback_data = mock_send.call_args[0][0]
        self.assertEqual(callback_data.id, test_id)
        self.assertEqual(callback_data.progress, test_progress)
        self.assertEqual(callback_data.inputs, test_inputs)
        self.assertEqual(callback_data.outputs, test_outputs)
        self.assertEqual(callback_data.start_time, test_start_time)
        self.assertEqual(callback_data.end_time, test_end_time)
        self.assertEqual(callback_data.failure_type, test_failure_type)
        self.assertEqual(callback_data.err_msg, test_err_msg)
        self.assertEqual(callback_data.metadata, test_metadata)

    @patch('clay.callback.http_callback.HTTPCallback._send_callback')
    def test_send_progress(self, mock_send):
        """Test send_progress method."""
        # Setup mock
        mock_send.return_value = True
        
        # Test data
        test_id = "progress-test"
        test_progress = 25.0
        test_inputs = [{"name": "input1", "value": "test"}]
        test_metadata = {"version": "1.0"}
        
        # Call send_progress
        result = self.callback.send_progress(
            id=test_id,
            progress=test_progress,
            inputs=test_inputs,
            metadata=test_metadata,
            logger=self.logger
        )
        
        # Verify result
        self.assertTrue(result)
        
        # Verify callback data
        mock_send.assert_called_once()
        callback_data = mock_send.call_args[0][0]
        self.assertEqual(callback_data.id, test_id)
        self.assertEqual(callback_data.progress, test_progress)
        self.assertEqual(callback_data.inputs, test_inputs)
        self.assertEqual(callback_data.metadata, test_metadata)

    @patch('clay.callback.http_callback.HTTPCallback._send_callback')
    def test_send_success(self, mock_send):
        """Test send_success method."""
        # Setup mock
        mock_send.return_value = True
        
        # Test data
        test_id = "success-test"
        test_inputs = [{"name": "input1", "value": "test"}]
        test_outputs = [{"name": "output1", "value": "result"}]
        test_start_time = "2024-01-01T10:00:00Z"
        test_end_time = "2024-01-01T10:10:00Z"
        test_metadata = {"version": "1.0"}
        
        # Call send_success
        result = self.callback.send_success(
            id=test_id,
            inputs=test_inputs,
            outputs=test_outputs,
            start_time=test_start_time,
            end_time=test_end_time,
            metadata=test_metadata,
            logger=self.logger
        )
        
        # Verify result
        self.assertTrue(result)
        
        # Verify callback data
        mock_send.assert_called_once()
        callback_data = mock_send.call_args[0][0]
        self.assertEqual(callback_data.id, test_id)
        self.assertEqual(callback_data.inputs, test_inputs)
        self.assertEqual(callback_data.outputs, test_outputs)
        self.assertEqual(callback_data.start_time, test_start_time)
        self.assertEqual(callback_data.end_time, test_end_time)
        self.assertEqual(callback_data.metadata, test_metadata)

    @patch('clay.callback.http_callback.HTTPCallback._send_callback')
    def test_send_error(self, mock_send):
        """Test send_error method."""
        # Setup mock
        mock_send.return_value = True
        
        # Test data
        test_id = "error-test"
        test_failure_type = ErrorType.RUNTIME_EXCEPTION
        test_err_msg = "Test error"
        test_inputs = [{"name": "input1", "value": "test"}]
        test_start_time = "2024-01-01T10:00:00Z"
        test_end_time = "2024-01-01T10:10:00Z"
        test_metadata = {"version": "1.0"}
        
        # Call send_error
        result = self.callback.send_error(
            id=test_id,
            failure_type=test_failure_type,
            err_msg=test_err_msg,
            inputs=test_inputs,
            start_time=test_start_time,
            end_time=test_end_time,
            metadata=test_metadata,
            logger=self.logger
        )
        
        # Verify result
        self.assertTrue(result)
        
        # Verify callback data
        mock_send.assert_called_once()
        callback_data = mock_send.call_args[0][0]
        self.assertEqual(callback_data.id, test_id)
        self.assertEqual(callback_data.failure_type, test_failure_type)
        self.assertEqual(callback_data.err_msg, test_err_msg)
        self.assertEqual(callback_data.inputs, test_inputs)
        self.assertEqual(callback_data.start_time, test_start_time)
        self.assertEqual(callback_data.end_time, test_end_time)
        self.assertEqual(callback_data.metadata, test_metadata)

if __name__ == "__main__":
    unittest.main()