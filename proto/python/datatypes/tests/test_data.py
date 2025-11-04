import unittest
from dataclasses import dataclass
from typing import Any, Dict, Union

from google.protobuf.json_format import ParseError

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
        assert rw.get_format() == "raster"

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
            self.TestCase(name="number", proto=data.Number(), expected=data.Format.number)
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
            self.TestCase(name="number", proto=data.Number(), expected=False)
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
            self.TestCase(name="number", proto=data.Number(), expected=data.Format.number)
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
            self.TestCase(name="number", proto=data.Number(), expected=False)
        ]
        for tc in test_cases:
            dw = data.DataWrapper(tc.proto)
            self.assertEqual(dw.get_field("is_artifact"), tc.expected, f"failed for: {tc.name}")
    
    def test_default_if_field_and_default_unset(self):
        v = data.Vector()
        self.assertEqual(v.value, "")
        
        dw = data.DataWrapper(v)
        self.assertEqual(dw.get_name(), '')

def test__convert_legacy_value_primittives_to_string():
    v = data._convert_legacy_value_primitives_to_string_(1)
    assert v == "1"
    v = data._convert_legacy_value_primitives_to_string_(1.23456)
    assert v == "1.23456"
    v = data._convert_legacy_value_primitives_to_string_(False)
    assert v == "false"