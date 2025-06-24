FROM python:3.11-slim

RUN useradd -ms /bin/bash exporter

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY cloudstack_exporter.py ./

USER exporter

EXPOSE 9116

# Gunicorn for production WSGI
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:9116", "cloudstack_exporter:app"]
