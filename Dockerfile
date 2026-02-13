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
COPY encryption_utils.py .
COPY group_poster.py .
COPY onchain_analyzer.py .
COPY project_sponsors.py .
COPY sponsorship_processor.py .
COPY performers_tracker.py .
COPY scoring.py .

# Create directory for database
RUN mkdir -p /app/data

# Run the bot
CMD ["python", "sniper_bot.py"]

