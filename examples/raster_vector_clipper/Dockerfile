FROM ghcr.io/osgeo/gdal:ubuntu-small-3.6.3

WORKDIR /app

RUN apt-get update && \
    apt-get install -y python3.10 python3-pip wget && \
    pip3 install --upgrade pip

ENV PYTHONBUFFERED 1

COPY api-test/raster_vector_clipper/requirements.txt .

# Add local clay package
ADD python /app/clay/python/

RUN --mount=type=secret,id=CODEARTIFACT_AUTH_TOKEN \
    CODEARTIFACT_AUTH_TOKEN=$(cat /run/secrets/CODEARTIFACT_AUTH_TOKEN) && \
    pip3 install --no-cache-dir \
    pixxel-datatypes \
    -r requirements.txt \
    --extra-index-url https://aws:${CODEARTIFACT_AUTH_TOKEN}@REDACTED.d.codeartifact.us-east-2.amazonaws.com/pypi/python/simple/

# Install local clay package
RUN pip3 install /app/clay/python

COPY api-test/raster_vector_clipper/raster_vector_clipper /app
COPY api-test/raster_vector_clipper/clay.yaml /
COPY api-test/raster_vector_clipper/assets /app/assets

ENTRYPOINT ["python3", "entry.py"]
