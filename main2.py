import base64
import streamlit as st
from openai import OpenAI
from audio_recorder_streamlit import audio_recorder
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

def autoplay_audio(file_path: str):
    with open(file_path, "rb") as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio controls autoplay="true">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(
            md,
            unsafe_allow_html=True,
        )

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Title and layout
st.title("프리 토킹 서비스")

# Container for messages
con1 = st.container()
# Container for audio recorder
con2 = st.container()

user_input = ""

with con2:
    st.markdown('🗣️ Talk with your friend.')
    audio_bytes = audio_recorder("Talk", pause_threshold=1.0)
    if audio_bytes:
        with open("./tmp_audio.wav", "wb") as f:
            f.write(audio_bytes)
        
        st.audio(audio_bytes, format="audio/wav")
        
        try:
            with open("./tmp_audio.wav", "rb") as f: 
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f
                )
                user_input = transcript.text
        except Exception as e:
            st.error(f"Error in transcription: {e}")

with con1:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
