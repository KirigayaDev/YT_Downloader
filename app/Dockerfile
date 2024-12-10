FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN python3 -m venv venv

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python3", "main.py"]