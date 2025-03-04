import streamlit as st
import os
from groq import Groq
import tempfile
import wave
import io
from moviepy import VideoFileClip
from dotenv import load_dotenv
import pdfkit

load_dotenv()

client = Groq(api_key=os.getenv("groq_api_key"))

st.markdown(
    """
<style>
    /* Main background and text colors */
    body {
        color: #E0E0E0;
        background-color: #1E1E1E;
    }
    .stApp {
        background-color: #1E1E1E;
    }
/* Headings */
    h1, h2, h3 {
        color: #BB86FC;
    }
    /* Buttons */
    .stButton>button {
        color: #1E1E1E;
        background-color: #BB86FC;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #A66EFC;
    }
    /* File uploader */
    .stFileUploader {
        background-color: #2E2E2E;
        border: 1px solid #BB86FC;
        border-radius: 4px;
        padding: 1rem;
    }
    /* Audio player */
    .stAudio {
        background-color: #2E2E2E;
        border-radius: 4px;
        padding: 0.5rem;
    }
    /* Text areas (for transcription output) */
    .stTextArea textarea {
        background-color: #2E2E2E;
        color: #E0E0E0;
        border: 1px solid #BB86FC;
        border-radius: 4px;
    }
</style>
""",
    unsafe_allow_html=True,
)

def transcribe_audio(audio_file):
    with open(audio_file, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(os.path.basename(audio_file), file.read()),
            model="whisper-large-v3",
            response_format="json",
            language="en",
            temperature=0.0,
        )
    return transcription.text

def extract_audio_from_video(video_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio_file:
        with VideoFileClip(video_file) as video:
            video.audio.write_audiofile(temp_audio_file.name, codec="mp3")
        return temp_audio_file.name
    
st.title("🎙️ Meeting/Podcast Summarizer")

uploaded_file = st.file_uploader(
    "Choose an audio or video file", type=["wav", "mp3", "mp4"]
)
if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    if uploaded_file.type.startswith("audio"):
        st.audio(file_bytes)
    elif uploaded_file.type.startswith("video"):
        st.audio(file_bytes)

col1, col2, col3 = st.columns(3)

with col1:
    transcribe_button = st.button("🎬 Transcribe")
with col2:
    summarize_button = st.button("📝 Summarize")

with col3:
    pdf_button = st.button("PDF generate!")
if transcribe_button:
    with st.spinner("Transcribing..."):
        try:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix="." + uploaded_file.name.split(".")[-1]
            ) as temp_file:
                temp_file.write(file_bytes)
                temp_file_path = temp_file.name

            if uploaded_file.type.startswith("video"):
                audio_file_path = extract_audio_from_video(temp_file_path)
                os.unlink(temp_file_path)
                temp_file_path = audio_file_path

            transcription = transcribe_audio(temp_file_path)

            st.subheader("📝 Transcription:")
            x = st.text_area(
                "", value=transcription, height=300, max_chars=None, key="transcription_output"
            )

            st.session_state.transcription = transcription

            os.unlink(temp_file_path)
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
        finally:
            if "temp_file_path" in locals():
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            if "audio_file_path" in locals():
                try:
                    os.unlink(audio_file_path)
                except:
                    pass

if summarize_button:
    if "transcription" in st.session_state:
        with st.spinner("Summarizing..."):
            try:
                response = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that summarizes text."},
                        {
                            "role": "user",
                            "content": f"Please summarize the following transcription:\n\n{st.session_state.transcription}",
                        },
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.5,
                )

                summary = response.choices[0].message.content
                st.subheader("📋 Summary:")
                st.markdown(summary)
            except Exception as e:
                st.error(f"❌ An error occurred during summarization: {str(e)}")
    else:
        st.warning("Please transcribe the audio/video first.")


if pdf_button:
    if "transcription" in st.session_state and st.session_state.transcription.strip():
        pdf_filename = st.text_input("Enter PDF name", "transcription_report.pdf")
        transcription_text = st.session_state.transcription.replace("\n", "<br>")
        html_content = f"""
        <html>x 
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    color: #333;
                }}
                h1 {{
                    color: #BB86FC;
                }}
                p {{
                    line-height: 1.6;
                }}
            </style>
        </head>
        <body>
            <h1>Transcription Report</h1>
            <p>{transcription_text}</p>
        </body>
        </html>
        """

        with st.spinner("Generating PDF..."):
            pdf_path = "output.pdf"
            pdfkit.from_string(html_content, pdf_path)

            with open(pdf_path, "rb") as pdf_file:
                st.download_button(
                    "📄 Download Transcription PDF",
                    data=pdf_file,
                    file_name=pdf_filename,
                    mime="application/pdf"
                )
    else:
        st.warning("No transcription available. Please transcribe first.")