FROM python:3.12.1-slim
WORKDIR /app
EXPOSE 8000
COPY requirements.txt ./
COPY .env ./
RUN apt-get update && apt-get install -y curl
# Устанавливаем зависимости python не пересобирая их
RUN pip install --no-cache --no-cache-dir -r requirements.txt
# Копирование кода приложения
COPY app.py /app/
ENTRYPOINT ["uvicorn"]
CMD ["app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]