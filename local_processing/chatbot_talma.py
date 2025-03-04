import streamlit as st
import requests
import time
import re

API_URL_CREATE = "https://qsdwrr8keh.execute-api.us-east-1.amazonaws.com/dev/similarity_search"  
API_URL_GET = "https://qsdwrr8keh.execute-api.us-east-1.amazonaws.com/dev/get_result"  

st.markdown("<h1 style='text-align: center;'>🤖 Chatbot Talma Reportes De Quejas</h1>", unsafe_allow_html=True)

# Inicializar estados de sesión
if "reportes" not in st.session_state:
    st.session_state["reportes"] = []
if "refresh" not in st.session_state:
    st.session_state["refresh"] = False
if "feedback_mode" not in st.session_state:
    st.session_state["feedback_mode"] = False
if "id_generation" not in st.session_state:
    st.session_state["id_generation"] = None
if "feedback_reports" not in st.session_state:
    st.session_state["feedback_reports"] = {}

if st.button("🔄 Volver a Interfaz Inicial"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]  # Borra todas las variables de sesión
    st.rerun()

# *Sección 1: Ingreso de Datos*
st.header("Ingresar Información Para el Reporte")
descripcion_hallazgo = st.text_area("Descripción del hallazgo:")
causa_raiz = st.text_area("Lista de Causas Raíz:")

# *Botón para generar reporte*
if st.button("Generar Reporte"):
    if descripcion_hallazgo and causa_raiz:
        payload = {
            "descripcion_hallazgo": re.sub(r'\n+', ' ', descripcion_hallazgo),
            "causa_raiz": causa_raiz,
        }

        with st.spinner("Generando reporte..."):
            try:
                response = requests.post(API_URL_CREATE, json=payload)
                response.raise_for_status()
                data = response.json()
                id_generation = data["item"]["id_generation"]
                st.session_state["id_generation"] = id_generation
                st.success("Reporte enviado correctamente. Generando análisis...")
                
                # *Consulta automática al segundo endpoint (POST)*
                report_payload = {"id_generation": id_generation}
                max_retries = 5
                retry_count = 0
                
                while retry_count < max_retries:
                    report_response = requests.post(API_URL_GET, json=report_payload)
                    time.sleep(30)
                    
                    if report_response.status_code == 200:
                        report_data = report_response.json()
                        status = report_data.get("result", {}).get("status", "unknown")
                        
                        if status == "completed":
                            report_number = len(st.session_state["reportes"]) + 1
                            st.session_state["reportes"].append({
                                "report_number": report_number,
                                "id_generation": id_generation,
                                "info_manuales": report_data.get("result", {}).get("info_manuales", "unknown"),
                                "evento_hallazgo": report_data.get("result", {}).get("descripcion_hallazgo", "unknown"),
                                "response_info": report_data["result"]["response"],
                            })
                            st.session_state["feedback_reports"][report_number] = []
                            
                            st.success("Reporte generado exitosamente.")
                            st.session_state["refresh"] = True
                            break
                        else:
                            retry_count += 1
                            st.warning(f"Intento {retry_count}/{max_retries}... esperando respuesta.")
                    else:
                        retry_count += 1
                        st.warning(f"Error en la API. Intento {retry_count}/{max_retries}...")
                
                if retry_count == max_retries:
                    st.error("No se pudo obtener el reporte después de varios intentos.")
            
            except requests.exceptions.RequestException as e:
                st.error(f"Error en la API: {e}")
    else:
        st.warning("Por favor, ingrese tanto la descripción del hallazgo como la causa raíz.")

# *Sección 2: Mostrar Reportes Generados*
if st.session_state["reportes"]:
    st.header("Reportes Generados")
    for reporte in st.session_state["reportes"]:
        with st.expander(f"Reporte {reporte['report_number']}", expanded=st.session_state["refresh"]):
            st.write(f"**Información manuales:**\n\n{reporte['info_manuales']}")
            st.write(f"**Evento:**\n\n{reporte['evento_hallazgo']}")
            st.write(f"**Respuesta del reporte:**\n\n{reporte['response_info']}")
    
    st.session_state["refresh"] = False

    # *Sección 3: Evaluación del Último Reporte*
    st.header("Evaluar Respuesta del Último Reporte")
    feedback_accept = st.radio("¿Está de acuerdo con la respuesta?", ("", "Sí", "No"))

    if feedback_accept == "No":
        st.session_state["feedback_mode"] = True
    else:
        st.session_state["feedback_mode"] = False

# *Sección 4: Ingreso de Feedback*
if st.session_state["feedback_mode"]:
    st.header("Ingresar Feedback para Mejorar el Reporte")
    feedback_text = st.text_area("Ingrese su feedback:")
    
    if st.button("Generar Reporte con Feedback"):
        if feedback_text:
            last_report = st.session_state["reportes"][-1]
            report_number = last_report["report_number"]
            feedback_number = len(st.session_state["feedback_reports"][report_number]) + 1
            
            feedback_payload = {
                "id_generation": last_report["id_generation"],
                "feedback": feedback_text,
            }
            with st.spinner("Generando nuevo reporte con feedback..."):
                try:
                    response = requests.post(API_URL_CREATE, json=feedback_payload)
                    response.raise_for_status()
                    data = response.json()
                    new_id_generation = data["item"]["id_generation"]
                    st.success("Feedback enviado correctamente. Generando análisis...")
                    
                    report_payload = {"id_generation": new_id_generation}
                    retry_count = 0
                    max_retries = 5
                    
                    while retry_count < max_retries:
                        report_response = requests.post(API_URL_GET, json=report_payload)
                        time.sleep(20)
                        
                        if report_response.status_code == 200:
                            report_data = report_response.json()
                            status = report_data.get("result", {}).get("status", "unknown")
                            
                            if status == "completed":
                                st.session_state["feedback_reports"][report_number].append({
                                    "feedback_number": feedback_number,
                                    "info_manuales": report_data.get("result", {}).get("info_manuales", "unknown"),
                                    "evento_hallazgo": report_data.get("result", {}).get("descripcion_hallazgo", "unknown"),
                                    "response_info": report_data["result"]["response"],
                                })
                                st.success("Reporte mejorado generado exitosamente.")
                                break
                            else:
                                retry_count += 1
                                st.warning(f"Intento {retry_count}/{max_retries}... esperando respuesta.")
                        else:
                            retry_count += 1
                            st.warning(f"Error en la API. Intento {retry_count}/{max_retries}...")

                    if retry_count == max_retries:
                        st.error("No se pudo obtener el reporte después de varios intentos.")

                except requests.exceptions.RequestException as e:
                    st.error(f"Error al generar reporte con feedback: {e}")

# *Sección 5: Mostrar Reportes con Feedback*
if any(st.session_state["feedback_reports"].values()):
    st.header("Reportes Generados con Feedback")
    for report_number, feedback_list in st.session_state["feedback_reports"].items():
        for feedback_report in feedback_list:
            with st.expander(f"Reporte {report_number} - Feedback {feedback_report['feedback_number']}"):
                st.write(f"**Información manuales:**\n\n{feedback_report['info_manuales']}")
                st.write(f"**Evento:**\n\n{feedback_report['evento_hallazgo']}")
                st.write(f"**Respuesta del reporte con feedback:**\n\n{feedback_report['response_info']}")