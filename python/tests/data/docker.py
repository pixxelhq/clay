docker_opts_valid = {
    "args": ["A", "B"],
    "env": [{"name": "a", "value": 1}, {"name": "b", "value": 2}],
    "requirements": "a.txt",
    "runs": ["some random command", "some other command"],
}

valid_dockerfile = """FROM crk2hub.azurecr.io/pygdal-ubuntu-small:latest

ARG A
ARG B
ENV a 1
ENV b 2
COPY gitlab app/
WORKDIR app/

RUN apt-get update

RUN python3 -m pip install --upgrade pip &&\
    python3 -m pip install -r a.txt

CMD ["python3", "entry.py"]"""
