import streamlit as st
import requests

API_URL = " "

st.markdown("<h1 style='text-align: center;'>🤖 Chatbot Talma Reportes De Quejas</h1>", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state["messages"] = []
    st.session_state["last_response"] = ""
    st.session_state["last_user_input"] = ""

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

user_input = st.chat_input("Escriba su consulta sobre análisis de causa...")

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    st.session_state["last_user_input"] = user_input  # Guardar última entrada del usuario
    with st.chat_message("user"):
        st.markdown(user_input, unsafe_allow_html=True)

    payload = {"descripcion_hallazgo": user_input}

    with st.spinner("Generando análisis de causa..."):
        response = requests.post(API_URL, json=payload)
        print("Código de estado:", response.status_code)  # Depuración
        response_text = response.text  # Capturar la respuesta como string
        print("Respuesta de la API:", response_text)  # Depuración
        
        if response.status_code == 200:
            try:
                response_data = response.json()  # Intentar convertir a JSON
                analysis = response_data.get("respuesta", response_text)  
            except (ValueError, AttributeError):
                analysis = response_text  # Si no es JSON, usar el string plano
        else:
            analysis = f"Error en la API (Código {response.status_code}): {response_text}"
        
        st.session_state["last_response"] = analysis
        st.session_state["messages"].append({"role": "assistant", "content": analysis})
        with st.chat_message("assistant"):
            st.markdown(analysis, unsafe_allow_html=True)

# Permitir que el usuario ingrese feedback y generar nuevas versiones iterativamente
feedback = st.text_area("Si la respuesta no es satisfactoria, ingrese su feedback aquí:")
submit_feedback = st.button("Aplicar Feedback")

if submit_feedback and feedback and st.session_state["last_response"]:
    st.session_state["messages"].append({"role": "user", "content": feedback})
    with st.chat_message("user"):
        st.markdown(feedback, unsafe_allow_html=True)
    
    feedback_payload = {
        "descripcion_hallazgo": st.session_state["last_user_input"],
        "feedback": feedback,
        "original_response": st.session_state["last_response"]
    }
    
    with st.spinner("Reevaluando análisis basado en feedback..."):
        feedback_response = requests.post(API_URL, json=feedback_payload)
        print("Código de estado feedback:", feedback_response.status_code)  # Depuración
        feedback_text = feedback_response.text  # Capturar la respuesta como string
        print("Respuesta de feedback API:", feedback_text)  # Depuración
        
        if feedback_response.status_code == 200:
            try:
                feedback_data = feedback_response.json()  # Intentar convertir a JSON
                improved_analysis = feedback_data.get("respuesta", feedback_text)  # Cambié 'cause_analysis' por 'improved_analysis'
            except (ValueError, AttributeError):
                improved_analysis = feedback_text  # Si no es JSON, usar el string plano
        else:
            improved_analysis = f"Error en la API (Código {feedback_response.status_code}): {feedback_text}"
        
        st.session_state["last_response"] = improved_analysis
        st.session_state["messages"].append({"role": "assistant", "content": improved_analysis})
        with st.chat_message("assistant"):
            st.markdown(improved_analysis, unsafe_allow_html=True)
