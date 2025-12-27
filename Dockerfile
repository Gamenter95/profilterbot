# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Set environment variables placeholder (will be set on Koyeb)
ENV API_ID=0
ENV API_HASH=""
ENV BOT_TOKEN=""

# Run bot
CMD ["python", "bot.py"]
