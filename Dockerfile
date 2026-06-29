# Use Python 3.12 slim base image
FROM python:3.12-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Streamlit will be configured at runtime via command line
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Create a non-root user (uid 1000) and group
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Install system dependencies (if any) - adjust as needed
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc && \
#     rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port 8080 (Cloud Run provides $PORT at runtime, but documenting is good practice)
EXPOSE 8080

# Run Streamlit, using the PORT environment variable provided by Cloud Run
# Fallback to 8501 if PORT is not set (for local testing)
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0