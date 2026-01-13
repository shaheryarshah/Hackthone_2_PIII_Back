# Dockerfile for Hugging Face Spaces deployment
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements-hf.txt /app/
RUN pip install --no-cache-dir -r requirements-hf.txt

# Copy project
COPY . /app/

# Expose the port
EXPOSE $PORT

# Run the application
CMD ["sh", "-c", "python app.py"]