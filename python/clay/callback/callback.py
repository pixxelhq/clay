import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from clay.types import ModelStates


class ErrorType(str, Enum):
    """Error types for callbacks."""
    BAD_REQUEST = "bad_request"
    RUNTIME_EXCEPTION = "runtime_exception"
    UNKNOWN = "unknown"


class CallbackData(BaseModel):
    """
    Represents the data to be sent in a callback.
    
    Attributes:
        id: Unique identifier for the execution
        inputs: List of input data objects
        outputs: List of output data objects
        progress: Current progress percentage (0-100)
        start_time: Start timestamp in seconds
        end_time: End timestamp in seconds
        failure_type: Error type at root level (using ErrorType enum)
        err_msg: Error message at root level
        metadata: Optional additional metadata
        status: Current state of the model execution (using ModelStates enum)
    """
    id: str = Field(serialization_alias="id")
    inputs: Optional[List[Dict[str, Any]]] = None
    outputs: Optional[List[Dict[str, Any]]] = None
    progress: Optional[float] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    failure_type: Optional[ErrorType] = None
    err_msg: Optional[str] = None
    disclaimer: Optional[Dict[str, str]] = None
    metadata: Dict[str, str] = Field(default_factory=dict)
    status: Annotated[ModelStates, Field(serialization_alias="state")] = ModelStates.INPROGRESS

    def to_dict(self) -> Dict[str, Any]:
        """Convert callback data to a dictionary for serialization."""
        return self.model_dump(exclude_none=True)


class CallbackInterface(ABC):
    """
    Abstract base class for callback implementations.
    
    This interface defines the methods that any callback implementation must provide.
    """

    @abstractmethod
    def send(
            self,
            id: str,
            metadata: Dict[str, str],
            inputs: List[Dict[str, Any]] = None,  # type: ignore
            logger: Optional[Union[logging.Logger, Any]] = None,
            status: ModelStates = ModelStates.INPROGRESS,
            *,
            progress: Optional[float] = None,
            outputs: Optional[List[Dict[str, Any]]] = None,
            start_time: Optional[str] = None,
            end_time: Optional[str] = None,
            failure_type: Optional[ErrorType] = None,
            disclaimer: Optional[Dict[str, str]] = None,
            err_msg: Optional[str] = None
    ) -> bool:
        """
        Send a unified callback that can represent progress, success, or error states.
        
        Args:
            id: Unique identifier for the execution
            inputs: List of input data objects
            metadata: Additional metadata
            logger: Optional logger for debug information
            status: Current state of the model execution (using ModelStates enum)
            progress: Optional progress percentage (0-100)
            outputs: Optional list of output data objects
            start_time: Optional start timestamp in seconds
            end_time: Optional end timestamp in seconds
            failure_type: Optional error type (using ErrorType enum)
            err_msg: Optional error message
            
        Returns:
            bool: True if callback was sent successfully, False otherwise
        """
        pass

    def send_success(
            self,
            id: str,
            inputs: List[Dict[str, Any]],
            outputs: List[Dict[str, Any]],
            start_time: str,
            end_time: str,
            metadata: Dict[str, str],
            logger: Optional[Union[logging.Logger, Any]] = None
    ) -> bool:
        """
        Send a success callback.

        Args:
            id: Unique identifier for the execution
            inputs: List of input data objects
            outputs: List of output data objects
            start_time: Start timestamp in seconds
            end_time: End timestamp in seconds
            metadata: Additional metadata
            logger: Optional logger for debug information

        Returns:
            bool: True if callback was sent successfully, False otherwise
        """
        return self.send(
            id=id,
            inputs=inputs,
            metadata=metadata,
            logger=logger,
            outputs=outputs,
            start_time=start_time,
            end_time=end_time,
            status=ModelStates.COMPLETED
        )

    def send_progress(
            self,
            id: str,
            progress: float,
            inputs: List[Dict[str, Any]],
            metadata: Dict[str, str],
            status: Optional[ModelStates] = None,
            logger: Optional[Union[logging.Logger, Any]] = None
    ) -> bool:
        """
        Send a progress update callback.

        Args:
            id: Unique identifier for the execution
            progress: Current progress percentage (0-100)
            inputs: List of input data objects
            metadata: Additional metadata
            status: Current state of the model execution (using ModelStates enum)
            logger: Optional logger for debug information

        Returns:
            bool: True if callback was sent successfully, False otherwise
        """
        return self.send(
            id=id,
            inputs=inputs,
            metadata=metadata,
            logger=logger,
            progress=progress,
            status=status if status is not None else ModelStates.INPROGRESS
        )

    def send_error(
            self,
            id: str,
            failure_type: ErrorType,
            err_msg: str,
            inputs: List[Dict[str, Any]],
            start_time: str,
            end_time: str,
            metadata: Dict[str, str],
            logger: Optional[Union[logging.Logger, Any]] = None
    ) -> bool:
        """
        Send an error callback.
        
        Args:
            id: Unique identifier for the execution
            failure_type: Error type
            err_msg: Error message
            inputs: List of input data objects
            start_time: Start timestamp in seconds
            end_time: End timestamp in seconds
            metadata: Additional metadata
            logger: Optional logger for debug information
            
        Returns:
            bool: True if callback was sent successfully, False otherwise
        """
        return self.send(
            id=id,
            inputs=inputs,
            metadata=metadata,
            logger=logger,
            failure_type=failure_type,
            err_msg=err_msg,
            start_time=start_time,
            end_time=end_time,
            status=ModelStates.FAILED
        )
