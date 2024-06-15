from openai import OpenAI
import anthropic 
import os 
from dotenv import load_dotenv 
import streamlit as st 
from langchain.document_loaders import JSONLoader
import json 
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

client_o = OpenAI(api_key=OPENAI_API_KEY)
client_a = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

store_path = './db/faiss_index'
embed_model = OpenAIEmbeddings(model='text-embedding-3-large')
vector_index = FAISS.load_local(store_path, embed_model, allow_dangerous_deserialization=True)

query = 'I need help with getting motivated.'
retriever = vector_index.as_retriever(
  search_kwargs={'k': 3}
)
retrieved_docs = retriever.invoke(query)
for doc in retrieved_docs:
  print(doc)
print('================================ \n')
ret1 = vector_index.similarity_search_with_score(query)
print(ret1)
print('================================ \n')
ret2 = vector_index.similarity_search(query)
print(ret2)
print('================================ \n')
ret3 = vector_index.similarity_search_with_relevance_scores(query)
print(ret3)
print('================================ \n')
ret4 = vector_index.similarity_search_with_score_by_vector(query)
print(ret4)