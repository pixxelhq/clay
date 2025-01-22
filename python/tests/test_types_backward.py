import unittest

import datatypes
from google.protobuf.json_format import MessageToDict

from clay import types

from .utils import (
    CustomLegacyAndProtoComparators,
    compare_legacy_and_proto_dicts,
)


class Test_BackwardCompatibility_RasterViz(unittest.TestCase):
    def test_all_viz_fields_set(self):
        proto = datatypes.Visualization(
            type=datatypes.VizTypes.bucket,
            continuous=datatypes.ContinuousViz(
                color_map_name="green",
                bandwise_range=[
                    datatypes.Range(min=-1, max=-2),
                    datatypes.Range(min=1, max=2),
                ],
            ),
            discrete={"1": "grass", "2": "water"},
            bucket=datatypes.BucketViz(
                bandwise=[
                    datatypes.ListOfBuckets(
                        items=[
                            datatypes.Bucket(color_code="red", min=-1, max=-2),
                            datatypes.Bucket(color_code="black", min=0, max=0.5),
                        ]
                    ),
                    datatypes.ListOfBuckets(items=[datatypes.Bucket(color_code="green", min=2, max=3)]),
                ]
            ),
        )
        legacy = types.RasterVisualisation(
            Type="bucket",
            Continuous=types.VizContinuous(ColorMapName="green", Range=[[-1, -2], [1, 2]]),
            Bucket=[
                [
                    types.VizBucket(ColorCode="red", Range=[-1, -2]),
                    types.VizBucket(ColorCode="black", Range=[0, 0.5]),
                ],
                [types.VizBucket(ColorCode="green", Range=[2, 3])],
            ],
            Discrete={"1": "grass", "2": "water"},
        )

        proto_dict = MessageToDict(
            proto,
            preserving_proto_field_name=True,
            use_integers_for_enums=False,
            always_print_fields_with_no_presence=True,
        )
        legacy_dict = legacy.model_dump(by_alias=True)
        equal = CustomLegacyAndProtoComparators.compare_raster_properties_viz(legacy_dict, proto_dict)
        if not equal:
            print("not equal (v1 -> v2)")
            assert legacy_dict == proto_dict

        legacy_from_proto = types.RasterVisualisation.from_types_v2(proto)
        assert legacy_from_proto == legacy


class Test_BackwardCompatibility_RasterDiscretization(unittest.TestCase):
    def test_all_fields_set(self):
        proto = datatypes.Discretization(
            type="index",
            classes=[
                datatypes.DiscretizationClass(
                    color="red",
                    name="grass",
                    value="123",
                    range=datatypes.Range(min=-1, max=0),
                ),
                datatypes.DiscretizationClass(
                    color="black",
                    name="water",
                    value="567",
                    range=datatypes.Range(min=1, max=2),
                ),
            ],
        )
        legacy = types.RasterDiscretization(
            Type="index",
            Classes=[
                types.DiscretizationItem(Name="grass", Color="red", Value="123", Range=[-1, 0]),
                types.DiscretizationItem(Name="water", Color="black", Value="567", Range=[1, 2]),
            ],
        )

        proto_dict = MessageToDict(
            proto,
            preserving_proto_field_name=True,
            use_integers_for_enums=False,
            always_print_fields_with_no_presence=True,
        )
        legacy_dict = legacy.model_dump(by_alias=True)
        equal = CustomLegacyAndProtoComparators.compare_raster_properties_discretization(legacy_dict, proto_dict)
        if not equal:
            assert legacy_dict == proto_dict

        legacy_from_proto = types.RasterDiscretization.from_types_v2(proto)
        assert legacy_from_proto == legacy


class Test_BackwardCompatibility_Raster(unittest.TestCase):
    def test_with_properties_unset(self):
        legacyType = types.Raster(
            name="raster",
            default="",
            value="123",
            is_artifact=True,
            metadata={"meta": "data"},
            group="group",
            type="url",
        )
        legacyType.DisplayName = "Raster"
        legacyType.Description = "some-desc"
        legacyType.Group = "group"

        generatedProtoClass = legacyType.to_types_v2()
        types_v2_dict = generatedProtoClass.serialize_to_dict()
        legacy_dict = legacyType.model_dump(by_alias=True)

        # we are checking whether the dicts produced by dumping the legacy pydantic type and the resulting proto
        # type are equivalent.
        equal = compare_legacy_and_proto_dicts(
            legacy_dict,
            types_v2_dict,
            "",
            ignore_dict_fields={"version", "properties", "area"},
        )
        if not equal:
            assert legacy_dict == types_v2_dict

        legacy_from_proto = types.Raster.from_types_v2(generatedProtoClass.DATA)  # type: ignore
        legacy_from_proto_dict = legacy_from_proto.model_dump(by_alias=True)
        assert legacy_from_proto_dict == legacy_dict

    def test_with_properties_set_but_viz_unset(self):
        legacyType = types.Raster(
            name="raster",
            default="",
            value="123",
            is_artifact=True,
            metadata={"meta": "data"},
            group="group",
            type="url",
        )
        legacyType.DisplayName = "Raster"
        legacyType.Description = "some-desc"
        legacyType.Group = "group"

        discretization = types.RasterDiscretization()
        discretization.Type = "index"
        discretization.Classes = [types.DiscretizationItem(Color="red", Name="grass", Value="1", Range=[-1, -2])]
        legacyType.Properties = types.RasterProperties(
            Bands=["B01"],
            Collection="sentinel-2",
            Source="elements",
            Dtype="uint8",
            SatelliteLookAngle=4.2,
            SunElevation=4.2,
            Date="1-1-1999",
            Images=["img-1"],
            Discretization=discretization,
        )

        generatedProtoClass = legacyType.to_types_v2()
        types_v2_dict = generatedProtoClass.serialize_to_dict()
        legacy_dict = legacyType.model_dump(by_alias=True)

        # area is excluded since at the time of writing clay.types didn't support area
        equal = compare_legacy_and_proto_dicts(
            legacy_dict,
            types_v2_dict,
            "",
            {"version", "area", "properties.discretization", "properties.visualisation", "default"},
        )
        if not equal:
            assert legacy_dict == types_v2_dict

        legacy_from_proto = types.Raster.from_types_v2(generatedProtoClass.DATA)  # type: ignore
        legacy_from_proto_dict = legacy_from_proto.model_dump(by_alias=True)
        assert legacy_from_proto_dict == legacy_dict

    def test_with_properties_set_but_discretization_unset(self):
        legacyType = types.Raster(
            name="raster",
            default="",
            value="123",
            is_artifact=True,
            metadata={"meta": "data"},
            group="group",
            type="url",
        )
        legacyType.DisplayName = "Raster"
        legacyType.Description = "some-desc"
        legacyType.Group = "group"

        visualisation = types.RasterVisualisation()
        visualisation.Type = "continuous"
        visualisation.Continuous = types.VizContinuous(ColorMapName="blue", Range=[[-1, -2]])
        visualisation.Bucket = [[types.VizBucket(Range=[-1, -2], ColorCode="#123")]]
        visualisation.Discrete = {"red": "grass"}

        legacyType.Properties = types.RasterProperties(
            Bands=["B01"],
            Collection="sentinel-2",
            Source="elements",
            Dtype="uint8",
            SatelliteLookAngle=4.2,
            SunElevation=4.2,
            Date="1-1-1999",
            Images=["img-1"],
            Visualisation=visualisation,
        )

        generatedProtoClass = legacyType.to_types_v2()
        types_v2_dict = generatedProtoClass.serialize_to_dict()
        legacy_dict = legacyType.model_dump(by_alias=True)

        # area is excluded since at the time of writing clay.types didn't support area
        equal = compare_legacy_and_proto_dicts(
            legacy_dict,
            types_v2_dict,
            "",
            {"version", "area", "properties.discretization", "default"},
        )
        if not equal:
            assert legacy_dict == types_v2_dict

        legacy_from_proto = types.Raster.from_types_v2(generatedProtoClass.DATA)  # type: ignore
        legacy_from_proto_dict = legacy_from_proto.model_dump(by_alias=True)
        assert legacy_from_proto_dict == legacy_dict

    def test_all_set(self):
        legacyType = types.Raster(
            name="raster",
            default="",
            value="123",
            is_artifact=True,
            metadata={"meta": "data"},
            group="group",
            type="url",
        )
        legacyType.DisplayName = "Raster"
        legacyType.Description = "some-desc"
        legacyType.Group = "group"

        visualisation = types.RasterVisualisation()
        visualisation.Type = "continuous"
        visualisation.Continuous = types.VizContinuous(ColorMapName="blue", Range=[[-1, -2]])
        visualisation.Bucket = [[types.VizBucket(Range=[-1, -2], ColorCode="#123")]]
        visualisation.Discrete = {"red": "grass"}

        discretization = types.RasterDiscretization()
        discretization.Type = "index"
        discretization.Classes = [types.DiscretizationItem(Color="red", Name="grass", Value="1", Range=[-1, -2])]
        legacyType.Properties = types.RasterProperties(
            Bands=["B01"],
            Collection="sentinel-2",
            Source="elements",
            Dtype="uint8",
            SatelliteLookAngle=4.2,
            SunElevation=4.2,
            Date="1-1-1999",
            Images=["img-1"],
            Discretization=discretization,
            Visualisation=visualisation,
        )

        generatedProtoClass = legacyType.to_types_v2()
        types_v2_dict = generatedProtoClass.serialize_to_dict()
        legacy_dict = legacyType.model_dump(by_alias=True)

        # area is excluded since at the time of writing clay.types didn't support area
        equal = compare_legacy_and_proto_dicts(
            legacy_dict,
            types_v2_dict,
            "",
            {"version", "area", "properties.discretization", "default"},
        )
        if not equal:
            assert legacy_dict == types_v2_dict

        legacy_from_proto = types.Raster.from_types_v2(generatedProtoClass.DATA)  # type: ignore
        legacy_from_proto_dict = legacy_from_proto.model_dump(by_alias=True)
        assert legacy_from_proto_dict == legacy_dict


class Test_BackwardCompatibility_Vector(unittest.TestCase):
    def test_all_set(self):
        legacy = types.Vector(
            name="vector",
            value="123",
            is_artifact=True,
            type="url",
            metadata={"meta": "data"},
            group="group",
            default="",
            properties=types.VectorProperties(Geometry="polygon"),
        )
        legacy.DisplayName = "Vector"
        legacy.Description = "some-vector"

        generated_proto_class = legacy.to_types_v2()
        generated_proto_dict = generated_proto_class.serialize_to_dict()
        legacy_dict = legacy.model_dump(by_alias=True)

        equal = compare_legacy_and_proto_dicts(legacy_dict, generated_proto_dict, "", {"version", "area", "default"})
        if not equal:
            assert legacy_dict == generated_proto_dict

        legacy_from_proto = types.Vector.from_types_v2(generated_proto_class.DATA)  # type: ignore
        legacy_from_proto_dict = legacy_from_proto.model_dump(by_alias=True)
        assert legacy_from_proto_dict == legacy_dict


class Test_BackwardCompatibility_Tabular(unittest.TestCase):
    def test_all_set(self):
        legacy = types.Tabular(
            name="tab",
            value="123",
            is_artifact=True,
            type="url",
            metadata={"meta": "data"},
            group="group",
            default="",
            properties=types.TabularProperties(
                FileSchema=types.TabularFileSchema(Headers=["COL1", "COL2"]),
                FileType="csv",
            ),
        )
        legacy.DisplayName = "Vector"
        legacy.Description = "some-vector"

        generated_proto_class = legacy.to_types_v2()
        generated_proto_dict = generated_proto_class.serialize_to_dict()
        legacy_dict = legacy.model_dump(by_alias=True)

        equal = compare_legacy_and_proto_dicts(legacy_dict, generated_proto_dict, "", {"version", "area", "default"})
        if not equal:
            assert legacy_dict == generated_proto_dict

        legacy_from_proto = types.Tabular.from_types_v2(generated_proto_class.DATA)  # type: ignore
        legacy_from_proto_dict = legacy_from_proto.model_dump(by_alias=True)
        assert legacy_from_proto_dict == legacy_dict


class Test_BackwardCompatibility_Date(unittest.TestCase):
    def test_all_set(self):
        legacy = types.Date(
            name="date",
            value="123",
            is_artifact=True,
            type="url",
            metadata={"meta": "data"},
            group="group",
            default="",
            properties=types.DateProperties(FromAoi=True),
        )
        legacy.DisplayName = "Some large vector"
        legacy.Description = "some-vector"

        generated_proto_class = legacy.to_types_v2()
        generated_proto_dict = generated_proto_class.serialize_to_dict()
        legacy_dict = legacy.model_dump(by_alias=True)

        equal = compare_legacy_and_proto_dicts(legacy_dict, generated_proto_dict, "", {"version", "area", "default"})
        if not equal:
            assert legacy_dict == generated_proto_dict

        legacy_from_proto = types.Date.from_types_v2(generated_proto_class.DATA)  # type: ignore
        legacy_from_proto_dict = legacy_from_proto.model_dump(by_alias=True)
        assert legacy_from_proto_dict == legacy_dict


class Test_BackwardCompatibility_String(unittest.TestCase):
    def test_all_set(self):
        legacy = types.String(
            name="string",
            value="123",
            is_artifact=True,
            type="url",
            metadata={"meta": "data"},
            group="group",
            default="",
        )
        legacy.DisplayName = "Some Large String"
        legacy.Description = "some-vector"

        generated_proto_class = legacy.to_types_v2()
        generated_proto_dict = generated_proto_class.serialize_to_dict()
        legacy_dict = legacy.model_dump(by_alias=True)

        equal = compare_legacy_and_proto_dicts(legacy_dict, generated_proto_dict, "", {"version", "area", "default"})
        if not equal:
            assert legacy_dict == generated_proto_dict

        legacy_from_proto = types.String.from_types_v2(generated_proto_class.DATA)  # type: ignore
        legacy_from_proto_dict = legacy_from_proto.model_dump(by_alias=True)
        assert legacy_from_proto_dict == legacy_dict


class Test_BackwardCompatibility_Number(unittest.TestCase):
    def test_all_set(self):
        legacy = types.Number(
            name="num",
            value="123",
            is_artifact=True,
            type="url",
            metadata={"meta": "data"},
            group="group",
            default="",
        )
        legacy.DisplayName = "Some Large Number"
        legacy.Description = "some-desc"

        generated_proto_class = legacy.to_types_v2()
        generated_proto_dict = generated_proto_class.serialize_to_dict()
        legacy_dict = legacy.model_dump(by_alias=True)

        equal = compare_legacy_and_proto_dicts(legacy_dict, generated_proto_dict, "", {"version", "area", "default"})
        if not equal:
            assert legacy_dict == generated_proto_dict

        legacy_from_proto = types.Number.from_types_v2(generated_proto_class.DATA)  # type: ignore
        legacy_from_proto_dict = legacy_from_proto.model_dump(by_alias=True)
        assert legacy_from_proto_dict == legacy_dict


def test_raster_viz_unset_fields_should_be_none_v2_to_v1():
    d = datatypes.Raster(properties=datatypes.RasterProperties(visualisation=datatypes.Visualization(type="discrete")))

    lt = types.Raster.from_types_v2(d)

    assert lt.Properties is not None
    assert lt.Properties.Visualisation is not None

    assert lt.Properties.Visualisation.Bucket is None
    assert lt.Properties.Visualisation.Discrete is None
    assert lt.Properties.Visualisation.Continuous is None
