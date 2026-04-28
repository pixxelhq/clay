from typing import Any, Dict

import datatypes as T
from clay.core import BlockWrapper


class {{.BlockName}}(BlockWrapper):
    """Your block implementation.

    The Clay block lifecycle has four stages:
        1. setup()       — Called once at startup. Initialize your block, load weights, etc.
        2. preprocess()  — Called per request. Validate and prepare inputs.
        3. inference()   — Called per request. Run your core block logic.
        4. postprocess() — Called per request. Format results as output datatypes.

    Important:
        - Parameter names in setup() must match the "parameters" names in clay.yaml.
        - Argument names in preprocess() must match the "inputs" names in clay.yaml.
        - Keys returned from postprocess() must match the "outputs" names in clay.yaml.

    Supported datatypes (import as `datatypes` or `datatypes as T`):
        T.String  — Text data          (format: "string")
        T.Number  — Numeric data        (format: "number")
        T.Raster  — GeoTIFF files       (format: "raster")
        T.Vector  — GeoJSON files       (format: "vector")
        T.Tabular — CSV/table data      (format: "tabular")
        T.Date    — Date/time data      (format: "date")

    Each datatype has at minimum: name, value, format, type, description.
    Geospatial types (Raster, Vector, Tabular) also have a `properties` field.
    Access values with: input_arg.value
    """

    def setup(self, weight: int, **kwargs) -> None:
        """Initialize your block. Called once at startup.

        Parameter names here must match the "parameters" section in clay.yaml.

        For this template, clay.yaml defines:
            parameters:
              - name: weight    # <- matches the `weight` argument below
                type: int
                default: 5
        """
        self.weight = weight
        self.logger.info(f"Block initialized with weight={weight}")

    async def preprocess(
        self,
        input1: T.String,
        input2: T.Number,
    ) -> Dict[str, Any]:
        """Validate and prepare inputs. Called per request.

        Argument names here must match the "inputs" section in clay.yaml.

        For this template, clay.yaml defines:
            inputs:
              - name: input1    # <- matches the `input1` argument (format: string -> T.String)
                format: string
                type: str
              - name: input2    # <- matches the `input2` argument (format: number -> T.Number)
                format: number
                type: int

        Returns:
            Dict whose keys become the argument names for inference().
        """
        self.logger.info(f"Preprocessing: input1={input1.value}, input2={input2.value}")

        # Example: validate inputs
        if not input1.value:
            raise ValueError("input1 cannot be empty")

        return {"input1": input1, "input2": input2}

    async def inference(self, input1: T.String, input2: T.Number) -> Dict[str, Any]:
        """Run your core block logic. Called per request.

        Arguments here match the keys returned by preprocess().

        Returns:
            Dict whose keys become the argument names for postprocess().
        """
        self.logger.info("Running inference")

        # Example: use the parameter from setup() and inputs from preprocess()
        result = input2.value * self.weight

        return {"result": result}

    async def postprocess(self, result: int) -> Dict[str, T.Data]:
        """Format results as output datatypes. Called per request.

        Arguments here match the keys returned by inference().

        Must return a dict of datatypes whose keys match the "outputs" section in clay.yaml.

        For this template, clay.yaml defines:
            outputs:
              - name: output1   # <- matches the "output1" key below (format: number -> T.Number)
                format: number
                type: int

        Returns:
            Dict[str, T.Data] mapping output names to datatype instances.
        """
        self.logger.info(f"Postprocessing: result={result}")

        return {
            "output1": T.Number(name="output1", value=str(result)),
        }
