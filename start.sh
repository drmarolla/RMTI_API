#!/bin/sh
# One image, three roles. Cloud Run sets PORT; set RMTI_ROLE=api or ui there. Locally, both run side by side.
PORT="${PORT:-8501}"
case "${RMTI_ROLE:-both}" in
  api) exec uvicorn api:app --host 0.0.0.0 --port "$PORT" ;;
  ui)  exec streamlit run app.py --server.port "$PORT" --server.address 0.0.0.0 --server.headless true ;;
  *)   uvicorn api:app --host 0.0.0.0 --port 8000 &
       exec streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true ;;
esac
