FROM python:3.10-slim
LABEL authors="Ata Can"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY main.py .

EXPOSE 5000

CMD ["python", "main.py"]
