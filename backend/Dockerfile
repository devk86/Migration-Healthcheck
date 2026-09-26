FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini entrypoint.sh ./
COPY app ./app

RUN chmod +x entrypoint.sh \
    && useradd --create-home --uid 10001 appuser

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
