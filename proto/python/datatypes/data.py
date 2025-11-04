import abc
import typing
from typing import Any, Dict

from google.protobuf.json_format import MessageToDict, MessageToJson, ParseDict
from typing_extensions import Optional, Union

import datatypes.data_pb2 as gen_types
from datatypes import data_pb2
from datatypes.data_pb2 import *

T = typing.TypeVar("T")

FormatTypes = Union[
    gen_types.Raster,
    gen_types.Vector,
    gen_types.Tabular,
    gen_types.Date,
    gen_types.Number,
    gen_types.String,
]

Data = Union[
    gen_types.Raster,
    gen_types.Vector,
    gen_types.Tabular,
    gen_types.Date,
    gen_types.Number,
    gen_types.String,
]

Properties = Union[
    gen_types.RasterProperties,
    gen_types.VectorProperties,
    gen_types.TabularProperties,
    gen_types.DateProperties
]


class DataWrapperError(Exception):
    """Base exception for all data wrapper related errors"""

    pass


class FieldNotFoundError(DataWrapperError):
    """Raised when attempting to access a field that doesn't exist"""

    def __init__(self, field: str):
        self.field = field
        super().__init__(f"Field '{field}' does not exist in the proto message")


class InvalidFieldTypeError(DataWrapperError):
    """Raised when attempting to set a field with incorrect type"""

    def __init__(self, field: str, expected_type: str, received_type: str):
        self.field = field
        self.expected_type = expected_type
        self.received_type = received_type
        super().__init__(
            f"Invalid type for field '{field}'. Expected {expected_type}, got {received_type}"
        )


class UnsupportedFieldTypeError(DataWrapperError):
    """Raised when attempting to set a field with an unsupported field type"""

    def __init__(self, field: str):
        self.field = field
        super().__init__(
            f"Field '{field}' is unsupported for set_field operation"
        )


class DataWrapperInterface(abc.ABC):
    def get_name(self) -> str: ...

    def get_format(self) -> str: ...

    def get_type(self) -> str: ...

    def serialize_to_dict(self) -> Dict[str, Any]: ...

    def serialize_to_json(self) -> str: ...

    def get_value(self) -> str: ...

    def set_value(self, value: str) -> None: ...

    def get_default(self) -> str: ...

    def get_is_artifact(self) -> bool: ...

    def set_field(self, field: str, value: Any) -> None: ...

    def get_field(self, field: str) -> Optional[Union[str, Any]]: ...

    def set_properties(self, value: Union[Properties, Dict[str, Any], None]) -> None: ...

    @property
    def DATA(self): ...


class DataWrapper(DataWrapperInterface):
    def __init__(self, proto_cls: FormatTypes):
        descriptor = proto_cls.DESCRIPTOR
        for field in descriptor.fields:
            # Set default if field has one
            has_field = proto_cls.HasField(field.name) if field.label != field.LABEL_REPEATED else True
            if not has_field and field.has_default_value:
                if field.enum_type:
                    default_enum = field.enum_type.values_by_number[field.default_value].name
                    setattr(proto_cls, field.name, default_enum)
                else:
                    setattr(proto_cls, field.name, field.default_value)
        self._proto_cls_initialised = proto_cls

    @property
    def DATA(self):  # type: ignore
        return self._proto_cls_initialised

    def get_name(self) -> str:
        return self._proto_cls_initialised.name

    def get_format(self) -> str:
        return gen_types.Format.DESCRIPTOR.values_by_number[
            self._proto_cls_initialised.format
        ].name

    def get_type(self) -> str:
        return self._proto_cls_initialised.type

    def get_value(self) -> str:
        return self._proto_cls_initialised.value

    def set_value(self, value) -> None:
        self._proto_cls_initialised.value = value
    
    def get_default(self) -> str:
        return self._proto_cls_initialised.default

    def get_is_artifact(self) -> bool:
        return self._proto_cls_initialised.is_artifact

    def get_proto(self) -> FormatTypes:
        return self._proto_cls_initialised

    def serialize_to_dict(self) -> typing.Dict[str, typing.Any]:
        return MessageToDict(
            self._proto_cls_initialised,
            preserving_proto_field_name=True,
            use_integers_for_enums=False,
            always_print_fields_with_no_presence=True,
        )

    def serialize_to_json(self) -> str:
        return MessageToJson(
            self._proto_cls_initialised, 
            preserving_proto_field_name=True,     
            use_integers_for_enums=False, 
            always_print_fields_with_no_presence=True,
        )

    def from_dict(self, d: Dict[str, Any]) -> None:
        ParseDict(d, self._proto_cls_initialised, ignore_unknown_fields=True)

    def set_properties(self, value: Union[Properties, Dict[str, Any], None]):
        if not hasattr(self._proto_cls_initialised, "properties"):
            raise FieldNotFoundError("properties")

        # if not isinstance(value, dict):
        # TODO: check if value is oneOf Properties

        fd = self._proto_cls_initialised.DESCRIPTOR.fields_by_name["properties"]
        message_type = fd.message_type._concrete_class

        if value is None:
            self._proto_cls_initialised.ClearField("properties")
            return 

        if isinstance(value, dict):
            proto_msg = message_type()
            ParseDict(value, proto_msg, ignore_unknown_fields=False)
            value = proto_msg
        else:
            if not isinstance(value, fd.message_type._concrete_class):
                raise InvalidFieldTypeError(
                    "properties",
                    message_type.__name__,
                    value.DESCRIPTOR.full_name
                )
        fv = getattr(self._proto_cls_initialised, fd.name, None)
        if fv is None:
            fv = message_type()
            setattr(self._proto_cls_initialised, fd.name, fv)
        fv.CopyFrom(value)

    def set_field(self, field: str, value: Any) -> None:
        if not hasattr(self._proto_cls_initialised, field):
            raise FieldNotFoundError(field)
        field_descriptor = self._proto_cls_initialised.DESCRIPTOR.fields_by_name[field]

        if field_descriptor.label == field_descriptor.LABEL_REPEATED:
            # handle repeated fields
            # Note: Message.HasField cannot tell you whether a repeated field is set or not.
            # for that you have to check the length
            if (
                    field_descriptor.message_type
                    and field_descriptor.message_type.has_options
                    and field_descriptor.message_type.GetOptions().map_entry
            ):
                map_field = getattr(self._proto_cls_initialised, field)
                if not isinstance(value, dict):
                    raise InvalidFieldTypeError(field, "dict", type(value).__name__)
                map_field.update(value)
            else:
                f = getattr(self._proto_cls_initialised, field)
                f.extend(value if isinstance(value, (list, tuple)) else [value])
        elif field_descriptor.message_type:
            raise UnsupportedFieldTypeError(field)
        else:
            setattr(self._proto_cls_initialised, field, value)

    def get_field(self, field: str) -> Optional[Union[str, Any]]:
        if not hasattr(self._proto_cls_initialised, field):
            return None
        fd = self._proto_cls_initialised.DESCRIPTOR.fields_by_name[field]
        if fd.label == fd.LABEL_REPEATED:
            return getattr(self._proto_cls_initialised, field)
        if self._proto_cls_initialised.HasField(field):
            try:
                return getattr(self._proto_cls_initialised, field)
            except AttributeError:
                pass
        elif fd.has_default_value:
            return fd.default_value
        return None


def RasterFromDict(
        d: Dict[str, Any], wrap: bool = False
) -> Union[gen_types.Raster, DataWrapper]:
    r = gen_types.Raster()
    ParseDict(d, r, ignore_unknown_fields=True)
    if not wrap:
        return r
    dw = DataWrapper(r)
    return dw


def VectorFromDict(
        d: Dict[str, Any], wrap: bool = False
) -> Union[gen_types.Vector, DataWrapper]:
    v = gen_types.Vector()
    ParseDict(d, v, ignore_unknown_fields=True)
    if not wrap:
        return v
    dw = DataWrapper(v)
    return dw


def TabularFromDict(
        d: Dict[str, Any], wrap: bool = False
) -> Union[gen_types.Tabular, DataWrapper]:
    t = gen_types.Tabular()
    ParseDict(d, t, ignore_unknown_fields=True)
    if not wrap:
        return t
    dw = DataWrapper(t)
    return dw


def DateFromDict(
        d: Dict[str, Any], wrap: bool = False
) -> Union[gen_types.Date, DataWrapper]:
    t = gen_types.Date()
    ParseDict(d, t, ignore_unknown_fields=True)
    if not wrap:
        return t
    dw = DataWrapper(t)
    return dw


def StringFromDict(
        d: Dict[str, Any], wrap: bool = False
) -> Union[gen_types.String, DataWrapper]:
    s = gen_types.String()
    ParseDict(d, s, ignore_unknown_fields=True)
    if not wrap:
        return s
    dw = DataWrapper(s)
    return dw


def NumberFromDict(
        d: Dict[str, Any], wrap: bool = False
) -> Union[gen_types.Number, DataWrapper]:
    n = gen_types.Number()
    ParseDict(d, n, ignore_unknown_fields=True)
    if not wrap:
        return n
    dw = DataWrapper(n)
    return dw


def FromDict(d: Dict[str, Any], wrap: bool = False) -> Union[Data, DataWrapper]:
    fmt = data_pb2.Format.Value(d["format"])
    if "value" in d:
        d["value"] = _convert_legacy_value_primitives_to_string_(d["value"])
    if fmt == data_pb2.Format.raster:
        return RasterFromDict(d, wrap)
    elif fmt == data_pb2.Format.vector:
        return VectorFromDict(d, wrap)
    elif fmt == data_pb2.Format.tabular:
        return TabularFromDict(d, wrap)
    elif fmt == data_pb2.Format.date:
        return DateFromDict(d, wrap)
    elif fmt == data_pb2.Format.string:
        return StringFromDict(d, wrap)
    else:
        return NumberFromDict(d, wrap)

def _convert_legacy_value_primitives_to_string_(v: Union[int, float, str, bool]):
    if isinstance(v, bool):
        return str(v).lower()
    elif isinstance(v, int) or isinstance(v, float):
        return str(v)
    return v

