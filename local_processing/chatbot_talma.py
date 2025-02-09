import streamlit as st
import requests
import time

API_URL_CREATE = " "  
API_URL_GET = " "  

st.markdown("<h1 style='text-align: center;'>🤖 Chatbot Talma Reportes De Quejas</h1>", unsafe_allow_html=True)

# Inicializar estados de sesión
if "id_generation" not in st.session_state:
    st.session_state["id_generation"] = None
if "last_response" not in st.session_state:
    st.session_state["last_response"] = ""
if "feedback_mode" not in st.session_state:
    st.session_state["feedback_mode"] = False

# **Sección 1: Ingreso de Datos**
st.header("Ingresar Información del Hallazgo")
descripcion_hallazgo = st.text_area("Descripción del hallazgo:")
causa_raiz = st.text_area("Lista de Causas Raíz:")

# **Botón único para Enviar y Obtener Reporte o Feedback**
if st.button("Generar Reporte"):
    if descripcion_hallazgo and causa_raiz:
        payload = {
            "descripcion_hallazgo": descripcion_hallazgo,
            "causa_raiz": causa_raiz,
        }
        with st.spinner("Generando reporte..."):
            try:
                response = requests.post(API_URL_CREATE, json=payload)
                response.raise_for_status()
                data = response.json()
                st.session_state["id_generation"] = data["item"]["id_generation"]
                st.success("Reporte enviado correctamente. Generando análisis...")

                # **Consulta Automática al Segundo Endpoint (POST)**
                report_payload = {"id_generation": st.session_state["id_generation"]}
                max_retries = 3  # Número máximo de intentos
                retry_count = 0
                
                while retry_count < max_retries:
                    report_response = requests.post(API_URL_GET, json=report_payload)
                    time.sleep(50)  # Esperar antes de cada intento
                    
                    if report_response.status_code == 200:
                        report_data = report_response.json()
                        status = report_data.get("result", {}).get("status", "unknown")

                        if status == "completed":
                            st.session_state["last_response"] = report_data["result"]["response"]
                            st.success("Reporte generado exitosamente.")
                            st.write(st.session_state["last_response"])
                            break
                        else:
                            retry_count += 1
                            st.warning(f"Intento {retry_count}/{max_retries}... esperando respuesta.")
                    else:
                        retry_count += 1
                        st.warning(f"Error en la API. Intento {retry_count}/{max_retries}...")
                
                if retry_count == max_retries:
                    st.error("No se pudo obtener el reporte después de varios intentos. Inténtelo más tarde.")

            except requests.exceptions.RequestException as e:
                st.error(f"Error en la API: {e}")
    else:
        st.warning("Por favor, ingrese tanto la descripción del hallazgo como la causa raíz.")

# **Sección 2: Evaluación del Reporte**
if st.session_state["last_response"]:
    st.header("Evaluar Respuesta del Reporte")
    feedback_accept = st.radio("¿Está de acuerdo con la respuesta?", ("", "Sí", "No"))

    if feedback_accept == "Sí":
        st.success("¡Reporte aceptado! Puedes generar un nuevo reporte si lo deseas.")
        # Limpiar estados para permitir un nuevo reporte
        st.session_state["id_generation"] = None
        st.session_state["last_response"] = ""
        st.session_state["feedback_mode"] = False
    elif feedback_accept == "No":
        st.session_state["feedback_mode"] = True

# **Sección 3: Envío Automático de Feedback**
if st.session_state["feedback_mode"]:
    st.header("Ingresar Feedback para Mejorar el Reporte")
    feedback_text = st.text_area("Ingrese su feedback:")

    if st.button("Generar Reporte con Feedback"):
        if feedback_text:
            feedback_payload = {
                "id_generation": st.session_state["id_generation"],
                "feedback": feedback_text,
            }
            with st.spinner("Generando nuevo reporte con feedback..."):
                try:
                    response = requests.post(API_URL_CREATE, json=feedback_payload)
                    response.raise_for_status()
                    data = response.json()
                    st.session_state["id_generation"] = data["item"]["id_generation"]
                    st.success("Feedback enviado correctamente. Generando análisis...")
                    
                    # **Consulta Automática al Segundo Endpoint con Feedback**
                    report_payload = {"id_generation": st.session_state["id_generation"]}
                    max_retries = 3
                    retry_count = 0
                    
                    while retry_count < max_retries:
                        report_response = requests.post(API_URL_GET, json=report_payload)
                        time.sleep(20)
                        
                        if report_response.status_code == 200:
                            report_data = report_response.json()
                            print(report_data)
                            status = report_data.get("result", {}).get("status", "unknown")
                            
                            if status == "completed": 
                                st.session_state["last_response"] = report_data["result"]["response"]
                                st.success("Reporte mejorado generado exitosamente.")
                                st.write(st.session_state["last_response"])
                                break
                            else:
                                retry_count += 1
                                st.warning(f"Intento {retry_count}/{max_retries}... esperando respuesta.")
                        else:
                            retry_count += 1
                            st.warning(f"Error en la API. Intento {retry_count}/{max_retries}...")
                    
                    if retry_count == max_retries:
                        st.error("No se pudo obtener el reporte con feedback después de varios intentos.")

                except requests.exceptions.RequestException as e:
                    st.error(f"Error al generar reporte con feedback: {e}")
        else:
            st.warning("Por favor, ingrese el feedback antes de enviarlo.")
