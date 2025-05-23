# Use an official Python base image
FROM python:3.12-slim

# 1) Install Java for tabula
RUN apt-get update && apt-get install -y default-jre && apt-get clean

# Create working directory and copy code
WORKDIR /app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8080 for Cloud Run
EXPOSE 8080

# Use gunicorn (or another WSGI server) to run Django on port 8080
CMD ["gunicorn", "--bind=0.0.0.0:8080", "--timeout=600", "ResearchParsing.wsgi"]

ENV GUNICORN_CMD_ARGS="--log-level debug"
