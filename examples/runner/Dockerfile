FROM ghcr.io/osgeo/gdal:ubuntu-small-3.6.3

WORKDIR /app

ARG EXECUTOR

ENV EXECUTOR=${EXECUTOR}
RUN apt-get update && \
    apt-get install -y python3.10 python3-pip wget && \
    pip3 install --upgrade pip

ENV PYTHONBUFFERED 1

COPY examples/runner/requirements.txt .

ADD python /app/clay/python/
RUN --mount=type=secret,id=CODEARTIFACT_AUTH_TOKEN \
    CODEARTIFACT_AUTH_TOKEN=$(cat /run/secrets/CODEARTIFACT_AUTH_TOKEN) && \
    pip3 install --no-cache-dir \
    pixxel-datatypes \
    -r /app/clay/python/requirements/requirements-dev.txt \
    -r requirements.txt \
    --extra-index-url https://aws:${CODEARTIFACT_AUTH_TOKEN}@REDACTED.d.codeartifact.us-east-2.amazonaws.com/pypi/python/simple/

RUN pip3 install /app/clay/python

COPY examples/runner/demo-test /app

ENTRYPOINT ["python3", "entry.py"]
