import inspect
import os
from contextlib import contextmanager
from typing import Any, Dict, Optional, Set

import datatypes

from clay import types

DEFAULT_IGNORE_DICT_FIELDS: Set[str] = set("version")


def XOR_on_none_value(A, B) -> bool:
    """Performs and XOR operation between A and B. Returns True if
    both are None or not None. Returns False if one is None and
    other is not None.
    """
    return (A is None) == (B is None)


class CustomLegacyAndProtoComparators:
    @classmethod
    def compare_raster_properties_viz(cls, legacy: Dict[str, Any], proto: Dict[str, Any]) -> bool:
        if legacy["type"] != proto["type"]:
            return False
        if "continuous" in legacy:
            if "continuous" not in proto:
                return False
            if not XOR_on_none_value(legacy["continuous"], proto["continuous"]):
                return False
            legacy_cont = legacy["continuous"]
            proto_cont = proto["continuous"]
            if legacy_cont.get("name") != proto_cont.get("color_map_name"):
                return False
            bandwise_range = []
            for band in legacy_cont.get("range", []):
                bandwise_range.append({"min": band[0], "max": band[1]})
            if bandwise_range != proto_cont.get("bandwise_range", []):  # type: ignore
                return False
        if "bucket" in legacy:
            if "bucket" not in proto:
                return False
            if not XOR_on_none_value(legacy.get("bucket", None), proto.get("bucket", None)):
                return False
            legacy_bucket = legacy["bucket"]
            proto_bucket = proto["bucket"]
            bandwise = []
            # bandwise: [[items=[{...}]]]
            for band in legacy_bucket:
                per_band = []
                for bi in band:
                    per_band.append(
                        {
                            "min": bi.get("range")[0],
                            "max": bi.get("range")[1],
                            "color_code": bi.get("color", ""),
                        }
                    )
                bandwise.append({"items": per_band})
            if proto_bucket.get("bandwise") != bandwise:
                print("VizBucket failing")
                return False
        if "discrete" in legacy:
            if "discrete" not in proto:
                return False
            if not XOR_on_none_value(legacy.get("discrete", None), proto.get("discrete", None)):
                return False
            legacy_discrete = legacy["discrete"]
            proto_discrete = legacy["discrete"]
            if legacy_discrete != proto_discrete:
                print("discrete viz failing")
                return False
        return True

    @classmethod
    def compare_raster_properties_discretization(cls, legacy: Dict[str, Any], proto: Dict[str, Any]):
        if legacy.get("type", "") != proto.get("type", ""):
            return False
        if not XOR_on_none_value(legacy.get("classes", None), proto.get("classes", None)):
            return False
        classes_legacy = legacy.get("classes", [])
        classes_proto = []
        for c in classes_legacy:
            classes_proto.append(
                {
                    "name": c.get("name"),
                    "color": c.get("color"),
                    "value": c.get("value"),
                    "range": c.get("range"),
                }
            )
        if classes_proto != classes_legacy:
            return False
        return True


def is_class_or_instance_of_class(x: Any) -> bool:
    return inspect.isclass(type(x))


def compare_legacy_and_proto_type_classes(
    legacy: types.Data,
    proto: datatypes.FormatTypes,
    parent_key: str = "",
    ignore_fields: Set[str] = set(),
    only_check_fields: Optional[Set[str]] = None,
):
    all_fields_equal = True

    legacy_alias_field_mapping = {name: field.alias for name, field in legacy.model_fields.items()}
    proto_fields = [f.name for f in proto.DESCRIPTOR.fields]

    legacy_attrs = vars(legacy)

    for key in legacy_attrs:
        key_alias = legacy_alias_field_mapping[key]
        full_key_path = f"{parent_key}.{key_alias}" if parent_key else key_alias
        if full_key_path in ignore_fields:
            continue

        if only_check_fields and full_key_path not in only_check_fields:
            continue

        if key_alias not in proto_fields:
            all_fields_equal = False
            break

        legacy_value = getattr(legacy, key)
        proto_value = getattr(proto, proto_fields[proto_fields.index(key_alias)])

        if is_class_or_instance_of_class(legacy_value) and is_class_or_instance_of_class(proto_value):
            cmp_result = compare_legacy_and_proto_type_classes(
                legacy_value,
                proto_value,
                full_key_path,  # type: ignore
                ignore_fields,  # type: ignore
            )
        else:
            cmp_result = legacy_value == proto_value
        if not cmp_result:
            all_fields_equal = False
            break
    return all_fields_equal


def compare_legacy_and_proto_dicts(
    legacy: Dict[str, Any],
    proto: Dict[str, Any],
    parent_key: str = "",
    ignore_dict_fields: Set[str] = DEFAULT_IGNORE_DICT_FIELDS,
    only_check_fields: Optional[Set[str]] = None,
):
    all_fields_equal = True
    for key in legacy:
        full_key_path = f"{parent_key}.{key}" if parent_key else key
        if full_key_path in ignore_dict_fields:
            continue

        if only_check_fields and full_key_path not in only_check_fields:
            continue

        if key not in proto:
            all_fields_equal = False
            break

        legacy_value = legacy[key]
        proto_value = proto[key]

        if key == "visualisation":
            cmp_result = CustomLegacyAndProtoComparators.compare_raster_properties_viz(
                legacy_value,
                proto_value,  # type: ignore
            )
        elif key == "discretisation":
            cmp_result = CustomLegacyAndProtoComparators.compare_raster_properties_discretization(
                legacy_value, proto_value
            )
        elif isinstance(legacy_value, dict) and isinstance(legacy_value, dict):
            cmp_result = compare_legacy_and_proto_dicts(legacy_value, proto_value, full_key_path, ignore_dict_fields)
        else:
            cmp_result = legacy_value == proto_value
        if not cmp_result:
            all_fields_equal = False
            break
    return all_fields_equal


@contextmanager
def set_envvar(key: str, value: Any):
    old_value = None
    if key in os.environ:
        old_value = os.environ[key]
    os.environ[key] = value
    try:
        yield
    finally:
        if old_value is not None:
            os.environ[key] = old_value
        else:
            os.environ.pop(key)
