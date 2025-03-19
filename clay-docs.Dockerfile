FROM python:3.10.0-alpine

EXPOSE 8080

COPY . site/
WORKDIR site/

ENV PYTHONBUFFERED 1

RUN python3 -m pip install mkdocs-material mkdocstrings mkdocstrings-python mkdocs-autorefs mkdocs-schema-reader codespell tomli &&\
    apk add --no-cache make

COPY python/requirements/requirements-dev.txt .

RUN --mount=type=secret,id=CODEARTIFACT_AUTH_TOKEN \
    CODEARTIFACT_AUTH_TOKEN=$(cat /run/secrets/CODEARTIFACT_AUTH_TOKEN) && \
    pip3 install --no-cache-dir \
    pixxel-datatypes \
    --extra-index-url https://aws:${CODEARTIFACT_AUTH_TOKEN}@REDACTED.d.codeartifact.us-east-2.amazonaws.com/pypi/python/simple/ \
    -r requirements-dev.txt

RUN make build-docs

WORKDIR /site/mkdocs/site
ENTRYPOINT ["python", "-m", "http.server", "8080"]
