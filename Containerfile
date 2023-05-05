FROM docker.io/library/python:3

WORKDIR /app

COPY requirement.txt .

COPY db.py /app/db.py
COPY server.py /app/server.py
COPY queryLLM.py /app/queryLLM.py
COPY console.py /app/console.py
COPY loaderWrapper.py /app/loaderWrapper.py

RUN pip install --no-cache-dir -r requirement.txt

CMD ["python", "server.py"]
