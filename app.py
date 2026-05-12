import streamlit as st

st.set_page_config(page_title="AI Office Assistant", page_icon="🤖")

st.title("🤖 AI Office Assistant")
st.write("Tu asistente inteligente para automatización y documentos.")

mensaje = st.text_input("Escribe algo:")

if mensaje:
    st.success(f"Tu escribiste: {mensaje}")