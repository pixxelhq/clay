from typing import Any, Dict, List, Union

import datatypes

from clay import exceptions, types


def TypeFromDict(d: Dict[str, Any], to_v2: bool = False) -> Union[types.LegacyTypeWrapper, datatypes.DataWrapper]:
    dict_is_v2 = "version" in d
    res: Union[types.LegacyTypeWrapper, datatypes.DataWrapper]
    if not dict_is_v2:
        t = types._FormatModelMap[d["format"]].model_validate(d)
        res = wrap_types(t, to_v2)
    else:
        t = datatypes.FromDict(d, False)
        res = wrap_types(t, to_v2)
    return res


def lift_underlying_type(
    dw: datatypes.DataWrapperInterface,
) -> Union[datatypes.Data, types.Data]:
    if isinstance(dw, datatypes.DataWrapper):
        return dw._proto_cls_initialised
    assert isinstance(dw, types.LegacyTypeWrapper)  # for type checker
    return dw._legacy_type


def ListOfLegacyTypesToV2Types(types: List[types.Data]) -> List[datatypes.DataWrapper]:
    result = []
    for t in types:
        result.append(t.to_types_v2())
    return result


def ConvertTypesV2SchemaToV1(t: datatypes.Data) -> types.Data:
    f = t.format
    if f == datatypes.Format.raster:
        assert isinstance(t, datatypes.Raster)
        return types.Raster.from_types_v2(t)
    elif f == datatypes.Format.vector:
        assert isinstance(t, datatypes.Vector)
        return types.Vector.from_types_v2(t)
    elif f == datatypes.Format.tabular:
        assert isinstance(t, datatypes.Tabular)
        return types.Tabular.from_types_v2(t)
    elif f == datatypes.Format.date:
        assert isinstance(t, datatypes.Date)
        return types.Date.from_types_v2(t)
    elif f == datatypes.Format.string:
        assert isinstance(t, datatypes.String)
        return types.String.from_types_v2(t)
    elif f == datatypes.Format.number:
        assert isinstance(t, datatypes.Number)
        return types.Number.from_types_v2(t)
    raise exceptions.UnknownFormatException(str(f))


def wrap_types(
    t: Union[types.Data, datatypes.Data, types.LegacyTypeWrapper, datatypes.DataWrapper],
    convert_pydantic_to_proto: bool = True,
):
    if isinstance(t, types.LegacyTypeWrapper):
        if convert_pydantic_to_proto:
            return t.DATA.to_types_v2()
        else:
            return t
    elif isinstance(t, types.Data):
        if convert_pydantic_to_proto:
            return t.to_types_v2()
        return types.LegacyTypeWrapper(t)
    elif isinstance(t, datatypes.Data):
        if not convert_pydantic_to_proto:
            t = ConvertTypesV2SchemaToV1(t)
            return types.LegacyTypeWrapper(t)
        return datatypes.DataWrapper(t)
    else:
        return t


def WrapTypes(
    items: List[Union[types.Data, datatypes.Data, types.LegacyTypeWrapper, datatypes.DataWrapper]],
    convert_pydantic_to_proto: bool = True,
) -> List[datatypes.DataWrapperInterface]:
    result: List[datatypes.DataWrapperInterface] = []
    for t in items:
        if isinstance(t, types.LegacyTypeWrapper):
            if convert_pydantic_to_proto:
                result.append(t.DATA.to_types_v2())
            else:
                result.append(t)
        elif isinstance(t, types.Data):
            if convert_pydantic_to_proto:
                result.append(t.to_types_v2())
                continue
            result.append(types.LegacyTypeWrapper(t))
        elif isinstance(t, datatypes.Data):
            if not convert_pydantic_to_proto:
                t = ConvertTypesV2SchemaToV1(t)
                result.append(types.LegacyTypeWrapper(t))
                continue
            result.append(datatypes.DataWrapper(t))
        else:
            result.append(t)
    return result
