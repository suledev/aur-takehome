FROM python:3.12-slim

WORKDIR /app

COPY . /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Generate/update poetry.lock inside the image and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry lock \
    && poetry install --no-interaction --no-ansi


EXPOSE 8000


CMD ["uvicorn", "aurora.app.api:app", "--host", "0.0.0.0", "--port", "8000"]