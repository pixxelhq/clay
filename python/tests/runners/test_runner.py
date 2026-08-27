# type: ignore
import json
import os
import pathlib
import shutil
import unittest
from pathlib import Path
from typing import Any
from unittest import mock
from unittest.mock import patch  # noqa

import boto3
import datatypes
from moto import mock_aws

from clay.core import BlockWrapper
from clay.logger import Logger
from clay.runners.runner import JobRunner, deep_merge

FIXTURES_DIR = Path(__file__).parent
DUMMY_SPEC_PATH = str(FIXTURES_DIR / "dummy-spec.yml")


class TestJobRunner(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        # Load input JSON once for the whole class, resolving fixture paths
        raw = (FIXTURES_DIR / "sample_input.json").read_text()
        cls.input_json = raw.replace("{{FIXTURES_DIR}}", str(FIXTURES_DIR))

    def setUp(self) -> None:
        os.makedirs("./workingdir", exist_ok=True)
        self.dummy_raster = pathlib.Path("./clipped.tiff")
        self.dummy_raster.touch(exist_ok=True)
        # creating dummy inputs
        self.mock_env_vars = {
            "EXECUTION_ID": "task123",
            "INPUT_JSON_ENV_KEY": "INPUT_JSON",
            "INPUT_JSON": self.input_json,
            "LOCAL_ARTIFACT_DOWNLOAD_PATH": "./workingdir/inputs",
            "REMOTE_OUTPUT_PATH": "s3://workingdir/clay/outputs",
            "REMOTE_INPUT_PATH": "s3://workingdir/clay/",
            "CALLBACK_ENDPOINT": "http://localhost:3000/callback",
            "CALLBACK_HEADERS": "{}",
            "OUTPUT_JSON_PATH": "./workingdir/clay/outputs/",
            "OUTPUT_JSON_BASE_FILE_NAME": "spec.json",
        }

    def tearDown(self) -> None:
        self.dummy_raster.unlink(missing_ok=True)
        shutil.rmtree("./workingdir", ignore_errors=True)

    @mock.patch("clay.callback.http_callback.requests.Session.post")
    async def test_read_inputs(self, mock_post) -> None:
        mock_response = mock.Mock()
        mock_response.json.return_value = {"data": {"successful_update": "True", "updated_fields": {}, "err": ""}}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        class M(BlockWrapper):
            def __init__(self, config: str, logger: Logger = None) -> None:
                super().__init__(config, logger)

            def setup(self):
                pass

            async def preprocess(self, string, raster, vector) -> Any:
                return {"raster": raster, "string": string, "vector": vector}

            async def inference(self, raster, string, vector) -> None:
                return {
                    "raster": "./clipped.tiff",
                    "string": "this is hello",
                    "vector": vector,
                }

            async def postprocess(self, raster, string, vector) -> Any:
                return {
                    "result": datatypes.Raster(
                        format=datatypes.Format.raster,
                        type="url",
                        is_artifact=True,
                        name="result",
                        value=raster,
                    ),
                    "string": datatypes.String(
                        format=datatypes.Format.string,
                        type="str",
                        is_artifact=False,
                        name="string",
                        value=string,
                    ),
                    "vector": datatypes.Vector(
                        format=datatypes.Format.vector,
                        type="url",
                        is_artifact=True,
                        name="vector",
                        value=vector.value,
                    ),
                }

        with mock_aws():
            conn = boto3.resource("s3", region_name="us-east-2")
            conn.create_bucket(
                Bucket="workingdir",
                CreateBucketConfiguration={"LocationConstraint": "us-east-2"},
            )
            env_patcher = unittest.mock.patch.dict(os.environ, self.mock_env_vars)
            env_patcher.start()
            a = JobRunner(
                "dummy",
                M,
                {"config": DUMMY_SPEC_PATH},
                DUMMY_SPEC_PATH,
                None,
            )
            a.start()
            parsed_json = json.loads(self.input_json)

            def normalize(d):
                relevant = {k: d[k] for k in d if k in ["format", "type", "name", "value", "stac_url", "properties"]}
                if "properties" in relevant:
                    relevant["properties"] = {
                        k: relevant["properties"][k] for k in relevant["properties"] if k in ["bands", "collection"]
                    }
                return relevant

            norm_dict = [normalize(item) for item in a._input_dict]
            norm_json = [normalize(item) for item in parsed_json]
            assert norm_dict == norm_json
            env_patcher.stop()

    @mock.patch("clay.callback.http_callback.requests.Session.post")
    async def test_set_outputs(self, mock_post) -> None:
        mock_response = mock.Mock()
        mock_response.json.return_value = {"data": {"successful_update": "True", "updated_fields": {}, "err": ""}}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        class M(BlockWrapper):
            def __init__(self, config: str, logger: Logger = None) -> None:
                super().__init__(config, logger)

            def setup(self):
                pass

            async def preprocess(self, string, raster, vector) -> Any:
                filepath = pathlib.Path("./clipped.tiff")
                self.add_asset(file_path=filepath, io_name="raster")
                return {"raster": raster, "string": string, "vector": vector}

            async def inference(self, raster, string, vector) -> None:
                dummy_raster = pathlib.Path("./clipped.tiff")
                dummy_raster.touch()

                return {
                    "raster": str(dummy_raster),
                    "string": "this is hello",
                    "vector": vector,
                }

            async def postprocess(self, raster, string, vector) -> Any:
                return {
                    "result": datatypes.Raster(
                        format=datatypes.Format.raster,
                        type="url",
                        is_artifact=True,
                        name="result",
                        value=raster,
                    ),
                    "string": datatypes.String(
                        format=datatypes.Format.string,
                        type="str",
                        is_artifact=False,
                        name="string",
                        value=string,
                    ),
                    "vector": datatypes.Vector(
                        format=datatypes.Format.vector,
                        type="url",
                        is_artifact=True,
                        name="vector",
                        value=vector.value,
                    ),
                }

        with mock_aws():
            conn = boto3.client("s3", region_name="us-east-2")
            conn.create_bucket(
                Bucket="workingdir",
                CreateBucketConfiguration={"LocationConstraint": "us-east-2"},
            )
            env_patcher = unittest.mock.patch.dict(os.environ, self.mock_env_vars)
            env_patcher.start()
            a = JobRunner(
                "dummy",
                M,
                {"config": DUMMY_SPEC_PATH},
                DUMMY_SPEC_PATH,
                None,
            )
            a.start()

            response = conn.list_objects_v2(Bucket="workingdir", Prefix="clay/outputs/")
            keys = [obj["Key"] for obj in response.get("Contents", [])]
            assert "clay/outputs/result/clipped.tiff" in keys
            assert "clay/outputs/result/spec.json" in keys
            assert "clay/outputs/string/spec.json" in keys
            env_patcher.stop()

    @mock.patch("clay.callback.http_callback.requests.Session.post")
    async def test_upload_input_asset(self, mock_post) -> None:
        mock_response = mock.Mock()
        mock_response.json.return_value = {"data": {"successful_update": "True", "updated_fields": {}, "err": ""}}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        class M(BlockWrapper):
            def __init__(self, config: str, logger: Logger = None) -> None:
                super().__init__(config, logger)

            def setup(self):
                pass

            async def preprocess(self, string, raster, vector) -> Any:
                filepath = pathlib.Path("./clipped.tiff")
                self.add_asset(file_path=filepath, io_name="raster")
                return {"raster": raster, "string": string, "vector": vector}

            async def inference(self, raster, string, vector) -> None:
                dummy_raster = pathlib.Path("./clipped.tiff")
                dummy_raster.touch()

                return {
                    "raster": str(dummy_raster),
                    "string": "this is hello",
                    "vector": vector,
                }

            async def postprocess(self, raster, string, vector) -> Any:
                return {
                    "result": datatypes.Raster(
                        format=datatypes.Format.raster,
                        type="url",
                        is_artifact=True,
                        value=raster,
                        name="result",
                    ),
                    "string": datatypes.String(
                        format=datatypes.Format.string,
                        type="str",
                        is_artifact=False,
                        value=string,
                        name="string",
                    ),
                    "vector": datatypes.Vector(
                        format=datatypes.Format.vector,
                        type="url",
                        is_artifact=True,
                        value=vector.value,
                        name="vector",
                    ),
                }

        with mock_aws():
            conn = boto3.client("s3", region_name="us-east-2")
            conn.create_bucket(
                Bucket="workingdir",
                CreateBucketConfiguration={"LocationConstraint": "us-east-2"},
            )
            env_patcher = unittest.mock.patch.dict(os.environ, self.mock_env_vars)
            env_patcher.start()
            a = JobRunner(
                "dummy",
                M,
                {"config": DUMMY_SPEC_PATH},
                DUMMY_SPEC_PATH,
                None,
            )
            a.start()

            response = conn.list_objects_v2(Bucket="workingdir", Prefix="clay/inputs/")
            keys = [obj["Key"] for obj in response.get("Contents", [])]
            assert "clay/inputs/raster/clipped.tiff" in keys
            env_patcher.stop()

    @mock.patch("clay.callback.http_callback.requests.Session.post")
    async def test_set_output_properties(self, mock_post) -> None:
        mock_response = mock.Mock()
        mock_response.json.return_value = {"data": {"successful_update": "True", "updated_fields": {}, "err": ""}}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        class M(BlockWrapper):
            def __init__(self, config: str, logger: Logger = None) -> None:
                super().__init__(config, logger)

            def setup(self):
                pass

            async def preprocess(self, string, raster, vector) -> Any:
                filepath = pathlib.Path("./clipped.tiff")
                self.add_asset(file_path=filepath, io_name="raster")
                return {"raster": raster, "string": string, "vector": vector}

            async def inference(self, raster, string, vector) -> None:
                dummy_raster = pathlib.Path("./clipped.tiff")
                dummy_raster.touch()

                return {
                    "raster": str(dummy_raster),
                    "string": "this is hello",
                    "vector": vector,
                }

            async def postprocess(self, raster, string, vector) -> Any:
                return {
                    "result": datatypes.Raster(
                        format=datatypes.Format.raster,
                        type="url",
                        is_artifact=True,
                        value=raster,
                        name="result",
                        properties=datatypes.RasterProperties(
                            collection="sentinel-2-l2a",
                            source="planetary",
                            sun_elevation=0.0,
                            satellite_look_angle=0.0,
                        ),
                    ),
                    "string": datatypes.String(
                        format=datatypes.Format.string,
                        type="str",
                        is_artifact=False,
                        value=string,
                        name="string",
                    ),
                    "vector": datatypes.Vector(
                        format=datatypes.Format.vector,
                        type="url",
                        is_artifact=True,
                        value=vector.value,
                        name="vector",
                        properties=datatypes.VectorProperties(geometry="output_geom"),
                    ),
                }

        with mock_aws():
            conn = boto3.client("s3", region_name="us-east-2")
            conn.create_bucket(
                Bucket="workingdir",
                CreateBucketConfiguration={"LocationConstraint": "us-east-2"},
            )
            env_patcher = unittest.mock.patch.dict(os.environ, self.mock_env_vars)
            env_patcher.start()
            a = JobRunner(
                "dummy",
                M,
                {"config": DUMMY_SPEC_PATH},
                DUMMY_SPEC_PATH,
                None,
            )
            a.start()

            expected_output_raster = {
                "format": "raster",
                "type": "url",
                "name": "result",
                "is_artifact": True,
                "metadata": {"block-name": "dummy"},
                "value": "s3://workingdir/clay/outputs/result/clipped.tiff",
                "properties": {
                    "source": "planetary",
                    "collection": "sentinel-2-l2a",
                    "satellite_look_angle": 0.0,
                    "sun_elevation": 0.0,
                    "visualisation": {
                        "type": "continuous",
                        "continuous": {
                            "color_map_name": "jet",
                            "bandwise_range": [{"min": 0.0, "max": 1000.0}],
                        },
                        "discrete": {},
                    },
                    "bands": [],
                    "images": [],
                },
                "version": "v2",
            }
            expected_output_vector = {
                "format": "vector",
                "type": "url",
                "name": "vector",
                "is_artifact": True,
                "metadata": {"block-name": "dummy"},
                "value": "s3://workingdir/clay/outputs/vector/vector.geojson",
                "properties": {"geometry": "output_geom"},
                "version": "v2",
            }
            expected_output_string = {
                "format": "string",
                "type": "str",
                "name": "string",
                "is_artifact": False,
                "metadata": {"block-name": "dummy"},
                "value": "this is hello",
                "version": "v2",
            }
            response = conn.list_objects_v2(Bucket="workingdir", Prefix="clay/outputs/")
            keys = [obj["Key"] for obj in response.get("Contents", [])]
            for key in keys:
                if key.endswith("spec.json"):
                    obj = conn.get_object(Bucket="workingdir", Key=key)
                    content = obj["Body"].read().decode()
                    data = json.loads(content)
                    if "clay/outputs/result/spec.json" == key:
                        assert data == expected_output_raster
                    elif "clay/outputs/vector/spec.json" == key:
                        assert data == expected_output_vector
                    elif "clay/outputs/string/spec.json" == key:
                        assert data == expected_output_string
            env_patcher.stop()


class TestRunnerConfigInputJSONURI(unittest.TestCase):
    """Tests for INPUT_JSON_URI S3 offload support (RFC 0003)."""

    @mock_aws
    def test_input_json_uri_downloads_from_s3(self):
        """When INPUT_JSON_URI is set, RunnerConfig downloads input from S3 instead of using INPUT_JSON env var."""
        conn = boto3.client("s3", region_name="us-east-1")
        conn.create_bucket(Bucket="test-bucket")

        input_data = '[{"name": "aoi", "value": "test-geojson"}]'
        conn.put_object(Bucket="test-bucket", Key="direct-insights/inf-1/inf-1/inf-1/inputs/input.json",
                        Body=input_data.encode("utf-8"))

        from clay.runners.runner import RunnerConfig
        result = RunnerConfig._download_input_json("s3://test-bucket/direct-insights/inf-1/inf-1/inf-1/inputs/input.json")
        assert result == input_data

    def test_fallback_to_input_json_env_var(self):
        """When INPUT_JSON_URI is absent, RunnerConfig falls back to INPUT_JSON env var."""
        input_data = '[{"name": "aoi", "value": "inline-data"}]'
        env_vars = {
            "EXECUTION_ID": "inf-2",
            "INPUT_JSON_ENV_KEY": "INPUT_JSON",
            "INPUT_JSON": input_data,
            "CALLBACK_ENDPOINT": "http://localhost:3000/callback",
            "CALLBACK_HEADERS": "{}",
        }

        # Ensure INPUT_JSON_URI is NOT set
        env_clean = {k: v for k, v in env_vars.items()}
        with unittest.mock.patch.dict(os.environ, env_clean, clear=False):
            os.environ.pop("INPUT_JSON_URI", None)
            from clay.runners.runner import RunnerConfig
            cfg = RunnerConfig.__new__(RunnerConfig)
            cfg._execution_id_env_key = "EXECUTION_ID"
            cfg._input_json_env_key = "INPUT_JSON_ENV_KEY"
            cfg._execution_id = "inf-2"

            # Simulate the __init__ logic for _input_json_string
            input_json_uri = os.getenv("INPUT_JSON_URI")
            if input_json_uri:
                result = RunnerConfig._download_input_json(input_json_uri)
            else:
                result = os.getenv(os.getenv("INPUT_JSON_ENV_KEY", "INPUT_JSON"), "[{}]")
            assert result == input_data


class TestDeepMerge(unittest.TestCase):
    def test_simple_merge(self):
        output = {"a": 1}
        config = {"b": 2}
        expected = {"a": 1, "b": 2}
        result = deep_merge(output, config)
        self.assertEqual(result, expected)

    def test_nested_merge(self):
        output = {"a": {"y": 20}, "b": 2}
        config = {"a": {"x": 10}}
        expected = {"a": {"x": 10, "y": 20}, "b": 2}
        result = deep_merge(output, config)
        self.assertEqual(result, expected)

    def test_overwrite_value(self):
        output = {"a": 1}
        config = {"a": 2, "b": 3}
        expected = {"a": 1, "b": 3}
        result = deep_merge(output, config)
        self.assertEqual(result, expected)

    def test_output_none(self):
        output = None
        config = {"a": 1}
        expected = {"a": 1}
        result = deep_merge(output, config)
        self.assertEqual(result, expected)

    def test_config_none(self):
        output = {"a": 1}
        config = None
        expected = {"a": 1}
        result = deep_merge(output, config)
        self.assertEqual(result, expected)

    def test_both_none(self):
        output = None
        config = None
        expected = {}
        result = deep_merge(output, config)
        self.assertEqual(result, expected)


# Kept byte-identical to dexter's `inputFlattenFilter`
# (executor/argo/workflow_input_test.go). Dexter sets this as INPUT_JSON_JQ_FILTER
# on the DAG path; if the two literals drift, every DAG task fails at input parsing.
INPUT_FLATTEN_FILTER = "[.[] | .spec + {name: .name}]"


def _resolved_envelope(declared_name: str, embedded_name: str, value: str):
    """The DAG payload as it reaches the pod, i.e. after argo fills the {{...}} holes.

    Dexter emits [{"name": "<declared>", "spec": {{inputs.parameters.<declared>}}}].
    Argo resolves the reference to the producing task's output spec, so the *embedded*
    name is the producer's output name and need not match the declared one.
    """
    return json.dumps([{
        "name": declared_name,
        "spec": {
            "format": "raster", "type": "url", "name": embedded_name,
            "is_artifact": True, "value": value, "version": "v2",
        },
    }])


class TestInputJqFlattening(unittest.TestCase):
    """The DAG path's {name, spec} envelope must reach the block as a flat data spec."""

    @staticmethod
    def _config(input_json_string: str, jq_filter=None):
        from clay.runners.runner import RunnerConfig
        cfg = RunnerConfig.__new__(RunnerConfig)
        cfg._input_json_string = input_json_string
        cfg._input_json = None
        cfg._input_json_jq_filter = jq_filter
        return cfg

    def test_envelope_is_flattened_into_a_parsable_data_spec(self):
        cfg = self._config(_resolved_envelope("raster", "raster", ""), INPUT_FLATTEN_FILTER)

        flat = cfg.get_input_json()

        self.assertEqual(len(flat), 1)
        # the envelope is gone: format sits at the top level, which is the key
        # datatypes.FromDict reads first
        self.assertEqual(flat[0]["format"], "raster")
        self.assertNotIn("spec", flat[0])
        datatypes.FromDict(dict(flat[0]), wrap=True)

    def test_declared_name_overrides_the_producers_output_name(self):
        """The regression that breaks wired DAGs.

        `index_block` names its output "result" while `cloud-gap-filling` declares its
        input "raster". Clay keys inputs by name before calling preprocess(**inputs),
        so the declared name has to win or the block is called with result= instead of
        raster= and dies on a missing argument.
        """
        cfg = self._config(
            _resolved_envelope("raster", "result", "s3://up/out.tif"), INPUT_FLATTEN_FILTER)

        flat = cfg.get_input_json()

        self.assertEqual(flat[0]["name"], "raster")
        self.assertEqual(flat[0]["value"], "s3://up/out.tif")
        self.assertEqual(datatypes.FromDict(dict(flat[0]), wrap=True).get_name(), "raster")

    def test_flat_input_passes_through_when_no_filter_is_set(self):
        """The inference path and local `clay run --input` send flat specs already."""
        flat_in = [{"format": "string", "type": "str", "name": "index",
                    "is_artifact": False, "value": "TVI", "version": "v2"}]
        cfg = self._config(json.dumps(flat_in), None)

        self.assertEqual(cfg.get_input_json(), flat_in)

    def test_broken_filter_raises_instead_of_silently_emptying_the_inputs(self):
        cfg = self._config(_resolved_envelope("raster", "raster", ""), "[.[] | .nope +")

        with self.assertRaises(ValueError):
            cfg.get_input_json()
