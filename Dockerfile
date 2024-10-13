# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Install Node.js and npm
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the Python requirements file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Install React dependencies and build the app
WORKDIR /app/frontend/automated-dividend-investing
RUN npm install
RUN npm run build

# Move back to the app root
WORKDIR /app

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run Gunicorn when the container launches
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]