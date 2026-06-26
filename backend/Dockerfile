FROM python:3.11-slim

# Set the working directory inside the container.
# All subsequent commands run from here.
WORKDIR /app

# Install system-level dependencies.
# gcc and libpq-dev are required to compile psycopg2 (the PostgreSQL driver).
# libmupdf-dev supports PyMuPDF for PDF text extraction.
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first — Docker caches this layer.
# If requirements.txt hasn't changed, pip install is skipped on rebuilds.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Default command — uvicorn runs the FastAPI app.
# --reload watches for file changes (useful in dev since backend/ is volume-mounted).
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]