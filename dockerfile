FROM python:3.11-slim
WORKDIR /app
RUN pip install flask youtube-transcript-api
COPY app.py .
CMD ["python", "app.py"]