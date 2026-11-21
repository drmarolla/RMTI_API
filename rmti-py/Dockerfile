# REST API container:  docker build -t rmti-api . && docker run -p 8000:8000 rmti-api   (docs at /docs)
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir ".[api]"
EXPOSE 8000
CMD ["uvicorn", "rmti.api:app", "--host", "0.0.0.0", "--port", "8000"]
