FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml poetry.lock* ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-root
COPY modeling ./modeling
CMD ["python", "-m", "modeling.train"]
