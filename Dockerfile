FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TELETHON_SESSION_PATH=/home/app/telethonbot \
    TELEGRAM_SESSION_DIR=/home/app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt gunicorn supervisor

RUN groupadd --system app \
    && useradd --system --gid app --create-home --home-dir /home/app app

COPY --chown=app:app . .
COPY supervisord.conf /etc/supervisor/conf.d/bot.conf

USER app

EXPOSE 5000

CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/bot.conf"]
