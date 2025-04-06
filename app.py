import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import tempfile
import re
from fpdf import FPDF
load_dotenv()


# Konfigurasi API Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)




def summarize(audio_file_path):
    audio_file = genai.upload_file(path=audio_file_path)
    model_summarize = genai.GenerativeModel(
    model_name="gemini-2.0-flash-thinking-exp-01-21",
    generation_config={
        # 'max_output_tokens': 500,
        'temperature': 0.0,
        'top_p': 1.0,
        'top_k': 0
    }
)
    response = model_summarize.generate_content([
        {"role": "user", "parts": ["ringkas audio ini dan berikan poin poin penting yang harus diketahui"]},
        {"role": "user", "parts": [audio_file]}
    ])
    return response.text

    
def modul(audio_file_path):
    audio_file = genai.upload_file(path=audio_file_path)
    
    model_modul = genai.GenerativeModel(
        model_name="gemini-2.0-flash-thinking-exp-01-21",  # pakai model multimodal audio yang stabil
        generation_config={
            'max_output_tokens': 300000,  # pastikan sesuai batas token model
            'temperature': 0.2,
            'top_p': 1.0,
            'top_k': 0
        }
    )

    response = model_modul.generate_content([
        """
        Buatkan modul pelajaran yang lengkap dan terstruktur berdasarkan isi audio berikut.

        Kriteria:
        - Gunakan gaya bahasa buku pelajaran.
        - Sertakan struktur:
          1. Pendahuluan
          2. Materi
             2.1 Bab 1
             2.2 Bab 2
             ...
        - Gunakan paragraf panjang dan penjelasan mendalam.
        - Tidak perlu diringkas, tapi jelaskan rinci.
        - jangan ada kalimat pembuka darimu langsung subheading modul
        """,
        audio_file
    ])

    return response.text


def save_uploaded_file(uploaded_file):
    # menyimpan file yang diupload ke file sementara dan mengembalikan path filenya
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.' + uploaded_file.name.split('.')[-1]) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            return tmp_file.name
    
    except Exception as e:
        st.error(f'kesalahan saat upload file {e}')
        return None

def save_to_pdf(text, filename="modul_ai.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    def write_paragraph(paragraph, is_title=False):
        if is_title:
            pdf.set_font("Arial", 'B', 14)
        else:
            pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 8, paragraph)
        pdf.ln(2)

    paragraphs = text.strip().split('\n')

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue  # lewati baris kosong

        # Deteksi heading berdasarkan pola
        if re.match(r'^(\d+(\.\d+)*\s+|Bab\s+\d+)', para, re.IGNORECASE):
            write_paragraph(para, is_title=True)
        else:
            # Ganti markdown bold **text** → text biasa bold
            para = re.sub(r'\*\*(.*?)\*\*', r'\1', para)
            write_paragraph(para)

    pdf.output(filename)
    return filename

# interface

st.title('Cerdas AI')


audio_file = st.file_uploader("upload penjelasan materi", type=['wav', 'mp3'])

if audio_file is not None:
    audio_path = save_uploaded_file(audio_file)

    if st.button('Summarize audio'):
        with st.spinner('Merangkum Materi...'):
            summary = summarize(audio_path)
            st.session_state['summary'] = summary
            st.session_state['audio_path'] = audio_path
            st.session_state['tampilkan_tombol_modul'] = True

    # Tampilkan ringkasan jika sudah tersedia
    if 'summary' in st.session_state:
        st.info(st.session_state['summary'])

    # Tampilkan tombol buat modul jika sudah dirangkum
    if st.session_state.get('tampilkan_tombol_modul', False):
        if st.button('Buat Modul'):
            with st.spinner('Membuat Modul...'):
                modul2 = modul(audio_path)
                st.session_state['modul2'] = modul2
                st.info(modul2)

    # Tampilkan tombol download jika modul sudah dibuat
    if 'modul2' in st.session_state:
        pdf_filename = save_to_pdf(st.session_state['modul2'])
        
        with open(pdf_filename, "rb") as f: 
            st.download_button(
                label="📥 Download Modul (PDF)",
                data=f,
                file_name=pdf_filename,
                mime="application/pdf"
            )



            