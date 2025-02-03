import streamlit as st
import requests

API_URL = " "  # Aquí debes colocar la URL de tu API

st.markdown("<h1 style='text-align: center;'>🤖 Chatbot Talma Reportes De Quejas</h1>", unsafe_allow_html=True)

# Inicializar el estado de la sesión si no está ya definido
if "messages" not in st.session_state:
    st.session_state["messages"] = []
    st.session_state["last_response"] = ""
    st.session_state["last_user_input"] = ""
    st.session_state["last_causa_raiz"] = ""  # Añadir almacenamiento de causa raíz
    st.session_state["info_saved"] = False  # Estado para saber si la información fue guardada
    st.session_state["working_with_feedback"] = False  # Estado para saber si estamos trabajando con feedback
    st.session_state["response_accepted"] = False  # Estado para saber si la respuesta fue aceptada

# Mostrar los mensajes anteriores en el chat
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# **Si la información no ha sido aceptada**, mostramos los campos de entrada
if not st.session_state["response_accepted"]:
    # Entrada para la descripción del hallazgo
    user_input = st.text_area("Ingrese información sobre la descripción del hallazgo...", value=st.session_state.get("last_user_input", ""))

    # Entrada para la causa raíz
    causa_raiz_input = st.text_area("Ingrese lista de Causas Raíz ...", value=st.session_state.get("last_causa_raiz", ""))

    # Botón para guardar causa raíz y descripción del hallazgo
    submit_info_button = st.button("Guardar Información")

    # Si el botón para guardar la información es presionado
    if submit_info_button:
        if user_input and causa_raiz_input:
            # Guardamos ambas informaciones en el estado de la sesión
            st.session_state["last_user_input"] = user_input
            st.session_state["last_causa_raiz"] = causa_raiz_input
            st.session_state["messages"].append({"role": "user", "content": f"Descripción: {user_input}\nCausa raíz: {causa_raiz_input}"})

            st.success("Información guardada correctamente. Ahora puedes generar el reporte.")
            st.session_state["info_saved"] = True  # Indicamos que la información fue guardada
            st.session_state["working_with_feedback"] = False  # Aseguramos que no se está trabajando con feedback
        else:
            st.warning("Por favor, ingresa tanto la descripción del hallazgo como la causa raíz.")
else:
    st.info("La respuesta ha sido aceptada. Ahora puedes generar un nuevo reporte o trabajar con feedback.")
    
# **Si la información ha sido guardada**, mostramos el botón para generar el reporte
if st.session_state["info_saved"] and not st.session_state["working_with_feedback"] and not st.session_state["response_accepted"]:
    submit_report_button = st.button("Generar Reporte")

    # Si el botón "Generar Reporte" es presionado
    if submit_report_button:
        # Solo proceder si la descripción del hallazgo y la causa raíz están presentes
        if st.session_state["last_user_input"] and st.session_state["last_causa_raiz"]:
            payload = {
                "descripcion_hallazgo": st.session_state["last_user_input"],
                "causa_raiz": st.session_state["last_causa_raiz"],
            }

            with st.spinner("Generando información para reporte..."):
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

                # Después de enviar la solicitud, se puede permitir ingresar feedback
                st.session_state["info_saved"] = False  # Una vez enviado, se puede generar nueva información
                st.session_state["working_with_feedback"] = True  # Ahora estamos trabajando con feedback

                # Mostrar el botón de aceptación de la respuesta directamente
                st.session_state["response_accepted"] = False  # Mantenerlo como "no aceptado" hasta que se confirme
                feedback_accept = st.radio("¿Está de acuerdo con la respuesta?", ("Sí", "No"))
                
                if feedback_accept == "Sí":
                    st.success("¡Reporte aceptado! Ahora puedes generar un nuevo reporte.")
                    st.session_state["info_saved"] = False  # Resetear estado para nuevo reporte
                    st.session_state["working_with_feedback"] = False  # Terminamos con el feedback
                    st.session_state["response_accepted"] = True  # Marcamos la respuesta como aceptada
                elif feedback_accept == "No":
                    st.session_state["working_with_feedback"] = True  # Permitir feedback si se rechaza
                    st.info("Puedes seguir trabajando con el feedback o modificar tu descripción.")

# **Nueva sección**: Permitir que el usuario ingrese feedback si ya ha recibido una respuesta.
if st.session_state["working_with_feedback"] and not st.session_state["response_accepted"]:
    feedback = st.text_area("Si la respuesta no es satisfactoria, ingrese su feedback aquí:")

    submit_feedback_button = st.button("Aplicar Feedback")

    # Si se ha proporcionado feedback, realizar una nueva solicitud
    if submit_feedback_button and feedback and st.session_state["last_response"]:
        st.session_state["messages"].append({"role": "user", "content": feedback})
        with st.chat_message("user"):
            st.markdown(feedback, unsafe_allow_html=True)

        feedback_payload = {
            "descripcion_hallazgo": st.session_state["last_user_input"],
            "causa_raiz": st.session_state["last_causa_raiz"],  # Usar la causa raíz de la primera solicitud
            "feedback": feedback,
        }

        with st.spinner("Reevaluando información para reporte basado en feedback..."):
            feedback_response = requests.post(API_URL, json=feedback_payload)
            print("Código de estado feedback:", feedback_response.status_code)  # Depuración
            feedback_text = feedback_response.text  # Capturar la respuesta como string
            print("Respuesta de feedback API:", feedback_text)  # Depuración

            if feedback_response.status_code == 200:
                try:
                    feedback_data = feedback_response.json()  
                    improved_analysis = feedback_data.get("respuesta", feedback_text)  
                except (ValueError, AttributeError):
                    improved_analysis = feedback_text  
            else:
                improved_analysis = f"Error en la API (Código {feedback_response.status_code}): {feedback_text}"

            st.session_state["last_response"] = improved_analysis
            st.session_state["messages"].append({"role": "assistant", "content": improved_analysis})
            with st.chat_message("assistant"):
                st.markdown(improved_analysis, unsafe_allow_html=True)

        # **Botón para aceptar o rechazar el feedback**
        feedback_accept = st.radio("¿Está de acuerdo con la respuesta?", ("Sí", "No"))

        if feedback_accept == "Sí":
            st.success("¡Reporte aceptado! Ahora puedes generar un nuevo reporte.")
            st.session_state["info_saved"] = False  # Resetear estado para nuevo reporte
            st.session_state["working_with_feedback"] = False  # Terminamos con el feedback
            st.session_state["response_accepted"] = True  # Marcamos la respuesta como aceptada
        else:
            st.info("Puedes seguir trabajando con el feedback o modificar tu descripción.")

# **Permitir generar un nuevo reporte después de aceptar el reporte**.
if st.session_state["response_accepted"]:
    new_report_button = st.button("Generar un nuevo reporte")

    if new_report_button:
        # Restablecer el estado para un nuevo reporte
        st.session_state["response_accepted"] = False
        st.session_state["info_saved"] = False
        st.session_state["working_with_feedback"] = False
        st.session_state["messages"] = []  # Limpiar el chat
        st.session_state["last_user_input"] = ""
        st.session_state["last_causa_raiz"] = ""
        st.session_state["last_response"] = ""

        st.info("Nuevo reporte generado. Ingresa la información del hallazgo y la causa raíz.")
