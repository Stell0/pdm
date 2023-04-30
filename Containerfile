FROM docker.io/library/python:3

WORKDIR /app

COPY requirement.txt .

RUN mkdir -p /app/sources

COPY pdm.py pdm.py

RUN pip install --no-cache-dir -r requirement.txt

CMD ["python", "pdm.py"]
