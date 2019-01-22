FROM python:latest

COPY requirements.txt /app/
WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python3", "server.py"]