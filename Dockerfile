# Use a slim Python base image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install the requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set the entry point
ENTRYPOINT ["python", "-m", "beanbot"]
