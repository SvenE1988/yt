FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir flask youtube-transcript-api==0.6.2
COPY app.py .
EXPOSE 8080
CMD ["python", "app.py"]
