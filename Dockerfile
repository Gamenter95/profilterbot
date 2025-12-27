# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Run bot
CMD ["python", "bot.py"]

RUN apt-get update && apt-get install -y tzdata ntpdate \
    && ntpdate pool.ntp.org

ENV TZ=UTC
