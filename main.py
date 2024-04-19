from openai import OpenAI
import streamlit as st 
import numpy as np 
from dotenv import load_dotenv
import os 

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

response = client.chat.completions.create(
    model='gpt-3.5-turbo-0125',
    messages=[
        {'role': 'system', 'content': 'You are an assistant'}
    ]
)

print(response)