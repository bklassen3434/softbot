FROM python:3.10-slim

WORKDIR /app

COPY ./app /app/app
COPY requirements.txt /app/

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
