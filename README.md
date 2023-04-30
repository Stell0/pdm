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

## launch PostgreSQL pgvector storage

```
export OPENAI_API_KEY=xx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
export POSTGRES_PASSWORD=some-passowrd
export PGVECTOR_PASSWORD=${POSTGRES_PASSWORD}
podman pod create --name pdm --network=slirp4netns:allow_host_loopback=true --replace
podman run --pod=pdm --name postgres -e POSTGRES_PASSWORD -d --replace docker.io/ankane/pgvector:latest
podman run --pod=pdm --rm --interactive=true --name pdm -e PGVECTOR_PASSWORD -e OPENAI_API_KEY -v ./sources:/app/sources --replace ghcr.io/stell0/pdm
```

## Langchain

Of course all of that is possible thanks to https://github.com/hwchase17/langchain 