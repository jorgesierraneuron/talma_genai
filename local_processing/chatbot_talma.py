import streamlit as st
import requests

# Configurar la API URL en AWS
API_OPTIONS = {
    "Análisis de Causa (Filtrado)": "",
    "Análisis de Causa (Sin Filtro)": ""
}

st.markdown("<h1 style='text-align: center;'>🤖 Chatbot de Análisis de Causa</h1>", unsafe_allow_html=True)

api_choice = st.selectbox("Seleccione el tipo de análisis a generar:", list(API_OPTIONS.keys()))
API_URL = API_OPTIONS[api_choice]

if "messages" not in st.session_state:
    st.session_state["messages"] = []
    st.session_state["last_response"] = ""
    st.session_state["last_user_input"] = ""

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Escriba su consulta sobre análisis de causa...")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.session_state["last_user_input"] = user_input  # Guardar última entrada del usuario
    with st.chat_message("user"):
        st.markdown(user_input)

    payload = {"descripcion_hallazgo": user_input}

    with st.spinner("Generando análisis de causa..."):
        response = requests.post(API_URL, json=payload)
        
        try:
            response_text = response.text  # Capturar la respuesta como string
            print("Respuesta de la API:", response_text)  # Depuración
            
            # Intentar convertir a JSON si es posible
            try:
                response_data = response.json()
                cause_analysis = response_data.get("response", response_text)
            except ValueError:
                cause_analysis = response_text  # Si la conversión a JSON falla, usar la respuesta como string
        except Exception as e:
            cause_analysis = f"Error al procesar la respuesta de la API: {str(e)}"
        
        st.session_state["last_response"] = cause_analysis
        st.session_state["messages"].append({"role": "assistant", "content": cause_analysis})
        with st.chat_message("assistant"):
            st.markdown(cause_analysis)

# Permitir que el usuario ingrese feedback
feedback = st.text_area("Si la respuesta no es satisfactoria, ingrese su feedback aquí:")
submit_feedback = st.button("Aplicar Feedback")

if submit_feedback and feedback and st.session_state["last_response"]:
    st.session_state["messages"].append({"role": "user", "content": feedback})
    with st.chat_message("user"):
        st.markdown(feedback)
    
    feedback_payload = {
        "descripcion_hallazgo": st.session_state["last_user_input"],  # Asegurar que se usa la última consulta
        "feedback": feedback,
        "original_response": st.session_state["last_response"]
    }
    
    with st.spinner("Reevaluando análisis basado en feedback..."):
        feedback_response = requests.post(API_URL, json=feedback_payload)
        
        try:
            feedback_text = feedback_response.text  # Capturar la respuesta como string
            print("Respuesta de feedback API:", feedback_text)  # Depuración
            
            # Intentar convertir a JSON si es posible
            try:
                feedback_data = feedback_response.json()
                improved_analysis = feedback_data.get("response", feedback_text)
            except ValueError:
                improved_analysis = feedback_text  # Si la conversión a JSON falla, usar la respuesta como string
        except Exception as e:
            improved_analysis = f"Error al procesar la respuesta de la API: {str(e)}"
        
        st.session_state["last_response"] = improved_analysis
        st.session_state["messages"].append({"role": "assistant", "content": improved_analysis})
        with st.chat_message("assistant"):
            st.markdown(improved_analysis)

