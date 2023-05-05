
from langchain.llms import OpenAI
from langchain.callbacks.base import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.chains.llm import LLMChain
from langchain.chains.conversational_retrieval.prompts import CONDENSE_QUESTION_PROMPT, QA_PROMPT
from langchain.chains.question_answering import load_qa_chain
from langchain.chains import ConversationalRetrievalChain
from db import DB

llm = OpenAI(temperature=0)
streaming_llm = OpenAI(streaming=True,
	callback_manager=CallbackManager([StreamingStdOutCallbackHandler()]),
    verbose=True,
	temperature=0
)

question_generator = LLMChain(llm=llm, prompt=CONDENSE_QUESTION_PROMPT)
doc_chain = load_qa_chain(streaming_llm, chain_type="stuff", prompt=QA_PROMPT)

db = DB()
qa = ConversationalRetrievalChain(
    retriever=db.vectorstore.as_retriever(),
	combine_docs_chain=doc_chain,
	question_generator=question_generator,
	return_source_documents=True
)

chat_history = []
query = input("Hi! I'm your personal data manager. Ask me something about your data.\n")
result = qa({"question": query, "chat_history": chat_history})
print("\n")

while True:
	sources = []
	for doc in result["source_documents"]:
		sources.append(doc.metadata["source"])
		#print("Source: "+doc.metadata["source"])
		#print("Owner: "+str(doc.metadata["owner"]))
		#print("Grup: "+str(doc.metadata["group"]))
		#print("Permissions: "+str(doc.metadata["permissions"]))
	sources = list(set(sources))
	[print("Source: "+source) for source in sources]
		
	print("-"*80)
		
	chat_history = [(query, result["answer"])]
	query = input("\n")
	result = qa({"question": query, "chat_history": chat_history})
	print("\n")