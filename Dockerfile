FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY manager/requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY manager/ .

EXPOSE 8000

CMD ["sh", "-c", "python manage.py collectstatic --noinput && gunicorn task.wsgi:application --bind 0.0.0.0:8000"]