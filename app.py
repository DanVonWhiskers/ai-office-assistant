import streamlit as st
from pypdf import PdfReader
from openai import OpenAI
from dotenv import load_dotenv
from docx import Document
from io import BytesIO
import os

# ---------- CONFIG ----------
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(
    page_title="AI Office Assistant",
    page_icon="🤖",
    layout="centered"
)

# ---------- FUNCIONES ----------
def ask_ai(prompt):
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "Eres un asistente profesional experto en resumir documentos."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content


# ---------- RESUMIR PDF ----------
def resumir_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)

    texto = ""

    for page in reader.pages:
        contenido = page.extract_text()

        if contenido:
            texto += contenido

    texto = texto[:12000]

    prompt = f"""
    Resume el siguiente documento de forma clara, profesional y estructurada:

    {texto}
    """

    return ask_ai(prompt)


# ---------- CREAR DOCX ----------
def crear_docx(resumen):

    doc = Document()

    doc.add_heading("Resumen generado por AI Office Assistant", level=1)

    doc.add_paragraph(resumen)

    buffer = BytesIO()

    doc.save(buffer)

    buffer.seek(0)

    return buffer

# ---------- UI ----------
st.title("🤖 AI Office Assistant")
st.write("Sube un PDF y obtén un resumen inteligente.")

uploaded_file = st.file_uploader(
    "📄 Arrastra tu PDF aquí",
    type=["pdf"]
)

if uploaded_file is not None:

    st.success(f"Archivo cargado: {uploaded_file.name}")

    if st.button("✨ Generar resumen"):

        with st.spinner("Procesando documento..."):

            resumen = resumir_pdf(uploaded_file)

        
        st.subheader("🧠 Resumen generado")

        st.write(resumen)

        docx_file = crear_docx(resumen)

        st.download_button(
            label="📥 Descargar resumen en Word",
            data=docx_file,
            file_name="resumen.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)