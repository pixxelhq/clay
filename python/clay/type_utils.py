from typing import Any, Dict, List, Union

import datatypes


def TypeFromDict(d: Dict[str, Any]) -> datatypes.DataWrapper:
    """Create a DataWrapper from a dictionary."""
    t = datatypes.FromDict(d, False)
    return wrap_types(t)


def lift_underlying_type(
    dw: datatypes.DataWrapper,
) -> datatypes.Data:
    """Extract the underlying proto data type from a DataWrapper."""
    if isinstance(dw, datatypes.DataWrapper):
        return dw._proto_cls_initialised
    raise TypeError("Only DataWrapper instances are supported")


# Legacy function removed - use proto types directly


# Legacy conversion function removed - use proto types directly


def wrap_types(t: Union[datatypes.Data, datatypes.DataWrapper]) -> datatypes.DataWrapper:
    """Wrap a proto data type in a DataWrapper."""
    if isinstance(t, datatypes.Data):
        return datatypes.DataWrapper(t)
    return t

def WrapTypes(
    items: List[datatypes.Data],
) -> List[datatypes.DataWrapper]:
    """Wrap a list of proto data types in DataWrappers."""
    result: List[datatypes.DataWrapper] = []
    for t in items:
        if isinstance(t, datatypes.Data):
            result.append(datatypes.DataWrapper(t))
        else:
            raise TypeError(f"Unsupported type: {type(t)}")
    return result
