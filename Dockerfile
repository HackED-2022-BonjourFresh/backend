FROM python:3.8.12-slim

WORKDIR /app

COPY app.py helpers.py run.sh requirements.txt .

RUN pip install --upgrade pip && \ 
    pip install -r requirements.txt

ENTRYPOINT ./run.sh