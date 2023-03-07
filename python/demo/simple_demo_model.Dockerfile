FROM crk2hub.azurecr.io/pygdal-ubuntu-small:latest

ARG MATTER_TOKEN_NAME
ARG MATTER_TOKEN_PASS
ARG RAMEN_TOKEN_NAME
ARG RAMEN_TOKEN_PASS
ENV PYTHONBUFFERED 1
COPY . app/
WORKDIR app/

RUN apt-get update

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install -r requirements.txt
RUN pip install --index-url https://${MATTER_TOKEN_NAME}:${MATTER_TOKEN_PASS}@gitlab.com/api/v4/projects/38506821/packages/pypi/simple matter
RUN pip install --index-url https://${RAMEN_TOKEN_NAME}:${RAMEN_TOKEN_PASS}@gitlab.com/api/v4/projects/38508365/packages/pypi/simple ramen==0.0.7
ENTRYPOINT [ "python3", "demo_simple_model.py" ]
