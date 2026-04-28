import unittest
from unittest import TestCase

from clay.callback.callback import CallbackData, ErrorType


class TestCallbackBase(TestCase):
    """Tests for base callback classes."""

    def test_error_type_enum(self):
        """Test error type enumeration."""
        # Ensure error types are correctly defined
        self.assertEqual(ErrorType.BAD_REQUEST, "bad_request")
        self.assertEqual(ErrorType.RUNTIME_EXCEPTION, "runtime_exception")
        self.assertEqual(ErrorType.UNKNOWN, "unknown")

    def test_callback_data_with_minimal_args(self):
        """Test callback data with only required arguments."""
        # Create callback data with minimal arguments
        data = CallbackData(id="test-123")

        # Verify attributes
        self.assertEqual(data.id, "test-123")
        self.assertIsNone(data.inputs)
        self.assertIsNone(data.outputs)
        self.assertEqual(data.metadata, {})
        self.assertIsNone(data.progress)
        self.assertIsNone(data.start_time)
        self.assertIsNone(data.end_time)
        self.assertIsNone(data.failure_type)
        self.assertIsNone(data.err_msg)

        # Test block serialization
        data_dict = data.model_dump(exclude_none=True)
        self.assertEqual(data_dict["id"], "test-123")
        self.assertEqual(data_dict["metadata"], {})
        self.assertNotIn("inputs", data_dict)
        self.assertNotIn("outputs", data_dict)
        self.assertNotIn("progress", data_dict)
        self.assertNotIn("start_time", data_dict)
        self.assertNotIn("end_time", data_dict)
        self.assertNotIn("failure_type", data_dict)
        self.assertNotIn("err_msg", data_dict)

    def test_callback_data_with_full_args(self):
        """Test callback data with all arguments."""
        # Create test data
        test_id = "full-test-456"
        test_inputs = [{"name": "input1", "value": "value1"}]
        test_outputs = [{"name": "output1", "value": "result1"}]
        test_progress = 75.5
        test_start_time = "2024-01-01T10:00:00Z"
        test_end_time = "2024-01-01T10:10:00Z"
        test_failure_type = ErrorType.BAD_REQUEST
        test_err_msg = "Invalid input"
        test_metadata = {"version": "1.0", "env": "test"}

        # Create callback data with all arguments
        data = CallbackData(
            id=test_id,
            inputs=test_inputs,
            outputs=test_outputs,
            progress=test_progress,
            start_time=test_start_time,
            end_time=test_end_time,
            failure_type=test_failure_type,
            err_msg=test_err_msg,
            metadata=test_metadata,
        )

        # Verify attributes
        self.assertEqual(data.id, test_id)
        self.assertEqual(data.inputs, test_inputs)
        self.assertEqual(data.outputs, test_outputs)
        self.assertEqual(data.progress, test_progress)
        self.assertEqual(data.start_time, test_start_time)
        self.assertEqual(data.end_time, test_end_time)
        self.assertEqual(data.failure_type, test_failure_type)
        self.assertEqual(data.err_msg, test_err_msg)
        self.assertEqual(data.metadata, test_metadata)

        # Test block serialization
        data_dict = data.model_dump(exclude_none=True)
        self.assertEqual(data_dict["id"], test_id)
        self.assertEqual(data_dict["inputs"], test_inputs)
        self.assertEqual(data_dict["outputs"], test_outputs)
        self.assertEqual(data_dict["progress"], test_progress)
        self.assertEqual(data_dict["start_time"], test_start_time)
        self.assertEqual(data_dict["end_time"], test_end_time)
        self.assertEqual(data_dict["failure_type"], test_failure_type)
        self.assertEqual(data_dict["err_msg"], test_err_msg)
        self.assertEqual(data_dict["metadata"], test_metadata)

    def test_block_dump_serialization(self):
        """Test model_dump method for serialization."""
        # Create callback data
        data = CallbackData(id="compat-test", progress=50.0, metadata={"test": "value"})

        # Test the model_dump method
        result = data.model_dump(exclude_none=True)

        # Verify result
        self.assertEqual(result["id"], "compat-test")
        self.assertEqual(result["progress"], 50.0)
        self.assertEqual(result["metadata"], {"test": "value"})
        self.assertNotIn("inputs", result)  # excluded because None
        self.assertNotIn("outputs", result)  # excluded because None

    def test_to_dict_method_backward_compatibility(self):
        """Test to_dict method for backward compatibility."""
        # Create callback data
        data = CallbackData(id="compat-test", progress=50.0, metadata={"test": "value"})

        # Test the to_dict method
        result = data.to_dict()

        # Verify result (should match model_dump behavior)
        self.assertEqual(result["id"], "compat-test")
        self.assertEqual(result["progress"], 50.0)
        self.assertEqual(result["metadata"], {"test": "value"})
        self.assertNotIn("inputs", result)  # excluded because None
        self.assertNotIn("outputs", result)  # excluded because None


if __name__ == "__main__":
    unittest.main()
