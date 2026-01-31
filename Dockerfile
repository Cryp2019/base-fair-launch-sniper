FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY sniper_bot.py .
COPY database.py .
COPY trading.py .
COPY security_scanner.py .
COPY admin.py .
COPY payment_monitor.py .

# Create directory for database
RUN mkdir -p /app/data

# Run the bot
CMD ["python", "sniper_bot.py"]

