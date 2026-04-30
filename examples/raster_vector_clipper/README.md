# RasterVectorClipper - API Test Block

A stable Clay block for clipping raster data using vector geometries. Designed for end-to-end API testing with MinIO storage.

## Overview

This block takes a raster (GeoTIFF) and a vector (GeoJSON) as inputs and performs spatial clipping operations. It's specifically designed to be stable and robust for automated testing scenarios.

## Features

- **Robust Input Validation**: Checks file existence, CRS compatibility, and spatial intersection
- **Automatic CRS Reprojection**: Handles mismatched coordinate reference systems
- **Error Handling**: Comprehensive error handling with informative messages
- **Buffer Support**: Optional buffer distance parameter for geometry expansion
- **Multi-geometry Support**: Handles multiple geometries in vector files
- **Latest Clay Types**: Uses modern `datatypes` instead of legacy types

## Architecture

The block follows Clay's standard architecture with clear separation of responsibilities:

- **Preprocess**: Download inputs from MinIO, validate files, check CRS compatibility and spatial intersection
- **Inference**: Perform actual raster clipping using rasterio.mask
- **Postprocess**: Prepare output datatypes (Clay SDK handles MinIO upload automatically)

## Inputs

- `input_raster`: GeoTIFF raster file to be clipped
- `input_vector`: GeoJSON vector file defining clipping geometry

## Outputs

- `clipped_raster`: Clipped raster output
- `output_vector`: Original vector geometry used for clipping

## Parameters

- `buffer_distance` (float, default: 0.0): Optional buffer distance to apply to vector geometry

## Dependencies

- `rasterio>=1.3.0`: Industry standard for raster I/O operations
- `geopandas>=0.13.0`: Vector data handling and CRS operations
- `shapely>=2.0.0`: Geometry operations and validation
- `fiona>=1.9.0`: Vector file I/O
- `pyproj>=3.4.0`: CRS transformations

## Testing with MinIO

[MinIO](https://min.io/) is an open-source, S3-compatible object store. This
example uses MinIO as a local stand-in for AWS S3 so you can run the full
upload/download flow without cloud credentials.

### Local Development

1. **Start MinIO services**:
   ```bash
   docker-compose up -d
   ```

2. **Access MinIO Console**: 
   - URL: http://localhost:9001
   - Username: `minioadmin`
   - Password: `minioadmin`

3. **Test data is automatically uploaded** to `test-inputs` bucket:
   - `2024_02_24_mosaic.tif` (raster)
   - `Clay_Demo-05-03-2024.geojson` (vector)

### Running the Block

```bash
# Install dependencies
make setup

# Run tests
python raster_vector_clipper/test_block.py

# Package block (if needed)
make package
```

### Docker Testing

```bash
# Build image
docker build -t raster-clipper:latest .

# Run with docker-compose
docker-compose up
```

## Error Handling

The block includes comprehensive error handling for:

- **File Validation**: Missing or corrupted files
- **CRS Issues**: Incompatible or missing coordinate reference systems
- **Geometry Validation**: Invalid geometries (auto-fixed when possible)
- **Spatial Intersection**: Non-intersecting raster and vector data
- **Memory Management**: Large file handling
- **Format Support**: Unsupported file formats

## Example Usage

The block can be tested with the provided sample data or integrated into larger Clay workflows for automated testing scenarios.

## Development Notes

- Uses latest Clay SDK features with `is_artifact: true` for automatic MinIO handling
- Follows Clay coding standards and logging practices
- Designed for reliability in automated testing environments
- No legacy datatypes - uses modern `datatypes` module

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.
