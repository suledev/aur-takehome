FROM python:3.12-slim

WORKDIR /app

COPY . /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Install dependencies from pyproject.toml and install the project
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi


EXPOSE 8000


CMD ["uvicorn", "aurora.app.api:app", "--host", "0.0.0.0", "--port", "8000"]