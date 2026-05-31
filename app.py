import streamlit as st
from pypdf import PdfReader
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from docx import Document
from io import BytesIO
import os
import faiss

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

# ---------- EXTRAER TEXTO PDF ----------
def extraer_texto_pdf(uploaded_file):

    reader = PdfReader(uploaded_file)

    texto = ""

    for page in reader.pages:

        contenido = page.extract_text()

        if contenido:

            texto += contenido

    return texto


# ---------- RESUMIR TEXTO LARGO ----------
def resumir_texto_largo(texto):

    texto = texto[:12000]

    prompt = f"""
    Resume el siguiente documento de forma clara,
    profesional y estructurada:

    {texto}
    """

    return ask_ai(prompt)

def resumir_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)

    texto = ""

    for page in reader.pages:
        contenido = page.extract_text()

        if contenido:
            texto += contenido

    st.session_state.pdf_text = texto

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

# ---------- PREGUNTAR SOBRE PDF ----------
def preguntar_pdf(texto_pdf, pregunta):

    chunks = dividir_texto(texto_pdf)

    contexto = buscar_chunks_relevantes(
    st.session_state.index,
    st.session_state.chunks,
    pregunta
)

    prompt = f"""
    Usa el siguiente contexto del documento para responder.

    Contexto:
    {contexto}

    Pregunta:
    {pregunta}

    Responde de forma clara y profesional.
    """

    return ask_ai(prompt)

# ---------- CREAR EMBEDDINGS ----------
def crear_embedding(texto):

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texto
    )

    return response.data[0].embedding
    
# ---------- CREAR ÍNDICE VECTORIAL ----------
def crear_indice_faiss(chunks):

    embeddings = []

    for chunk in chunks:

        embedding = crear_embedding(
            chunk
        )

        embeddings.append(embedding)

    embeddings_array = np.array(
        embeddings
    ).astype("float32")

    dimension = embeddings_array.shape[1]

    index = faiss.IndexFlatL2(
        dimension
    )

    index.add(embeddings_array)

    return index, chunks


# ---------- DIVIDIR TEXTO EN CHUNKS ----------
def dividir_texto(texto, tamaño=1000):

    chunks = []

    for i in range(0, len(texto), tamaño):

        chunk = texto[i:i+tamaño]

        chunks.append(chunk)

    return chunks
 # ---------- BUSCAR CHUNKS RELEVANTES ----------
def buscar_chunks_relevantes(
    index,
    chunks,
    pregunta
):

    pregunta_embedding = np.array(
        [crear_embedding(pregunta)]
    ).astype("float32")

    k = 3

    distancias, indices = index.search(
        pregunta_embedding,
        k
    )

    resultados = []

    for i in indices[0]:

        resultados.append(
            chunks[i]
        )

    return "\n\n".join(resultados)

# ---------- UI ----------

# ---------- MEMORIA CHAT ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "qa_history" not in st.session_state:
    st.session_state.qa_history = []

st.write("🔥 AIR M2 TEST 🔥")
st.write("Sube un PDF y obtén un resumen inteligente.")

# ---------- MOSTRAR CHAT ----------
for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

uploaded_files = st.file_uploader(
    "📄 Arrastra tus PDFs aquí",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:

    nombres = [
    archivo.name
    for archivo in uploaded_files
    ]

    st.success(
        f"Archivos cargados: {', '.join(nombres)}"
    )

    if st.button("✨ Generar resumen"):

        with st.spinner("Procesando documento..."):

            texto_completo = ""

            for uploaded_file in uploaded_files:

                texto_pdf = extraer_texto_pdf(
                    uploaded_file
                )

                texto_completo += texto_pdf + "\n\n"

            resumen = resumir_texto_largo(
                texto_completo
            )

            st.session_state.pdf_text = texto_completo

            chunks = dividir_texto(
                texto_completo
            )

            index, chunks = crear_indice_faiss(
                chunks
            )

            st.session_state.index = index
            st.session_state.chunks = chunks

            st.session_state.resumen = resumen

            st.session_state.messages.append(
                {
                    "role": "user",
                    "content": (
                        f"Subí archivos: "
                        f"{', '.join(nombres)}"
                    )
                }
            )

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": resumen
                }
            )

if "resumen" in st.session_state:

    st.subheader("🧠 Resumen generado")

    st.write(st.session_state.resumen)

    docx_file = crear_docx(
        st.session_state.resumen
    )

    st.download_button(
        label="📥 Descargar resumen en Word",
        data=docx_file,
        file_name="resumen.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )

    # ---------- PREGUNTAS PDF ----------
    st.subheader("❓ Haz preguntas sobre el PDF")

    pregunta = st.text_input(
        "Escribe tu pregunta:"
    )

    if pregunta:

        with st.spinner("Pensando..."):

            respuesta = preguntar_pdf(
                st.session_state.pdf_text,
                pregunta
            )

        st.session_state.qa_history.append(
            {
                "pregunta": pregunta,
                "respuesta": respuesta
            }
        )

    # ---------- HISTORIAL Q&A ----------
    for item in st.session_state.qa_history:

        with st.chat_message("user"):
            st.markdown(item["pregunta"])

        with st.chat_message("assistant"):
            st.markdown(item["respuesta"])

