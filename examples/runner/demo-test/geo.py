# import rasterio as rio
# import os
# from clay.types import Raster


# def mosaic(r: Raster) -> int:
#     print("here", r.Value)
#     print(os.getcwd())
#     example_raster = rio.open(r.Value)
#     print(f"shape of raster: {example_raster.shape}")
#     return sum(example_raster.shape)