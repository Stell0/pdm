FROM docker.io/library/python:3

WORKDIR /app

COPY requirement.txt .

COPY db.py /app/db.py
COPY server.py /app/server.py
COPY queryLLM.py /app/queryLLM.py
COPY console.py /app/console.py
COPY loaderWrapper.py /app/loaderWrapper.py
RUN apt-get update && apt-get install -y pandoc
RUN pip install --no-cache-dir -r requirement.txt
RUN apt-get clean autoclean && apt-get autoremove --yes && rm -rf /var/lib/dpkg/info/* /var/lib/cache/* /var/lib/log/* && touch /var/lib/dpkg/status

CMD ["python", "server.py"]