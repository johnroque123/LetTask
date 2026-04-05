FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Production server
CMD ["gunicorn", "task.wsgi:application", "--bind", "0.0.0.0:8000"]