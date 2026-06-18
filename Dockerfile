# Use official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the necessary libraries
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project code into the container
COPY . .