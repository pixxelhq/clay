FROM python:3.9-alpine3.16

EXPOSE 8080

COPY . site/
WORKDIR site/

CMD ["python3", "-m", "http.server", "8080"]
