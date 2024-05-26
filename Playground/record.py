from openai import OpenAI
import base64
from openai import OpenAI 
from audio_recorder_streamlit import audio_recorder 
from dotenv import load_dotenv 
import os 
import streamlit as st

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

if 'messages' not in st.session_state:
    st.session_state.messages = []

user_input = ''

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

st.title('Talk with friend')

con1 = st.container()
con2 = st.container()

with con2:
    audio_bytes = audio_recorder('talk', pause_threshold=1.0)
    try:
        if audio_bytes:
            with open("./tmp_audio.wav", 'wb') as f:
                f.write(audio_bytes)
            with open('.tmp_audio.wav', 'rb') as f:
                transcript = client.audio.transcriptions.create(
                    model='whisper-1',
                    file=f
                )
                user_input = transcript.text 
    except Exception as e:
        pass

with con1:
    for message in st.session_state.messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])
    
    if user_input:
        st.session_state.messages.append({'role': 'user', 'content': user_input})
        
        with st.chat_message('user'):
            st.markdown(user_input)
        
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                ],
                stream=True,
            ):
                full_response += (response.choices[0].delta.content or "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

            speech_file_path = "tmp_speak.mp3"
            response = client.audio.speech.create(
            model="tts-1",
            voice="alloy", # alloy, echo, fable, onyx, nova, and shimmer
            input=full_response
            )
            response.stream_to_file(speech_file_path)

            autoplay_audio(speech_file_path)

        st.session_state.messages.append({"role": "assistant", "content": full_response})