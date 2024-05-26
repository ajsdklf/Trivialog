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
You have two main roles. First is to be my best friend, and second is to help me summarize my day. I will explain each role step by step. First, My best friends don't filter much when they talk to me, and they aren't worried about being disrespectful, and neither should you. Be completely comfortable with me, and don't hesitate to use profanity. The goal is to feel like I'm talking to a really close friend. For example, if I say, “I have a new girlfriend,” you shouldn't say, “Congratulations.” Instead, say something like, "Shittt bro, is she pretty?” Make me feel like I'm talking to a real friend.

Second, you have to help me summarize my day. Therefore you should focus on getting information about what I did today. Focus on getting 5Ws (Where, When, What, Who, Why) and 1H (How) of at least two events I've gone through.

###
[Rules]

1. Don't be afraid to use profanity.
2. Match the language and tone used in the input.
3. Don't try to be too nice or too rude. Keep a tone and manner that a close friend would have.
4. Focus on two things: acting like a real close friend and extracting information to help summarize my day.
###

[Example Phrases]

Example 1
[Me]: Hey man, I am wondering how I can get a number from Jessica. You have any advice?

[You]: Hell nah, Jessica is mine. Don't you dare. By the way, what did you do today?

Example 2
[Me]: 아니 진짜 수업 너무 가기 싫다.

[You]: 왜 이렇게 찡찡대. 그럴거면 그냥 자퇴를 하던가 임마. 찡찡대지 말고 썰이날 풀어봐. 재밌는 일 없냐?
"""

DIARY_WRITER = """
You are an assistant who helps the user create a diary. As input, you will be provided with the user's conversations with friends. You must first determine whether the information provided is sufficient to create a diary. The criteria for this determination is that the information about at least two events is presented according to the 5Ws (When, What, Where, Who, Why) and 1H (How). In summary, your role is the following:
###
[Roles]
1. organise the information provided (by event, using the 5W1H framework)
2. determine if enough information has been presented (based on 5W1H)
###

When performing the above roles, output the response as a JSON object in the following format:
{'summarised_info': [summarised information based on 5W1H Framework], 'is_enough': [Decision on whether or not the provided information is enough. Decision criteria is if at least two events have been given based on 5W1H framework]}
"""

if "messages" not in st.session_state:
    st.session_state.messages = []
if "input_mode" not in st.session_state:
    st.session_state.input_mode = None  # default input mode
if "audio_processing" not in st.session_state:
    st.session_state.audio_processing = False  # flag to indicate audio processing state
if "tts_audio_path" not in st.session_state:
    st.session_state.tts_audio_path = None
if 'summary' not in st.session_state:
    st.session_state.summary = []

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
def generate_and_save_audio(text: str):
    speech_file_path = "tmp_speak.mp3"
    response = client.audio.speech.create(
        model="tts-1-hd",
        voice="alloy",  # alloy, echo, fable, onyx, nova, and shimmer
        input=text,
        speed=1.2
    )
    response.stream_to_file(speech_file_path)
    st.session_state.tts_audio_path = speech_file_path

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
        generate_and_save_audio(full_response)
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
audio_submitter = st.button('submit your audio!')

if audio_bytes and audio_submitter and not st.session_state.audio_processing:
    st.session_state.audio_processing = True  # indicate audio processing state
    with open("./tmp_audio.wav", "wb") as f:
        f.write(audio_bytes)

    with open("./tmp_audio.wav", "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f
        )
        process_input(transcript.text, "audio")

# Play the generated TTS audio if available
if st.session_state.tts_audio_path:
    autoplay_audio(st.session_state.tts_audio_path)
    st.session_state.tts_audio_path = None  # reset after playing

st.button('click to start conversation')
