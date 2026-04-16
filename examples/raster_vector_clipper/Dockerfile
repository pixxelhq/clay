FROM ghcr.io/osgeo/gdal:ubuntu-small-3.6.3

WORKDIR /app

RUN apt-get update && \
    apt-get install -y python3.10 python3-pip wget && \
    pip3 install --upgrade pip

ENV PYTHONBUFFERED 1

COPY examples/raster_vector_clipper/requirements.txt .

# Add local clay package
ADD python /app/clay/python/

RUN pip3 install --no-cache-dir \
    pixxel-datatypes \
    -r requirements.txt
    
# Install local clay package
RUN pip3 install /app/clay/python

COPY examples/raster_vector_clipper/raster_vector_clipper /app
COPY examples/raster_vector_clipper/clay.yaml /
COPY examples/raster_vector_clipper/assets /app/assets

ENTRYPOINT ["python3", "entry.py"]
