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
if "input_mode" not in st.session_state:
    st.session_state.input_mode = None  # default input mode
if "audio_processing" not in st.session_state:
    st.session_state.audio_processing = False  # flag to indicate audio processing state

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

# Generate TTS and play the audio
def generate_and_play_audio(text: str):
    speech_file_path = "tmp_speak.mp3"
    response = client.audio.speech.create(
        model="tts-1-hd",
        voice="alloy",  # alloy, echo, fable, onyx, nova, and shimmer
        input=text,
        speed=1.2
    )
    response.stream_to_file(speech_file_path)
    autoplay_audio(speech_file_path)

# Process input and generate response
def process_input(user_input: str, mode: str):
    st.session_state.input_mode = mode
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
                {'role': 'assistant', 'content': '[Friend mode activated]'},
                * [ {"role": m["role"], "content": m["content"]} for m in st.session_state.messages ]
            ],
            stream=True,
        ):
            full_response += (response.choices[0].delta.content or "")
            message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)
        generate_and_play_audio(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.session_state.input_mode = None  # reset input mode
    st.session_state.audio_processing = False  # reset audio processing flag

# View
st.markdown(
    """
    <style>
    .title {
        font-size: 2.5em;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 20px;
    }
    .chat-container {
        max-height: 60vh;
        overflow-y: auto;
        margin-bottom: 20px;
        padding: 15px;
        background: #E3F2FD;
        border-radius: 10px;
        border: 1px solid #90CAF9;
    }
    .user-message {
        color: #1565C0;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .assistant-message {
        color: #0D47A1;
        margin-bottom: 10px;
    }
    .fixed-footer {
        position: fixed;
        bottom: 0;
        width: 100%;
        background: #BBDEFB;
        padding: 10px;
        border-top: 1px solid #90CAF9;
    }
    .audio-recorder {
        display: flex;
        justify-content: center;
    }
    .stButton>button {
        background-color: #1E88E5;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        cursor: pointer;
    }
    .stButton>button:hover {
        background-color: #1565C0;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<div class="title">내 친구 AI</div>', unsafe_allow_html=True)

con1 = st.container()

with con1:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for message in st.session_state.messages:
        role = "user-message" if message["role"] == "user" else "assistant-message"
        st.markdown(f'<div class="{role}">{message["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Audio recorder at the bottom
st.markdown('<div class="fixed-footer">', unsafe_allow_html=True)
audio_bytes = audio_recorder("talk", pause_threshold=1.0)
st.markdown('</div>', unsafe_allow_html=True)

if audio_bytes and not st.session_state.audio_processing:
    st.session_state.audio_processing = True  # indicate audio processing state
    with open("./tmp_audio.wav", "wb") as f:
        f.write(audio_bytes)

    with open("./tmp_audio.wav", "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
        process_input(transcript.text, "audio")

# Add input box at the bottom
st.button('click to start conversation')
# with st.form(key='my_form', clear_on_submit=True):
#     user_input = st.text_input("Type your message here:")
#     submit_button = st.form_submit_button(label='Send')

#     if submit_button and user_input and not st.session_state.audio_processing:
#         process_input(user_input, "text")
