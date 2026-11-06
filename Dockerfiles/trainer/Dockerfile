FROM python:3.12-slim

WORKDIR /app

COPY Dockerfiles/trainer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pipeline/ pipeline/

CMD ["python", "-m", "pipeline.run"]
