# Use an official Python image as the base image
FROM python:3.10-slim

# Set a working directory
WORKDIR /app

# Copy the dependencies file and install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port the application will run on
EXPOSE 8080

# Run the proxy server
CMD ["python", "llama_proxy.py"]
