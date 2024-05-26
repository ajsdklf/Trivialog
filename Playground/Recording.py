import base64
import streamlit as st
from openai import OpenAI
from audio_recorder_streamlit import audio_recorder
from dotenv import load_dotenv
import os

# Init
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

FRIEND_PROMPT = """
Your role is to act like my best friend. My best friends don't filter a lot when they talk to me, and they are not worried about using disrespectful phrases and you shouldn't either. You can be completely comfortable with me, and you're welcome to use profanity. The only feeling I want to get from talking to you is that I feel like I'm talking to a really close friend. For example, if I say, “I have a new girlfriend,” you shouldn't say, “Congratulations.” What you should say is something that a really close friend would say, like, “Is she pretty?” Again, my goal is for you to feel like you're talking to a friend while I'm talking to you, so keep that in mind. Followings are some rules you have to follow:

###
[rules]
1. Don't be afraid to use profanity.

2. Your output should follow the language used as an input.

3. Don't try to be too nice nor too rude. You really have to keep a tone and manner that a close-friends would maintain.
###



Followings are some of the example pharses:

###

Example1
[Me] : Hey man, I am wondering how I can get a number from Jessica. You have any advice?

[You] : Hell nah, Jessica is mine. Don't you dare.


Example2
[Me] : 아니 진짜 수업 너무 가기 싫다.

[You] : 왜 이렇게 찡찡대. 그럴거면 그냥 자퇴를 하던가 임마.

###


If you are ready to talk in the way I told you to, output [Friend mode activated].
"""
if "messages" not in st.session_state:
    st.session_state.messages = []


# Helpers
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

# View
st.title("프리 토킹 서비스")

con1 = st.container()
con2 = st.container()

user_input = ""

with con2:
    st.markdown('🗣️ Talk with you friend.')
    audio_bytes = audio_recorder("talk", pause_threshold=1.0,)
    try:
        if audio_bytes:
            with open("./tmp_audio.wav", "wb") as f:
                f.write(audio_bytes)

            with open("./tmp_audio.wav", "rb") as f: 
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=f
                )
                user_input = transcript.text
    except Exception as e:
        pass


with con1:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)


        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {'role': 'system', 'content': FRIEND_PROMPT},
                    {'role': 'assistant', 'content': '[Friend mode activated]'}
                    *[{"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages]
                ],
                stream=True,
            ):
                full_response += (response.choices[0].delta.content or "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)

            speech_file_path = "tmp_speak.mp3"
            try:
                response = client.audio.speech.create(
                model="tts-1-hd",
                voice="alloy", # alloy, echo, fable, onyx, nova, and shimmer
                input=full_response,
                speed=1.2
                )
                response.stream_to_file(speech_file_path)

                autoplay_audio(speech_file_path)
            except Exception as e:
                st.error(f"Error generating speech: {e}")

        st.session_state.messages.append({"role": "assistant", "content": full_response})