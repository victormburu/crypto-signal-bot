# Use lightweight Python base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy dependency file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Environment variables (optional)
ENV PYTHONUNBUFFERED=1

# Run your bot
# Change working directory if main.py is under /app/script
WORKDIR /app/script
# Option 1: Run main.py (signal bot)
# Option 2: Run scheduler.py if you want automated evaluation every 2 hours
CMD ["python", "main.py"]
