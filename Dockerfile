FROM python:latest

COPY requirements.txt /app/
WORKDIR /app

RUN pip install -r requirements.txt

CMD ["gunicorn", "-c", "wsgi.conf.py", "wsgi:app"]