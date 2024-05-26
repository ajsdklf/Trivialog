from openai import OpenAI
import streamlit as st 
import numpy as np 
from dotenv import load_dotenv
import os 
import sounddevice as sd
from scipy.io.wavfile import write


load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

def record_audio(duration=5, fs=44100):
    """Record audio for a given duration and sample rate."""
    st.write("Recording...")
    myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=2)
    sd.wait()  # Wait until recording is finished
    st.write("Recording stopped.")
    return myrecording

def save_audio(recording, fs=44100, filename='output.wav'):
    """Save the recorded audio to a WAV file."""
    write(filename, fs, recording)  # Save as WAV file

# Streamlit interface
st.title("Audio Recorder in Streamlit")
duration = st.slider("Select the duration of the recording in seconds:", min_value=1, max_value=10, value=5)
fs = 44100  # Sample rate

if st.button('Record'):
    recording = record_audio(duration, fs)
    save_path = 'temp_audio.wav'
    save_audio(recording, fs, save_path)
    st.audio(save_path)

# Cleanup (optional)
if os.path.exists('temp_audio.wav'):
    os.remove('temp_audio.wav')  # Remove temp file after the session (if needed)\
    

