# REST API + portal.  docker build -t rmti-api .
# docker run -p 8000:8000 -e RMTI_API_CLIENTS='[...]' rmti-api      (portal at /portal/; see docs/api.md). Put TLS in front of it.
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir ".[api]"
EXPOSE 8000
RUN useradd -r -u 10001 rmti
USER rmti
CMD ["uvicorn", "rmti.api:app", "--host", "0.0.0.0", "--port", "8000"]
