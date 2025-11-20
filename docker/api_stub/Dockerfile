# Minimal Dockerfile to run the API stub server
FROM python:3.12-slim

# Create app directory
WORKDIR /app

# Copy the stub
COPY api_stub.py /app/api_stub.py

# Ensure logs are unbuffered
ENV PYTHONUNBUFFERED=1

# Expose the port used by the stub
EXPOSE 3000

# Run the stub
CMD ["python", "api_stub.py"]
