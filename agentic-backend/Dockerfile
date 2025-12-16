FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Install the project into /app
COPY . /app
WORKDIR /app

# Allow statements and log messages to immediately appear in the logs
ENV PYTHONUNBUFFERED=1

# Install dependencies
RUN uv sync

# Expose port (Heroku will assign dynamically)
EXPOSE 8000

# Run the FastAPI server
# Note: When using heroku.yml, the CMD is overridden by the 'run' section
CMD ["sh", "-c", "uv run uvicorn app.main:app --host=0.0.0.0 --port=${PORT:-8000}"]

