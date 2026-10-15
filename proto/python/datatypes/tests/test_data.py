import datetime as _dt
import unittest
from dataclasses import dataclass
from typing import Any, Dict, Union

import pytest
from google.protobuf.json_format import MessageToDict, ParseError

from datatypes import DataWrapper, data

ProtoTypes = Union[
    data.Raster,
    data.Vector,
    data.Tabular,
    data.Date,
    data.String,
    data.Number,
]


class TestCreateTypeFromDict(unittest.TestCase):
    @dataclass
    class TestCase:
        name: str
        d: Dict[str, Any]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def test_get_format(self):
        r = data.Raster(format="raster")
        rw = DataWrapper(r)
        assert rw.get_format() == data.FormatTypes.RASTER.value

    def test_set_metadata(self):
        r = data.Raster(format="raster")
        rw = DataWrapper(r)
        rw.set_field("metadata", {"a": "1"})
        m = rw.get_field("metadata")
        assert m == {"a": "1"}

        rw.set_field("metadata", {"b": "2"})
        m = rw.get_field("metadata")
        assert m == {"a": "1", "b": "2"}

    def test_set_asset_source(self):
        r = data.Raster(format="raster")
        rw = DataWrapper(r)
        with self.assertRaises(data.UnsupportedFieldTypeError):
            rw.set_field("asset_source", data.AssetSource(layer_name="id"))
            rw.get_field("asset_source")

    def test_set_description(self):
        r = data.Raster(format="raster")
        rw = DataWrapper(r)

        s = rw.get_field("description")
        assert s is None

        rw.set_field("description", "this is description")
        s = rw.get_field("description")
        assert s == "this is description"

    def test_set_properties(self):
        r = data.Raster(format="raster")
        rw = DataWrapper(r)

        with self.assertRaises(data.InvalidFieldTypeError):
            rw.set_properties(data.TabularProperties())

        rw.set_properties(data.RasterProperties(bands=["1"]))
        properties = rw.get_field("properties")
        assert isinstance(properties, data.RasterProperties)
        assert properties.bands == ["1"]

        rw.set_properties(data.RasterProperties(bands=["2"]))
        properties = rw.get_field("properties")
        assert isinstance(properties, data.RasterProperties)
        assert properties.bands == ["2"]

        rw.set_properties({"bands": ["100"]})
        properties = rw.get_field("properties")
        assert isinstance(properties, data.RasterProperties)
        assert properties.bands == ["100"]

        with self.assertRaises(ParseError):
            rw.set_properties({"Bands": ["200"]})

        rw.set_properties(None)
        properties = rw.get_field("properties")
        assert properties is None

    def test_get_properties(self):
        r = data.Raster(format="raster")
        rw = DataWrapper(r)

        s = rw.get_field("properties")
        assert s is None

        r = data.Raster(format="raster", properties=data.RasterProperties(bands=["1"]))
        rw = DataWrapper(r)
        s = rw.get_field("properties")
        assert s is not None
        assert isinstance(s, data.RasterProperties)


class Test_Defaults(unittest.TestCase):
    @dataclass
    class TestCase:
        name: str
        proto: data.Data
        expected: Any

    def test_default_format_via_direct_access(self):
        test_cases = [
            self.TestCase(name="raster", proto=data.Raster(), expected=data.Format.raster),
            self.TestCase(name="vector", proto=data.Vector(), expected=data.Format.vector),
            self.TestCase(name="tabular", proto=data.Tabular(), expected=data.Format.tabular),
            self.TestCase(name="date", proto=data.Date(), expected=data.Format.date),
            self.TestCase(name="string", proto=data.String(), expected=data.Format.string),
            self.TestCase(name="number", proto=data.Number(), expected=data.Format.number),
        ]
        for ti in test_cases:
            self.assertEqual(ti.proto.format, ti.expected, f"failed for {ti.name}")

    def test_default_is_artifact_via_direct_access(self):
        test_cases = [
            self.TestCase(name="raster", proto=data.Raster(), expected=True),
            self.TestCase(name="vector", proto=data.Vector(), expected=True),
            self.TestCase(name="tabular", proto=data.Tabular(), expected=True),
            self.TestCase(name="date", proto=data.Date(), expected=False),
            self.TestCase(name="string", proto=data.String(), expected=False),
            self.TestCase(name="number", proto=data.Number(), expected=False),
        ]
        for ti in test_cases:
            self.assertEqual(ti.proto.is_artifact, ti.expected, f"failed for {ti.name}")

    def test_default_format_via_get_field(self):
        test_cases = [
            self.TestCase(name="raster", proto=data.Raster(), expected=data.Format.raster),
            self.TestCase(name="vector", proto=data.Vector(), expected=data.Format.vector),
            self.TestCase(name="tabular", proto=data.Tabular(), expected=data.Format.tabular),
            self.TestCase(name="date", proto=data.Date(), expected=data.Format.date),
            self.TestCase(name="string", proto=data.String(), expected=data.Format.string),
            self.TestCase(name="number", proto=data.Number(), expected=data.Format.number),
        ]
        for tc in test_cases:
            dw = data.DataWrapper(tc.proto)
            self.assertEqual(dw.get_field("format"), tc.expected, f"failed for: {tc.name}")

    def test_default_is_artifact_via_get_field(self):
        test_cases = [
            self.TestCase(name="raster", proto=data.Raster(), expected=True),
            self.TestCase(name="vector", proto=data.Vector(), expected=True),
            self.TestCase(name="tabular", proto=data.Tabular(), expected=True),
            self.TestCase(name="date", proto=data.Date(), expected=False),
            self.TestCase(name="string", proto=data.String(), expected=False),
            self.TestCase(name="number", proto=data.Number(), expected=False),
        ]
        for tc in test_cases:
            dw = data.DataWrapper(tc.proto)
            self.assertEqual(dw.get_field("is_artifact"), tc.expected, f"failed for: {tc.name}")

    def test_default_if_field_and_default_unset(self):
        v = data.Vector()
        self.assertEqual(v.value, "")

        dw = data.DataWrapper(v)
        self.assertEqual(dw.get_name(), "")


def test__convert_legacy_value_primittives_to_string():
    v = data._convert_legacy_value_primitives_to_string_(1)
    assert v == "1"
    v = data._convert_legacy_value_primitives_to_string_(1.23456)
    assert v == "1.23456"
    v = data._convert_legacy_value_primitives_to_string_(False)
    assert v == "false"


# --- Roundtrip tests: proto type -> MessageToDict -> FromDict -> MessageToDict ---


def _roundtrip(obj, from_dict_fn):
    dumped = MessageToDict(obj, preserving_proto_field_name=True)
    rebuilt = from_dict_fn(dumped)
    assert MessageToDict(rebuilt, preserving_proto_field_name=True) == dumped
    return rebuilt


def test_raster_roundtrip_via_fromdict():
    raster = data.Raster(
        format=data.Format.raster,
        type="url",
        name="r",
        is_artifact=True,
        value="s3://bucket/key.tif",
    )
    _roundtrip(raster, data.RasterFromDict)


def test_vector_roundtrip_via_fromdict():
    vector = data.Vector(
        format=data.Format.vector,
        type="url",
        name="v",
        is_artifact=True,
        value="s3://bucket/key.geojson",
    )
    _roundtrip(vector, data.VectorFromDict)


def test_tabular_roundtrip_via_fromdict():
    tabular = data.Tabular(
        format=data.Format.tabular,
        type="url",
        name="t",
        is_artifact=True,
        value="s3://bucket/key.csv",
    )
    _roundtrip(tabular, data.TabularFromDict)


def test_date_roundtrip_via_fromdict():
    date = data.Date(
        format=data.Format.date,
        type="str",
        name="d",
        is_artifact=False,
        value="2026-04-21",
    )
    _roundtrip(date, data.DateFromDict)


def test_string_roundtrip_via_fromdict():
    string = data.String(
        format=data.Format.string,
        type="str",
        name="s",
        is_artifact=False,
        value="hello world",
    )
    _roundtrip(string, data.StringFromDict)


def test_number_roundtrip_via_fromdict():
    number = data.Number(
        format=data.Format.number,
        type="str",
        name="n",
        is_artifact=False,
        value="42.5",
    )
    _roundtrip(number, data.NumberFromDict)


def test_from_dict_dispatches_by_format():
    """The generic dispatcher routes by the `format` field to the correct proto type."""
    r = data.FromDict({"format": "raster", "name": "r", "value": "x.tif"})
    assert isinstance(r, data.Raster)
    assert r.name == "r"

    v = data.FromDict({"format": "vector", "name": "v", "value": "x.geojson"})
    assert isinstance(v, data.Vector)

    n = data.FromDict({"format": "number", "name": "threshold", "value": "0.5"})
    assert isinstance(n, data.Number)

    s = data.FromDict({"format": "string", "name": "label", "value": "foo"})
    assert isinstance(s, data.String)


def test_raster_roundtrip_with_nested_properties():
    """Roundtrip a Raster whose properties include nested visualisation + bands."""
    raster = data.Raster(
        format=data.Format.raster,
        type="url",
        name="r",
        is_artifact=True,
        value="s3://bucket/key.tif",
        properties=data.RasterProperties(
            bands=["B01", "B02", "B03"],
            source="planetary",
            collection="sentinel-2-l2a",
            visualisation=data.Visualization(
                type=data.VizTypes.continuous,
                continuous=data.ContinuousViz(
                    color_map_name="jet",
                    bandwise_range=[data.Range(min=0, max=1000)],
                ),
            ),
        ),
    )
    rebuilt = _roundtrip(raster, data.RasterFromDict)
    assert isinstance(rebuilt, data.Raster)
    # Sanity: the nested visualisation survived the roundtrip
    assert rebuilt.properties.visualisation.continuous.color_map_name == "jet"


# --- validate_input tests ---


def _wrapped(from_dict_fn, d) -> DataWrapper:
    """Call *FromDict with wrap=True and narrow the union return type to DataWrapper."""
    dw = from_dict_fn(d, wrap=True)
    assert isinstance(dw, DataWrapper)
    return dw


def test_validate_input_string_allowed_values_pass():
    s = _wrapped(data.StringFromDict, {"format": "string", "name": "mode", "value": "fast"})
    data.validate_input(s, {"validation": {"allowed_values": ["fast", "slow"]}})


def test_validate_input_string_allowed_values_fail():
    s = _wrapped(data.StringFromDict, {"format": "string", "name": "mode", "value": "bogus"})
    with pytest.raises(data.ValidationError):
        data.validate_input(s, {"validation": {"allowed_values": ["fast", "slow"]}})


def test_validate_input_number_min_max_pass():
    n = _wrapped(data.NumberFromDict, {"format": "number", "name": "threshold", "value": "0.5"})
    data.validate_input(n, {"validation": {"min_value": 0.0, "max_value": 1.0}})


def test_validate_input_number_min_max_fail():
    n = _wrapped(data.NumberFromDict, {"format": "number", "name": "threshold", "value": "2.0"})
    with pytest.raises(data.ValidationError):
        data.validate_input(n, {"validation": {"min_value": 0.0, "max_value": 1.0}})


def test_validate_input_no_validation_spec_is_noop():
    """If the spec has no 'validation' key, validate_input returns without error."""
    s = _wrapped(data.StringFromDict, {"format": "string", "name": "mode", "value": "anything"})
    data.validate_input(s, {"name": "mode", "format": "string"})


# --- Typed .value access (cast_typed_value + TypedDataView) ---


def test_cast_typed_value_int():
    assert data.cast_typed_value("5", "int") == 5
    assert data.cast_typed_value("-3", "Int") == -3


def test_cast_typed_value_float():
    assert data.cast_typed_value("1.5", "float") == 1.5
    assert data.cast_typed_value("2", "Float") == 2.0


@pytest.mark.parametrize("raw,expected", [("true", True), ("True", True), ("1", True), ("yes", True)])
def test_cast_typed_value_bool_truthy(raw, expected):
    assert data.cast_typed_value(raw, "bool") is expected


@pytest.mark.parametrize(
    "raw,expected",
    [("false", False), ("False", False), ("0", False), ("no", False), ("", False)],
)
def test_cast_typed_value_bool_falsy(raw, expected):
    assert data.cast_typed_value(raw, "boolean") is expected


def test_cast_typed_value_bool_invalid_raises():
    with pytest.raises(ValueError):
        data.cast_typed_value("maybe", "bool")


def test_cast_typed_value_passthrough_for_unknown_or_absent_type():
    assert data.cast_typed_value("42", None) == "42"
    assert data.cast_typed_value("42", "") == "42"
    # Unrecognised declared types (e.g. "url" on a raster) are not Python primitives,
    # so the raw string is returned unchanged.
    assert data.cast_typed_value("42", "url") == "42"
    assert data.cast_typed_value("hello", "str") == "hello"


def test_typed_data_view_uses_proto_type_field():
    n = data.Number(name="weight", type="int", value="5")
    view = data.TypedDataView(n)
    assert view.value == 5
    assert isinstance(view.value, int)


def test_typed_data_view_delegates_other_attributes():
    n = data.Number(name="weight", type="int", value="5")
    view = data.TypedDataView(n)
    assert view.name == "weight"
    assert view.type == "int"


def test_typed_data_view_no_type_returns_raw():
    # When the proto has no declared type, `.value` falls through as the raw string.
    n = data.Number(name="raw", value="5")
    view = data.TypedDataView(n)
    assert view.value == "5"


def test_data_wrapper_typed_view_round_trip():
    """End-to-end: a typed input parsed via FromDict round-trips through the typed view."""
    dw = data.FromDict(
        {"name": "weight", "format": "number", "type": "int", "value": 5},
        wrap=True,
    )
    assert isinstance(dw, DataWrapper)
    view = dw.typed_view()
    assert view.value == 5
    assert isinstance(view.value, int)
    # The proto still stores the value as a string for wire compat.
    assert dw.get_proto().value == "5"


# --- date validation ---


def _date(value: str) -> DataWrapper:
    return _wrapped(data.DateFromDict, {"format": "date", "name": "capture", "value": value})


@pytest.mark.parametrize(
    "value, validation",
    [
        ("2024-06-01", {}),
        ("2024-06-01", {"min_date": "2024-01-01", "max_date": "2024-12-31"}),
        ("2024-01-01", {"min_date": "2024-01-01"}),  # min inclusive
        ("2024-12-31", {"max_date": "2024-12-31"}),  # max inclusive
        ("2099-01-01", {"min_date": "2024-01-01"}),  # only min set
        ("", {"min_date": "2024-01-01"}),  # empty is unset, not invalid
        ("2024-06-01T12:00:00Z", {"date_format": "date_time", "min_date": "2024-01-01T00:00:00Z"}),
        ("2024-06-01T12:00:00+05:30", {"date_format": "date_time", "max_date": "2024-12-31T23:59:59Z"}),
    ],
)
def test_validate_input_date_pass(value, validation):
    data.validate_input(_date(value), {"validation": validation})


@pytest.mark.parametrize(
    "value, validation, msg",
    [
        ("2023-12-31", {"min_date": "2024-01-01"}, "before minimum"),
        ("2025-01-01", {"max_date": "2024-12-31"}, "after maximum"),
        ("01-03-2024", {"min_date": "2024-01-01"}, "not a valid date"),
        ("2024-6-1", {"min_date": "2024-01-01"}, "not a valid date"),  # must be zero-padded, as in Go
        ("2024-06-01T00:00:00Z", {"min_date": "2024-01-01"}, "not a valid date"),  # date_time value in date_only mode
        ("2024-06-01", {"min_date": "yesterday"}, "min_date 'yesterday' is not a valid date"),
        ("2024-06-01", {"max_date": "2024-13-01"}, "max_date '2024-13-01' is not a valid date"),
        (
            "2024-12-31T23:00:00-05:00",
            {"date_format": "date_time", "max_date": "2024-12-31T23:59:59Z"},
            "after maximum",
        ),
        (
            "2024-06-01T12:00:00",
            {"date_format": "date_time"},
            "not a valid date",
        ),  # naive value rejected in date_time mode
        ("2024-06-01", {"date_format": "date_time"}, "not a valid date"),  # bare date in date_time mode
        ("2024-06-01", {"date_format": "bogus"}, "unknown date_format"),
    ],
)
def test_validate_input_date_fail(value, validation, msg):
    with pytest.raises(data.ValidationError) as exc:
        data.validate_input(_date(value), {"validation": validation})
    assert msg in str(exc.value)
    assert "capture" in str(exc.value)


def test_date_validation_round_trips_through_proto():
    """The new fields survive FromDict/serialize, i.e. the regenerated bindings carry them."""
    spec = data.DateSpec()
    spec.validation.min_date = "2024-01-01"
    spec.validation.date_format = data.DateFormat.Value("date_time")
    d = MessageToDict(spec, preserving_proto_field_name=True)
    assert d["validation"] == {"min_date": "2024-01-01", "date_format": "date_time"}


# yaml.safe_load turns unquoted bounds into date/datetime objects; the proto
# string setter would raise a bare TypeError on those. (Objects are built
# directly here so the datatypes tests do not depend on pyyaml.)
def test_validate_input_date_accepts_unquoted_yaml_date_bounds():
    bounds = {"min_date": _dt.date(2024, 1, 1), "max_date": _dt.date(2024, 12, 31)}
    data.validate_input(_date("2024-06-01"), {"validation": bounds})
    with pytest.raises(data.ValidationError) as exc:
        data.validate_input(_date("2023-06-01"), {"validation": bounds})
    assert "before minimum 2024-01-01" in str(exc.value)


def test_validate_input_date_accepts_unquoted_yaml_datetime_bound():
    lower = _dt.datetime(2024, 1, 1, tzinfo=_dt.timezone.utc)
    data.validate_input(_date("2024-06-01T12:00:00Z"), {"validation": {"date_format": "date_time", "min_date": lower}})


def test_validate_input_date_unquoted_naive_datetime_bound_is_rejected_in_date_time_mode():
    naive = _dt.datetime(2024, 1, 1)  # isoformat() carries no offset
    with pytest.raises(data.ValidationError) as exc:
        data.validate_input(
            _date("2024-06-01T12:00:00Z"), {"validation": {"date_format": "date_time", "min_date": naive}}
        )
    assert "min_date" in str(exc.value) and "not a valid date" in str(exc.value)


def test_validate_input_date_non_string_bound_is_validation_error():
    with pytest.raises(data.ValidationError) as exc:
        data.validate_input(_date("2024-06-01"), {"validation": {"min_date": 20240101}})
    assert "min_date must be a string, got int" in str(exc.value)
