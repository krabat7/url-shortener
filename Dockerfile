FROM python:3.12-slim

WORKDIR /app
COPY . /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["sh", "-c", "python app/init_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]