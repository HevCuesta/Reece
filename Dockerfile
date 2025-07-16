# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app/

# Install required packages
RUN pip install -r requirements.txt

# Run the bot when the container launches
CMD ["python", "main.py"]
