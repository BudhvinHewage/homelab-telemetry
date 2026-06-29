FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
COPY collector.py .

RUN pip install -r requirements.txt

CMD ["python", "collector.py"]