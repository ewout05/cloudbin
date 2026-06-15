# Use a lightweight Python base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the dependency list
COPY requirements.txt .

# Update pip and install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the full app directory into the container
COPY . .

# Expose the default port Flask runs on
EXPOSE 8080

# Set the start command using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
