import os
import tempfile
from typing import Any, Dict

import geopandas as gpd
import rasterio
import rasterio.mask
from rasterio.crs import CRS
from shapely.geometry import box
from shapely.errors import ShapelyError

import datatypes as T
from clay.core import ModelWrapper


class RasterVectorClipper(ModelWrapper):
    def setup(self, buffer_distance: float = 0.0, **hyperparameters) -> None:  # type: ignore
        """Initialize the model with parameters.

        Args:
            buffer_distance: Optional buffer distance to apply to vector geometry before clipping
        """
        self.buffer_distance = buffer_distance
        self.logger.info(f"RasterVectorClipper initialized with buffer_distance={buffer_distance}")

    async def preprocess(  # type: ignore
        self,
        input_raster: T.Raster,
        input_vector: T.Vector,
    ) -> Dict[str, Any]:
        """Preprocess inputs: validate files and perform initial checks.

        Args:
            input_raster: Input raster file (Clay will download from MinIO)
            input_vector: Input vector file (Clay will download from MinIO)

        Returns:
            Dict containing validated raster and vector data
        """
        self.logger.info("Starting preprocessing")

        # Validate inputs
        if not input_raster.value:
            raise ValueError("Input raster value is None or empty")
        if not input_vector.value:
            raise ValueError("Input vector value is None or empty")

        self.logger.info(f"Raster path: {input_raster.value}")
        self.logger.info(f"Vector path: {input_vector.value}")

        # Validate raster file
        try:
            with rasterio.open(input_raster.value) as src:
                raster_crs = src.crs
                raster_bounds = src.bounds
                raster_shape = (src.height, src.width)
                raster_bands = src.count

            self.logger.info(f"Raster CRS: {raster_crs}")
            self.logger.info(f"Raster bounds: {raster_bounds}")
            self.logger.info(f"Raster shape: {raster_shape}")
            self.logger.info(f"Raster bands: {raster_bands}")

        except Exception as e:
            raise ValueError(f"Failed to read raster file: {str(e)}")

        # Validate vector file
        try:
            gdf = gpd.read_file(input_vector.value)
            if gdf.empty:
                raise ValueError("Vector file contains no geometries")

            vector_crs = gdf.crs
            self.logger.info(f"Vector CRS: {vector_crs}")
            self.logger.info(f"Vector geometry count: {len(gdf)}")

            # Check geometry validity
            invalid_geoms = ~gdf.geometry.is_valid
            if invalid_geoms.any():
                self.logger.warning(f"Found {invalid_geoms.sum()} invalid geometries, attempting to fix")
                gdf.geometry = gdf.geometry.buffer(0)  # Fix invalid geometries

        except Exception as e:
            raise ValueError(f"Failed to read vector file: {str(e)}")

        # Check CRS compatibility
        if raster_crs != vector_crs:
            self.logger.info(f"CRS mismatch: raster={raster_crs}, vector={vector_crs}")
            self.logger.info("Will reproject vector to match raster CRS during inference")

        # Check spatial intersection
        raster_bbox = box(*raster_bounds)
        vector_bounds = gdf.total_bounds
        vector_bbox = box(*vector_bounds)

        if vector_crs and raster_crs and vector_crs != raster_crs:
            # Reproject vector bounds to raster CRS for intersection check
            vector_gdf_reproj = gdf.to_crs(raster_crs)
            vector_bbox_reproj = box(*vector_gdf_reproj.total_bounds)
            intersects = raster_bbox.intersects(vector_bbox_reproj)
        else:
            intersects = raster_bbox.intersects(vector_bbox)

        if not intersects:
            raise ValueError("Raster and vector geometries do not intersect")

        self.logger.info("Preprocessing completed successfully")
        return {"raster": input_raster, "vector": input_vector}

    async def inference(self, raster: T.Raster, vector: T.Vector) -> Dict[str, Any]:  # type: ignore
        """Perform raster clipping using vector geometry.

        Args:
            raster: Input raster data
            vector: Input vector data

        Returns:
            Dict containing clipped raster and original vector
        """
        self.logger.info("Starting inference (raster clipping)")

        try:
            # Read vector data
            gdf = gpd.read_file(vector.value)

            # Open raster
            with rasterio.open(raster.value) as src:
                raster_crs = src.crs

                # Reproject vector to match raster CRS if needed
                if gdf.crs != raster_crs:
                    self.logger.info(f"Reprojecting vector from {gdf.crs} to {raster_crs}")
                    gdf = gdf.to_crs(raster_crs)

                # Apply buffer if specified
                if self.buffer_distance > 0:
                    self.logger.info(f"Applying buffer distance: {self.buffer_distance}")
                    gdf.geometry = gdf.geometry.buffer(self.buffer_distance)

                # Combine all geometries into a single shape for clipping
                if len(gdf) > 1:
                    self.logger.info(f"Combining {len(gdf)} geometries for clipping")
                    combined_geom = gdf.geometry.unary_union
                    clip_shapes = [combined_geom]
                else:
                    clip_shapes = gdf.geometry.tolist()

                # Perform clipping
                self.logger.info("Performing raster clipping")
                clipped_data, clipped_transform = rasterio.mask.mask(
                    src, clip_shapes, crop=True, filled=False, nodata=src.nodata
                )

                # Get clipped metadata
                clipped_meta = src.meta.copy()
                clipped_meta.update({
                    "height": clipped_data.shape[1],
                    "width": clipped_data.shape[2],
                    "transform": clipped_transform,
                    "nodata": src.nodata if src.nodata is not None else -9999
                })

                self.logger.info(f"Clipped raster shape: {clipped_data.shape}")
                self.logger.info(f"Clipped transform: {clipped_transform}")

                # Save clipped raster to temporary file
                clipped_raster_path = os.path.join(tempfile.gettempdir(), "clipped_raster.tif")

                with rasterio.open(clipped_raster_path, 'w', **clipped_meta) as dst:
                    dst.write(clipped_data)

                self.logger.info(f"Clipped raster saved to: {clipped_raster_path}")

                return {
                    "clipped_raster_path": clipped_raster_path,
                    "original_vector": vector
                }

        except ShapelyError as e:
            raise ValueError(f"Geometry error during clipping: {str(e)}")
        except rasterio.errors.RasterioIOError as e:
            raise ValueError(f"Raster I/O error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during clipping: {str(e)}")

    async def postprocess(self, clipped_raster_path: str, original_vector: T.Vector) -> Dict[str, T.Data]:  # type: ignore
        """Postprocess results: prepare output data types.

        Args:
            clipped_raster_path: Path to clipped raster file
            original_vector: Original vector data

        Returns:
            Dict containing output raster and vector data types
        """
        self.logger.info("Starting postprocessing")

        try:
            # Create output data types - Clay SDK will automatically upload artifacts to MinIO
            clipped_raster_output = T.Raster(
                name="clipped_raster",
                value=clipped_raster_path,
                properties=T.RasterProperties(
                    dtype="float32"
                )
            )

            output_vector = T.Vector(
                name="output_vector",
                value=original_vector.value,
                properties=original_vector.properties
            )

            self.logger.info("Postprocessing completed successfully")

            return {
                "clipped_raster": clipped_raster_output,
                "output_vector": output_vector
            }

        except Exception as e:
            raise RuntimeError(f"Error during postprocessing: {str(e)}")
