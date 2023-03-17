FROM python:3.11-slim

# regex for python 3.11 requires gcc compilation (no binary wheels)
RUN apt-get update && apt-get -y install gcc

COPY requirements.txt /app/
WORKDIR /app

RUN pip install -r requirements.txt

CMD ["supervisord"]