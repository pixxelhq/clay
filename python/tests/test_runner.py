# type: ignore
import json
import os
from moto import mock_aws
import boto3
from unittest import mock
import unittest
from typing import Any
from unittest.mock import patch  # noqa
import pathlib
from pathlib import Path
from clay.core import ModelWrapper
from clay.logger import Logger
from clay.runners.runner import JobRunner
import datatypes

class TestJobRunner(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Load input JSON once for the whole class
        with (Path(__file__).parent / "sample_input.json").open() as f:
            cls.input_json = f.read()
    def setUp(self) -> None:
        os.makedirs("./workingdir", exist_ok=True)
        # creating dummy inputs
        self.mock_env_vars = {
            "EXECUTION_ID": "task123",
            "INPUT_JSON_ENV_KEY": "INPUT_JSON",
            "INPUT_JSON": self.input_json,
            "LOCAL_ARTIFACT_DOWNLOAD_PATH": "./workingdir/inputs",
            "REMOTE_OUTPUT_PATH": "s3://workingdir/clay/outputs",
            "REMOTE_INPUT_PATH": "s3://workingdir/clay/",
            "FORCE_INPUT_TYPES_TO_V2": "1",
            "CALLBACK_ENDPOINT": "http://localhost:3000/callback",
            "CALLBACK_HEADERS": "{}",
            "OUTPUT_JSON_PATH": "./workingdir/clay/outputs/",
            "OUTPUT_JSON_BASE_FILE_NAME": "spec.json",
        }
 
    @mock.patch("clay.callback.http_callback.requests.Session.post")
    async def test_read_inputs(self, mock_post) -> None:
        mock_response = mock.Mock()
        mock_response.json.return_value = {"data": {"successful_update": "True", "updated_fields": {}, "err": ""}}
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        class M(ModelWrapper):
            def __init__(self, config: str, logger: Logger = None) -> None:
                super().__init__(config, logger)

            def setup(self):
                pass

            async def preprocess(self, string, raster, vector) -> Any:
                return {"raster": raster, "string": string, "vector": vector}

            async def inference(self, raster, string, vector) -> None:
                dummy_raster = pathlib.Path("./clipped.tiff")
                dummy_raster.touch()
                

                return {"raster": str(dummy_raster), "string": "this is hello", "vector": vector}

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
                        name="result",
                        value=vector.value,
                            ),

                }
        with mock_aws():
            conn = boto3.resource("s3", region_name="us-east-2")
            conn.create_bucket(Bucket="workingdir", CreateBucketConfiguration={"LocationConstraint": "us-east-2"}) 
            env_patcher = unittest.mock.patch.dict(os.environ, self.mock_env_vars)
            env_patcher.start()
            a = JobRunner(
                "dummy",
                M,
                {"config": "./tests/dummy-spec.yml"},
                "./tests/dummy-spec.yml",
                None,
            )
            a.start()
            parsed_json = json.loads(self.input_json)

            def normalize(d):
                relevant = {k: d[k] for k in d if k in ['format', 'type', 'name', 'value', 'stac_url', 'properties']}
                if 'properties' in relevant:
                    relevant['properties'] = {k: relevant['properties'][k] for k in relevant['properties'] if k in ['bands', 'collection']}
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

        class M(ModelWrapper):
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

                return {"raster": str(dummy_raster), "string": "this is hello", "vector": vector}

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
                            )
                }
            
        with mock_aws():
            conn = boto3.client("s3", region_name="us-east-2")
            conn.create_bucket(Bucket="workingdir", CreateBucketConfiguration={"LocationConstraint": "us-east-2"})
            env_patcher = unittest.mock.patch.dict(os.environ, self.mock_env_vars)
            env_patcher.start()
            a = JobRunner(
                "dummy",
                M,
                {"config": "./tests/dummy-spec.yml"},
                "./tests/dummy-spec.yml",
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

        class M(ModelWrapper):
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

                return {"raster": str(dummy_raster), "string": "this is hello", "vector": vector}

            async def postprocess(self, raster, string, vector) -> Any:
                return {
                    "result": datatypes.Raster(
                        format=datatypes.Format.raster,
                        type="url",
                        is_artifact=True,
                        value=raster,
                            ),
                
                    "string": datatypes.String(
                        format=datatypes.Format.string,
                        type="str",
                       is_artifact=False,
                        value=string, 

                    ),
                    "vector": datatypes.Vector(
                        format=datatypes.Format.vector,
                        type="url",
                        is_artifact=True,
                        value=vector.value,
                            )
                }
            
        with mock_aws():
            conn = boto3.client("s3", region_name="us-east-2")
            conn.create_bucket(Bucket="workingdir", CreateBucketConfiguration={"LocationConstraint": "us-east-2"})
            env_patcher = unittest.mock.patch.dict(os.environ, self.mock_env_vars)
            env_patcher.start()
            a = JobRunner(
                "dummy",
                M,
                {"config": "./tests/dummy-spec.yml"},
                "./tests/dummy-spec.yml",
                None,
            )
            a.start()

            response = conn.list_objects_v2(Bucket="workingdir", Prefix="clay/inputs/") 
            keys = [obj["Key"] for obj in response.get("Contents", [])]
            assert "clay/inputs/raster/stac.json" in keys
            assert "clay/inputs/vector/vector.geojson" in keys
            env_patcher.stop()
   