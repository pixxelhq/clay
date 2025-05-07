import json
import logging
from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from clay.callback.callback import CallbackData, CallbackInterface, ErrorType


class HTTPCallback(CallbackInterface):
    """
    HTTP implementation of the callback interface.
    
    This class sends callbacks as HTTP PATCH requests to a specified endpoint.
    """
    
    def __init__(
        self, 
        callback_endpoint_prefix: str,
        headers: Optional[Dict[str, str]] = None,
        retry_total: int = 3,
        retry_backoff_factor: float = 0.2,
        retry_status_forcelist: Optional[List[int]] = None,
    ):
        """
        Initialize HTTP callback with an endpoint prefix.
        
        Args:
            callback_endpoint_prefix: The base URL prefix for callbacks
            headers: Optional custom headers to include in requests
            retry_total: Number of retries to attempt
            retry_backoff_factor: Backoff factor for retry delay calculation
            retry_status_forcelist: List of status codes to force retry
        """
        self.callback_endpoint_prefix = callback_endpoint_prefix.rstrip('/')
        self.headers = headers or {}

        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"

        # Initialize session with retry logic
        self.session = requests.Session()
        retries = Retry(
            total=retry_total, 
            backoff_factor=retry_backoff_factor, 
            status_forcelist=retry_status_forcelist if retry_status_forcelist is not None else [500, 502, 503, 504]
        )
        
        protocol = "https://" if self.callback_endpoint_prefix.startswith("https://") else "http://"
        self.session.mount(protocol, HTTPAdapter(max_retries=retries))
    
    def _log(self, logger: Optional[Union[logging.Logger, Any]], level: str, message: str) -> None:
        """
        Log a message if a logger is provided.
        
        Args:
            logger: The logger to use
            level: Log level (info, debug, error, etc.)
            message: The message to log
        """
        if logger is None:
            return
            
        log_method = getattr(logger, level, None)
        if log_method is not None and callable(log_method):
            log_method(message)
    
    def _send_callback(
        self, 
        callback_data: CallbackData, 
        logger: Optional[Union[logging.Logger, Any]] = None
    ) -> bool:
        """
        Send a callback via HTTP.
        
        Args:
            callback_data: The callback data to send
            logger: Optional logger for debugging
            
        Returns:
            bool: True if the callback was sent successfully, False otherwise
        """
        # Prepare the callback URL
        callback_url = f"{self.callback_endpoint_prefix}/callback"
        
        # Convert callback data to JSON
        payload = callback_data.model_dump(exclude_none=True)
        
        # Log the callback details if a logger is provided
        self._log(logger, "debug", f"Sending callback to {callback_url}")
        self._log(logger, "debug", f"Callback payload: {json.dumps(payload)}")
        
        try:
            # Send the PATCH request
            response = self.session.patch(
                url=callback_url,
                json=payload,
                headers=self.headers
            )
            
            # Check if the request was successful
            success = (
                response.status_code == HTTPStatus.ACCEPTED or
                response.status_code == HTTPStatus.NO_CONTENT or
                response.status_code == HTTPStatus.OK
            )
            
            if success:
                self._log(logger, "info", "Successfully sent callback")
                return True
            else:
                self._log(logger, "error", f"Callback failed with status code: {response.status_code}")
                self._log(logger, "error", f"Response: {response.text}")
                return False
        
        except Exception as e:
            self._log(logger, "error", f"Error sending callback: {str(e)}")
            return False
    
    def send(
        self,
        id: str,
        inputs: List[Dict[str, Any]],
        metadata: Dict[str, str],
        logger: Optional[Union[logging.Logger, Any]] = None,
        *,
        progress: Optional[float] = None,
        outputs: Optional[List[Dict[str, Any]]] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        failure_type: Optional[ErrorType] = None,
        err_msg: Optional[str] = None
    ) -> bool:
        """
        Send a unified callback that can represent progress, success, or error states.
        
        Args:
            id: Unique identifier for the execution
            inputs: List of input data objects
            metadata: Additional metadata
            logger: Optional logger for debug information
            progress: Optional progress percentage (0-100)
            outputs: Optional list of output data objects
            start_time: Optional start timestamp in seconds
            end_time: Optional end timestamp in seconds
            failure_type: Optional error type (using ErrorType enum)
            err_msg: Optional error message
            
        Returns:
            bool: True if callback was sent successfully, False otherwise
        """
        callback_data = CallbackData(
            id=id,
            inputs=inputs,
            metadata=metadata
        )
        
        # Set optional fields if provided
        if progress is not None:
            callback_data.progress = progress
            
        if outputs is not None:
            callback_data.outputs = outputs
            
        if start_time is not None:
            callback_data.start_time = start_time
            
        if end_time is not None:
            callback_data.end_time = end_time
            
        if failure_type is not None:
            callback_data.failure_type = failure_type
            
        if err_msg is not None:
            callback_data.err_msg = err_msg
        
        return self._send_callback(callback_data, logger)