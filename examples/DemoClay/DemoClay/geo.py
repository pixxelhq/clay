import rasterio as rio

from clay.types import Raster


def mosaic(r: Raster) -> int:
    example_raster = rio.open(r.Value)
    print(f"shape of raster: {example_raster.shape}")
    return sum(example_raster.shape)
