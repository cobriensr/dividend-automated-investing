# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install necessary tools and Node.js
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy the Python requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Install React dependencies and build the app
WORKDIR /app/frontend/automated-dividend-investing
RUN npm cache clean --force
RUN npm install -g npm@latest
RUN npm run build

# Move back to the app root
WORKDIR /app

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Create a logs directory
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Run Gunicorn when the container launches
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "wsgi:app"]