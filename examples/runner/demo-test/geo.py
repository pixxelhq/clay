# import rasterio as rio
# import os
# from clay.types import Raster
from clay.core import set_disclaimer

# def mosaic(r: Raster) -> int:
#     print("here", r.Value)
#     print(os.getcwd())
#     example_raster = rio.open(r.Value)
#     print(f"shape of raster: {example_raster.shape}")
#     return sum(example_raster.shape)

def add(a: int, b: int) -> int:
    set_disclaimer("This is an addition function")
    return a + b