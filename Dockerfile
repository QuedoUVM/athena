FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
# streamlit is only needed for Streamlit Cloud, not for the FastAPI server.
# Filter it out so Docker doesn't pull in pandas/numpy/pyarrow/pillow unnecessarily.
RUN grep -v '^streamlit' requirements.txt \
    | pip install --no-cache-dir --timeout 120 --retries 5 -r /dev/stdin

COPY agent.py app_api.py notion_tools.py ./

EXPOSE 8000

CMD ["uvicorn", "app_api:app", "--host", "0.0.0.0", "--port", "8000"]
