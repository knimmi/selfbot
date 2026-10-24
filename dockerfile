FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install git required for discord.py-self
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash botuser
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R botuser:botuser /app
USER botuser

CMD ["python", "bot.py"]