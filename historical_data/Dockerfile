# syntax=docker/dockerfile:1
FROM python:3.10-slim
WORKDIR /historical_data
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt
EXPOSE 5000
COPY . .
ENV PYTHONPATH="${PYTHONPATH}:/historical_data"
CMD ["python", "-m", "main"]