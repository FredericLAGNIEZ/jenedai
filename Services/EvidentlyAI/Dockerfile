FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Au lieu de COPY workspace
RUN mkdir -p /app/workspace
#COPY workspace ./workspace

EXPOSE 7860

CMD ["evidently", "ui", "--workspace", "workspace", "--port", "7860", "--host", "0.0.0.0"]