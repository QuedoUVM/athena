FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent.py app_api.py notion_tools.py ./

EXPOSE 8000

CMD ["uvicorn", "app_api:app", "--host", "0.0.0.0", "--port", "8000"]
