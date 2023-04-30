from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import VectorStore
from langchain.vectorstores.pgvector import PGVector,DistanceStrategy
from langchain.text_splitter import TokenTextSplitter
from langchain.document_loaders import TextLoader
from langchain.llms import OpenAI
from typing import List
from langchain.docstore.document import Document
from langchain.chains import ConversationalRetrievalChain
import os
from pathlib import Path
import psycopg
from langchain.document_loaders import ReadTheDocsLoader

class MyReadTheDocsLoader(ReadTheDocsLoader):
	def load(self) -> List[Document]:
		"""Load documents."""
		from bs4 import BeautifulSoup

		def _clean_data(data: str) -> str:
			soup = BeautifulSoup(data, **self.bs_kwargs)
			data = []
			h1_tags = soup.find_all('h1')
			for h1_tag in h1_tags:
				if h1_tag and h1_tag.text:
					title = h1_tag.text.replace("¶", "")
				else:
					continue
				try:
					text = ''
					for p in h1_tag.find_next_siblings():
						if p.name == 'section' or '©' in p.text:
							break
						text += p.text + "\n\n"
					text = text.strip()
					data.append(title+"\n"+text)
				except:
					continue
				h2_tags = soup.find_all({'h2','h3'})
				for h2_tag in h2_tags:
					if h2_tag and h2_tag.text:
						section_title = h2_tag.text.replace("¶", "")
					else:
						continue
					try:
						text = ''
						for p in h2_tag.find_next_siblings():
							if p.name == 'section' or '©' in p.text:
								break
							text += p.text
						text = text.replace("¶", "").strip()
						data.append(title+' - '+section_title+"\n"+text)
					except:
						continue
			return "\n\n".join(data)

		docs = []
		for p in Path(self.file_path).rglob("*"):
			if p.is_dir():
				continue
			with open(p, encoding=self.encoding, errors=self.errors) as f:
				text = _clean_data(f.read())
				metadata = {"source": str(p)}
			docs.append(Document(page_content=text, metadata=metadata))
		return docs

def initdb():
	# initialize db
	embedding = OpenAIEmbeddings()
	CONNECTION_STRING = PGVector.connection_string_from_db_params(
    	driver=os.environ.get("PGVECTOR_DRIVER", "psycopg2"),
    	host=os.environ.get("PGVECTOR_HOST", "127.0.0.1"),
    	port=int(os.environ.get("PGVECTOR_PORT", "5432")),
    	database=os.environ.get("PGVECTOR_DATABASE", "postgres"),
    	user=os.environ.get("PGVECTOR_USER", "postgres"),
    	password=os.environ.get("PGVECTOR_PASSWORD", "postgres"),
	)

	# also connect to postgres and query it
	connection_string = 'dbname={dbname} host={host} port=5432 user={user} password={password}'
	connection_string = connection_string.format(
    	dbname=os.environ.get("PGVECTOR_DATABASE", "postgres"),
		host=os.environ.get("PGVECTOR_HOST", "127.0.0.1"),
		port=os.environ.get("PGVECTOR_PORT", "5432"),
		user=os.environ.get("PGVECTOR_USER", "postgres"),
		password=os.environ.get("PGVECTOR_PASSWORD", "postgres")
	)
	connection = psycopg.connect(connection_string)
	connection.autocommit = True
	cursor = connection.cursor()

	#create vector extension if not exists
	cursor.execute("CREATE EXTENSION IF NOT EXISTS vector") 

	vectordb = PGVector(
		connection_string=CONNECTION_STRING,
		embedding_function=embedding,
		distance_strategy=DistanceStrategy.COSINE
	)

	return (vectordb, connection, cursor)

def data_ingest(vectordb: VectorStore, connection: psycopg.connection, cursor: psycopg.cursor):
	# check if there are new sources in sources folder
	sources = os.listdir("sources")

	for source in sources:
		# skip source if it is already in db
		cursor.execute("select count(*) from public.langchain_pg_embedding where cmetadata->>'source' LIKE 'sources/"+source+"%';")
		if cursor.fetchone()[0] > 0:
			continue
		print("Ingesting new source: ", source)
		# ingest new sources
		if source.endswith(".txt"):
			# load txt data
			loader = TextLoader("sources/"+source)
		if source.endswith(".rtdocs"):
			# Load ReadTheDocs data
			loader = MyReadTheDocsLoader("sources/"+source, features='html.parser', encoding='utf-8', errors='ignore')
		documents = loader.load()
		# get all sources already in db
		cursor.execute("select distinct(cmetadata->>'source') from public.langchain_pg_embedding;")
		already_ingested = cursor.fetchall()
		# filter out already ingested sources
		documents = [doc for doc in documents if doc.metadata["source"] not in already_ingested]
		# Add file permissions to metadata
		for doc in documents:
			doc.metadata["owner"] = os.stat(doc.metadata["source"]).st_uid
			doc.metadata["group"] = os.stat(doc.metadata["source"]).st_gid
			doc.metadata["permissions"] = oct(os.stat(doc.metadata["source"]).st_mode)[-3:]
			
		text_splitter = TokenTextSplitter(chunk_size=500, chunk_overlap=100)
		texts = text_splitter.split_documents(documents)
		vectordb.add_documents(texts)

def data_ingest_from_ddg(question: str, vectordb: VectorStore, connection: psycopg.connection, cursor: psycopg.cursor):
	# condense the question into a duckduckgo query
	# ask ddg
	# check if answer is already in db
	# if not, add it
	pass

if __name__ == "__main__":
	# initialize vector db
	(vectordb, connection, cursor) = initdb()
	# ingest new data
	data_ingest(vectordb, connection, cursor)

	# chat with the user
	from langchain.chains.llm import LLMChain
	from langchain.callbacks.base import CallbackManager
	from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
	from langchain.chains.conversational_retrieval.prompts import CONDENSE_QUESTION_PROMPT, QA_PROMPT
	from langchain.chains.question_answering import load_qa_chain

	# Construct a ConversationalRetrievalChain with a streaming llm for combine docs
	# and a separate, non-streaming llm for question generation
	llm = OpenAI(temperature=0)
	streaming_llm = OpenAI(streaming=True,
			callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
			verbose=True,
			temperature=0
			)
	question_generator = LLMChain(llm=llm, prompt=CONDENSE_QUESTION_PROMPT)
	doc_chain = load_qa_chain(streaming_llm, chain_type="stuff", prompt=QA_PROMPT)

	qa = ConversationalRetrievalChain(
    	retriever=vectordb.as_retriever(),
		combine_docs_chain=doc_chain,
		question_generator=question_generator,
		return_source_documents=True
		)

	chat_history = []
	query = input("Ciao, sono il tuo assistente Nethesis. Sono qui per rispondere alle tue domande, prova a chiedermi qualcosa\n")
	result = qa({"question": query, "chat_history": chat_history})
	print("\n")

	while True:
		sources = []
		for doc in result["source_documents"]:
			sources.append(doc.metadata["source"])
			#print("Fonte: "+doc.metadata["source"])
			#print("Proprietario: "+str(doc.metadata["owner"]))
			#print("Gruppo: "+str(doc.metadata["group"]))
			#print("Permessi: "+str(doc.metadata["permissions"]))
		sources = list(set(sources))
		[print("Fonte: "+source) for source in sources]
		
		print("-"*80)
		
		chat_history = [(query, result["answer"])]
		query = input("\n")
		result = qa({"question": query, "chat_history": chat_history})
		print("\n")
	
