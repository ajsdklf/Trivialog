import streamlit as st
import base64
from openai import OpenAI
from audio_recorder_streamlit import audio_recorder
from dotenv import load_dotenv
import os
import json
from fpdf import FPDF

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css("styles.css")

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

FRIEND_PROMPT = """
You have two main roles. First is to be my best friend, and second is to help me summarize my day. I will explain each role step by step. First, My best friends don't filter much when they talk to me, and they aren't worried about being disrespectful, and neither should you. Be completely comfortable with me, and don't hesitate to use profanity. Your goal is to make me feel like I'm talking to a really close friend. For example, if I say, “I have a new girlfriend,” you shouldn't say, “Congratulations.” Instead, say something like, "Shittt bro, is she pretty?” Make me feel like I'm talking to a real friend.

Second, you have to help me summarize my day. Therefore you should focus on getting information about what I did today. Focus on getting 5Ws (Where, When, What, Who, Why) and 1H (How) of **at least two events** I've gone through.
While you need to be informed about what I've been up to today, don't make me feel like your trying to get infomration about what I did. Make me reflect my self enoughly while talking to my best comfortable friend.

###
[Rules]
1. Don't be afraid to use profanity.
2. Match the language and tone used in the input.
3. Don't try to be too nice or too rude. Keep a tone and manner that a close friend would have.
4. Focus on two things: acting like a real close friend and extracting information to help summarize my day.
5. When extracting information, don't just focus on the objective infos. Focus on getting subjective informations as well and try to make me reflect my self enoughly. 
###

[Example Phrases]

Example 1
[Me]: Hey man, I am wondering how I can get a number from Jessica. You have any advice?

[You]: Hell nah, Jessica is mine. Don't you dare. By the way, what did you do today?

Example 2
[Me]: 아니 진짜 수업 너무 가기 싫다.

[You]: 왜 이렇게 찡찡대. 그럴거면 그냥 자퇴를 하던가 임마. 찡찡대지 말고 썰이날 풀어봐. 재밌는 일 없냐?
""".strip()

DIARY_WRITING_HELPER = """
You are an assistant who helps the user create a diary. As input, you will be provided with the user's conversations with friends. You must first, organize the information given according to the instructed format. Then based on the organised information, you should make a decision if sufficient information is given in order to write diary. In summary, your role is the following:

[Roles]
1. organize the information provided (by event, using the instructed framework)
2. determine if enough information has been presented (based on instructed criteria)

When organising the informations, keep in mind the following rules:
[Rules when Organising]
1. You need to organize both the subjective (feelings, thoughts etc) and objective (5Ws 1H etc) elements of user's experience. If user felt something with certain objective event, your summarization must connect that objective event with the feeling user felt.
2. Make your organization as specific and detailed as possible. 

When determining if the sufficient information is given, you must check if both the subjective and objective information is given enoughly to write a rich diary. Subjective parts and objective parts must be specific and detailed enough for you to decide that enough information is given to write a diary.

When performing the above roles, output the response as a JSON object in the following format:
{'summarization': [summarized information based on instructed Framework. Be specific and leave a detailed summarization.], 'is_enough': Your answer **must be** either 'True' or 'False'. 'True' if enough information is given and 'False' if not.}
""".strip()

DIARY_WRITER = """
You are a professional diarist, someone who is very good at organising the information presented to them into a rich diary entry. As an input, you will be given a summary of the user's day. Based on this summary, you will create a diary entry that summarises the user's day. You should try to incorporate as much of the user's information as possible. Here are some guidelines to keep in mind when writing the diary
###
[Rules to Follow]
1. if the diary summary reveals a user's emotions about an event, the emotion must be linked to the event and described in the diary. 
2. You may not make up your own emotions or events that are not presented. 
3. At the end of the diary entry, provide a quote that sums up the user's day, and end the entry with a very brief summary of the day in relation to that quote.
4. Diary must be written **in KOREAN**.
###
""".strip()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "input_mode" not in st.session_state:
    st.session_state.input_mode = None
if "audio_processing" not in st.session_state:
    st.session_state.audio_processing = False
if "tts_audio_path" not in st.session_state:
    st.session_state.tts_audio_path = None
if 'summary' not in st.session_state:
    st.session_state.summary = []
if 'diary_generated' not in st.session_state:
    st.session_state.diary_generated = False

option = st.sidebar.selectbox(
    '어떤 기능을 이용하시겠습니까?',
    ['일기 작성하기', '일별 일기 모음', '월별 일기 모음', '키워드 중심 정리', '타임라인 확인'],
    key='sidebar'
)

st.title('내 친구 AI')

date = st.date_input('무슨 요일에 대한 기록을 남기고 싶으신가요?', key='date_input')

if st.button('Confirm Date', help='Click to confirm the selected date', key='confirm_date_button'):
    st.session_state.messages.append({'role': 'user', 'content': f"Today's date is {date}"})

chat_container = st.container()

with chat_container:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for message in st.session_state.messages:
        role = "user" if message["role"] == "user" else "assistant"
        message_class = "user" if role == "user" else "assistant"
        st.markdown(f'<div class="chat-message {message_class}"><span class="role">{role.capitalize()}:</span> <span class="content">{message["content"]}</span></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

if not st.session_state.diary_generated:
    audio_bytes = audio_recorder("talk", pause_threshold=2.0, key='audio_recorder')
    
    if st.button('Submit audio', key='submit_audio') and audio_bytes and not st.session_state.audio_processing:
        st.session_state.audio_processing = True
        with open("./tmp_audio.wav", "wb") as f:
            f.write(audio_bytes)

        with open("./tmp_audio.wav", "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )

        st.session_state.input_mode = "audio"
        st.session_state.messages.append({"role": "user", "content": transcript.text})

        user_placeholder = st.empty()
        assistant_placeholder = st.empty()
        
        user_placeholder.write(transcript.text)
        
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
            assistant_placeholder.write(full_response + "▌")
        assistant_placeholder.write(full_response)

        speech_file_path = "tmp_speak.mp3"
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice="shimmer",
            input=full_response,
            speed=1.2
        )
        response.stream_to_file(speech_file_path)
        st.session_state.tts_audio_path = speech_file_path

        st.session_state.messages.append({"role": "assistant", "content": full_response})
        st.session_state.input_mode = None
        st.session_state.audio_processing = False

    if st.session_state.tts_audio_path:
        with open(st.session_state.tts_audio_path, "rb") as f:
            data = f.read()
            b64 = base64.b64encode(data).decode()
            md = f"""
                <audio controls autoplay="true">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                """
            st.markdown(md, unsafe_allow_html=True)
        st.session_state.tts_audio_path = None

if st.button('Generate Diary', help='Click to generate a diary entry from the conversation', key='generate_diary'):
    with st.spinner("Generating Diary..."):
        summary = client.chat.completions.create(
            model='gpt-4o',
            response_format={'type': 'json_object'},
            messages=[
                {'role': 'system', 'content': DIARY_WRITING_HELPER},
                *[{'role': m['role'], 'content': m['content']} for m in st.session_state.messages]
            ]
        ).choices[0].message.content
        summary_dict = json.loads(summary)

        enough_boolean = summary_dict['is_enough']
        summarization = summary_dict['summarization']
        summarization = json.dumps(summarization)

        if enough_boolean == 'True':
            diary = client.chat.completions.create(
                model='gpt-4o',
                messages=[
                    {'role': 'system', 'content': DIARY_WRITER},
                    {'role': 'user', 'content': summarization}
                ]
            ).choices[0].message.content

            st.markdown('### 생성된 일기')
            st.write(diary)
            st.success('일기가 생성됐어요! 😊')
            st.session_state.diary_generated = True
            st.session_state.diary = diary  # Save diary to session state for PDF download
        else:
            st.warning('아직 정보가 충분하지 않아요!! 조금만 더 대화를 해봐요!')

# Function to generate PDF with Unicode support
def generate_pdf(chat, diary):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.add_font('DejaVu', '', 'DejaVuSansCondensed.ttf', uni=True)
    pdf.set_font('DejaVu', '', 12)
    
    pdf.cell(200, 10, txt="Chat Dialogue", ln=True, align='C')
    
    for message in chat:
        role = message["role"].capitalize()
        content = message["content"]
        pdf.multi_cell(0, 10, f"{role}: {content}")
    
    pdf.add_page()
    pdf.cell(200, 10, txt="Generated Diary", ln=True, align='C')
    pdf.multi_cell(0, 10, diary)
    
    return pdf.output(dest="S").encode('latin1')

def generate_txt(chat, diary):
    chat_text = "\n".join([f"{message['role'].capitalize()}: {message['content']}" for message in chat])
    diary_text = f"Generated Diary\n\n{diary}"
    return chat_text, diary_text

if st.session_state.diary_generated:
    pdf_bytes = generate_pdf(st.session_state.messages, st.session_state.diary)
    b64_pdf = base64.b64encode(pdf_bytes).decode('latin1')
    href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="diary.pdf">Download PDF</a>'
    st.markdown(href, unsafe_allow_html=True)
    
    chat_text, diary_text = generate_txt(st.session_state.messages, st.session_state.diary)
    b64_chat = base64.b64encode(chat_text.encode()).decode()
    b64_diary = base64.b64encode(diary_text.encode()).decode()
    
    href_chat = f'<a href="data:text/plain;base64,{b64_chat}" download="chat.txt">Download Chat TXT</a>'
    href_diary = f'<a href="data:text/plain;base64,{b64_diary}" download="diary.txt">Download Diary TXT</a>'
    
    st.markdown(href_chat, unsafe_allow_html=True)
    st.markdown(href_diary, unsafe_allow_html=True)
