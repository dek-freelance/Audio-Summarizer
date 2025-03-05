import streamlit as st
import os
from groq import Groq
import tempfile
from moviepy import VideoFileClip
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.colors import black
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import textwrap
import ffmpeg
import subprocess

load_dotenv()
client = Groq(api_key=os.getenv("groq_api_key"))

# Language options
languages = {"English": "en", "Hindi": "hi", "Marathi": "mr", "Telugu": "te", "Hinglish": "hi"}

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
        audio_path = temp_audio_file.name
        try:
            subprocess.run(
                ["ffmpeg", "-i", video_file, "-vn", "-acodec", "mp3", audio_path, "-y"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return audio_path
        except subprocess.CalledProcessError as e:
            st.error(f"Error extracting audio: {e.stderr.decode()}")
            return None

def translate_text(text, target_language):
    if target_language == "en":
        return text
    return GoogleTranslator(source="auto", target=target_language).translate(text)

def generate_pdf(content, language):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        pdf_path = temp_pdf.name

    # Choose the correct font based on the language
    font_map = {
        "English": ("NotoSans", "NotoSans-Regular.ttf"),
        "Hindi": ("NotoSansDevanagari", "NotoSansDevanagari-Regular.ttf"),
        "Marathi": ("NotoSansDevanagari", "NotoSansDevanagari-Regular.ttf"),
        "Telugu": ("NotoSansTelugu", "NotoSansTelugu-Regular.ttf"),
        "Hinglish": ("NotoSans", "NotoSansDevanagari-Regular.ttf"),
    }

    font_name, font_path = font_map.get(language, ("NotoSans", "NotoSans-Regular.ttf"))
    pdfmetrics.registerFont(TTFont(font_name, font_path))

    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Function to draw border
    def draw_border():
        border_thickness = 8
        margin = 20
        c.setStrokeColor(black)
        c.setLineWidth(border_thickness)
        c.rect(margin, margin, width - 2 * margin, height - 2 * margin)

    # Function to add title
    def add_title():
        c.setFont(font_name, 18)
        title = "BhashaBridge for Realtors"
        c.setFillColor("blue")
        text_width = c.stringWidth(title, font_name, 18)
        c.drawString((width - text_width) / 2, height - 50, title)

    draw_border()
    add_title()
    c.setFillColor("black")
    c.setFont(font_name, 14)
    c.drawString(100, height - 70, f"Transcription Report ({language})")

    # Handling multilingual text
    c.setFont(font_name, 12)
    margin = 50
    y_position = height - 100
    line_height = 16

    wrapped_text = []
    for paragraph in content.split("\n"):
        wrapped_text.extend(textwrap.wrap(paragraph, width=80))
        wrapped_text.append("")  # Add space between paragraphs

    for line in wrapped_text:
        if y_position < 50:
            c.showPage()
            draw_border()
            add_title()
            c.setFont(font_name, 12)
            y_position = height - 80
        c.drawString(margin, y_position, line)
        y_position -= line_height

    c.save()
    return pdf_path


st.title("🎙️ Meeting/Podcast Summarizer")
selected_language = st.selectbox("Choose Language", options=list(languages.keys()))
uploaded_file = st.file_uploader("Choose an audio/video file", type=["wav", "mp3", "mp4", "webm"])

if uploaded_file is not None:
    file_bytes = uploaded_file.read()
    if uploaded_file.type.startswith("audio"):
        st.audio(file_bytes)
    elif uploaded_file.type.startswith("video"):
        st.audio(file_bytes)
    
    if st.button("🎬 Transcribe"):
        with st.spinner("Transcribing..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix="." + uploaded_file.name.split(".")[-1]) as temp_file:
                temp_file.write(file_bytes)
                temp_file_path = temp_file.name
            
            if uploaded_file.type.startswith("video"):
                audio_file_path = extract_audio_from_video(temp_file_path)
                os.unlink(temp_file_path)
                temp_file_path = audio_file_path
            
            transcription = transcribe_audio(temp_file_path)
            translated_transcription = translate_text(transcription, languages[selected_language])
            st.subheader("📝 Transcription:")
            st.text_area("", value=translated_transcription, height=300, key="transcription_output")
            st.session_state.transcription = translated_transcription
            os.unlink(temp_file_path)

if st.button("📝 Summarize") and "transcription" in st.session_state:
    with st.spinner("Summarizing..."):
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes text."},
                {"role": "user", "content": f"Please summarize:\n{st.session_state.transcription}"},
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.5,
        )
        summary = response.choices[0].message.content
        translated_summary = translate_text(summary, languages[selected_language])
        st.subheader("📋 Summary:")
        st.markdown(translated_summary)
        st.session_state.summary = translated_summary

if st.button("📄 Generate PDF") and "transcription" in st.session_state:
    with st.spinner("Generating PDF..."):
        pdf_path = generate_pdf(st.session_state.transcription, selected_language)
        with open(pdf_path, "rb") as pdf_file:
            st.download_button("📄 Download PDF", pdf_file, file_name="transcription.pdf", mime="application/pdf")
        os.unlink(pdf_path)
