FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt is inside manager/
COPY manager/requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the Django project from manager/
COPY manager/ .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "task.wsgi:application", "--bind", "0.0.0.0:8000"]