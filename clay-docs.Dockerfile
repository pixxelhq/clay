FROM python:3.9-alpine3.16

EXPOSE 8080

COPY . site/
WORKDIR site/


RUN python3 -m pip install mkdocs-material mkdocstrings mkdocstrings-python mkdocs-autorefs mkdocs-schema-reader codespell tomli &&\
    apk add --no-cache make

RUN make init-requirements &&\
    make build-docs

WORKDIR /site/mkdocs/site
ENTRYPOINT ["python", "-m", "http.server", "8080"]
