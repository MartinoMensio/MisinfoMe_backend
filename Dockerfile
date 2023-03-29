FROM python:3.11-alpine as builder

WORKDIR /app
# install dependencies
RUN pip install pdm
# gcc may be needed for some dependencies
# RUN apt-get update && apt-get install -y gcc
RUN apk --no-cache add musl-dev linux-headers g++

# ADD requirements.txt /app/requirements.txt
COPY pyproject.toml pdm.lock README.md /app/
# RUN pip install .
# install pdm in .venv by default
RUN pdm install --prod --no-lock --no-editable

# run stage
# FROM python:3.11-slim as production
FROM python:3.11-alpine as production
# pip and setuptools have open vulnerabilities
RUN pip uninstall setuptools pip -y
WORKDIR /app
COPY --from=builder /app /app
COPY api /app/api
COPY supervisord.conf /app/

# celery non root user
# RUN useradd -ms /bin/bash celery
# RUN chown -R celery:celery /app
# USER celery

# set environment as part of CMD because pdm installs there
CMD . .venv/bin/activate && supervisord