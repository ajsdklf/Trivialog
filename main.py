from openai import OpenAI
import streamlit as st 
import numpy as np 
from dotenv import load_dotenv
import os 

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

st.header("기록 MVP")

