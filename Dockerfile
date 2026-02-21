# LinkedIn Job Analysis - Docker Image
# =====================================

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p data/raw data/processed outputs/reports outputs/visualizations logs config/alerts

# Set environment variables
ENV PYTHONUNBUFFERED=1
# Expose ports
EXPOSE 5000 8000

# Default command
CMD ["python", "scripts/dashboard.py"]
