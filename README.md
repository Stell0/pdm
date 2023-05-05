# PDM - Personal Data Manager

PDM aims to be a manager of all your personal data. It ingests your documents, creates embedding for them and allows you to chat with a ChatGPT that knows your stuff.
Data dat you offer to PDM are ingested and embedding are created using OpenAI, then text chunks and embedding are stored in a PostgreSQL Vectorstore. When you chat with assistant, semantically similar chunk of text are retrieved from ingested data, and are given as context to GPT.

## give data to PDM

Create a directory and put your files in it. At the moment .txt and .rtdocs are supported.
```
mkdir -p sources
```

.rtdocs are dump of ReadTheDocs websites created with the command:
```
wget -r -A.html -P my.documentation.rtdocs https://mydocumentation.readthedocs.io/en/latest/
```

## launch PostgreSQL pgvector storage and application

```
export OPENAI_API_KEY=xx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export POSTGRES_PASSWORD=some-password
```
Other available environment variables are:
```
POSTGRES_DATABASE - Default: postgres
POSTGRES_HOST - Default: 127.0.0.1
POSTGRES_PORT - Default: 5432
POSTGRES_USER - Default: postgres
```


```
podman run --name postgres -e POSTGRES_PASSWORD -d -p 5432:5432 --replace docker.io/ankane/pgvector:latest
```
Launch API server
```
podman run --rm --interactive=true --name pdm-server -e POSTGRES_PASSWORD -e OPENAI_API_KEY -p 5000:5000 --network=host --replace ghcr.io/stell0/pdm
```

Upload data
http://127.0.0.1:5000/upload

List of sources
GET http://127.0.0.1:5000/sources


Ask something to the assistant
The history parameter is optional, it is used to give context to the assistant if you want to follow up on a previous question.
```
curl 'http://127.0.0.1:5000/ask' -H 'Content-Type: application/json' -X POST --data '{"question": "What is CQR?","history":""}'
```


Launch interactive shell
```
podman exec -it --interactive=true --name pdm-cli -e POSTGRES_PASSWORD -e OPENAI_API_KEY pdm-server python3 console.py
```

## Langchain

Of course all of that is possible thanks to https://github.com/hwchase17/langchain 
