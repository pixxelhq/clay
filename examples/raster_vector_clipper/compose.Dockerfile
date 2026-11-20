FROM ghcr.io/osgeo/gdal:ubuntu-small-3.6.3

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

RUN apt-get update && \
    apt-get install -y python3.10 python3-pip wget

ENV PYTHONBUFFERED 1

COPY examples/raster_vector_clipper/requirements.txt .

# Add local clay package
ADD python /app/clay/python/

RUN uv pip install --system --no-cache \
    pixxel-datatypes \
    -r requirements.txt

# Install local clay package
RUN uv pip install --system /app/clay/python

COPY examples/raster_vector_clipper/raster_vector_clipper /app
COPY examples/raster_vector_clipper/clay.yaml /
COPY examples/raster_vector_clipper/assets /app/assets

ENTRYPOINT ["python3", "entry.py"]
