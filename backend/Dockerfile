FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
COPY main.py .

RUN pip install -r requirements.txt

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]