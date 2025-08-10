FROM python:3.11-slim
WORKDIR /app
RUN pip install fastapi uvicorn httpx pydantic slowapi
COPY app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
