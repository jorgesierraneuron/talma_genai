import re
from app.connections import get_vector_store
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.config import openai_api_key


def extraer_codigo_y_cliente(texto):
    """
    Extrae el código de aeropuerto y nombre del cliente desde un texto.
    """
    codigo_aeropuerto = re.search(r'aeropuerto\s+(\w+)', texto, re.IGNORECASE)
    nombre_cliente = re.search(r'cliente\s+([\w\s-]+)', texto, re.IGNORECASE)

    codigo_aeropuerto = codigo_aeropuerto.group(1).strip() if codigo_aeropuerto else None
    nombre_cliente = nombre_cliente.group(1).strip().upper() if nombre_cliente else None

    return codigo_aeropuerto, nombre_cliente

def search_filtered(descripcion_hallazgo):
    """
    Realiza una búsqueda de similaridad filtrando por código de aeropuerto y cliente.
    """
    codigo_aeropuerto, nombre_cliente = extraer_codigo_y_cliente(descripcion_hallazgo)
    
    if not codigo_aeropuerto or not nombre_cliente:
        return {"mensaje": "No se pudo extraer el código de aeropuerto o el nombre del cliente."}

    vector_store = get_vector_store("""
        MATCH (node:Incidente)
        WHERE node.codigo_aeropuerto = $codigo_aeropuerto AND node.nombre_cliente = $nombre_cliente
        MATCH (node)-[:TIENE_ANALISIS]->(analisisCausa:AnalisisCausas)
        MATCH (node)-[:TIENE_PLAN_DE_ACCION]->(planAccion:PlanAccion)
        MATCH (node)-[:TIENE_CAUSA_RAIZ]->(causaRaiz:CausaRaiz)
        RETURN
            node.descripcion_hallazgo AS text,
            score,
            {
                analisis_causa: analisisCausa.texto,
                plan_de_accion: planAccion.texto,
                causa_raiz: causaRaiz.texto
            } AS metadata
    """)

    result = vector_store.similarity_search(
        descripcion_hallazgo,
        k=3,
        params={"codigo_aeropuerto": codigo_aeropuerto, "nombre_cliente": nombre_cliente}
    )

    if not result:
        return {"mensaje": "No se encontraron resultados similares con los filtros aplicados."}

    return {
        "codigo_aeropuerto": codigo_aeropuerto,
        "nombre_cliente": nombre_cliente,
        "resultados_de_busqueda": [
            {
                "descripcion_hallazgo": res.page_content,
                "analisis_causa": res.metadata.get("analisis_causa", "No disponible"),
                "plan_de_accion": res.metadata.get("plan_de_accion", "No disponible"),
                "causa_raiz": res.metadata.get("causa_raiz", "No disponible")
            }
            for res in result
        ]
    }

def search_unfiltered(descripcion_hallazgo):
    """
    Realiza una búsqueda de similaridad en toda la base de datos sin filtros.
    """
    vector_store = get_vector_store()

    result = vector_store.similarity_search(descripcion_hallazgo, k=3)

    if not result:
        return {"mensaje": "No se encontraron resultados similares."}

    return {
        "resultados_de_busqueda": [
            {
                "descripcion_hallazgo": res.page_content,
                "analisis_causa": res.metadata.get("analisis_causa", "No disponible"),
                "plan_de_accion": res.metadata.get("plan_de_accion", "No disponible"),
                "causa_raiz": res.metadata.get("causa_raiz", "No disponible")
            }
            for res in result
        ]
    }

def generate_cause_analysis(first_element, descripcion_hallazgo):
    """
    Genera un análisis de causa utilizando el método de los 5 Porqués basado en ejemplos previos.
    
    Parámetros:
    - first_element (str): Ejemplos previos de análisis de causa para eventos similares.
    - descripcion_hallazgo (str): Descripción detallada del evento nuevo.
    - openai_api_key (str): Clave API para acceder al modelo OpenAI.
    
    Retorna:
    - str: La respuesta generada por el modelo con el análisis de causa.
    """

    # Configuración del modelo LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=openai_api_key,
        max_tokens=2000,
        temperature=0.1
    )

    # Definir el template de prompt
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                A continuación, se presentan ejemplos previos de análisis de causa realizados utilizando el método de los 5 Porqués para eventos similares dentro de la misma operación. 
                Estos ejemplos incluyen análisis detallados que contienen múltiples campos relevantes para proporcionar contexto específico sobre el proceso, los factores contribuyentes y las lecciones aprendidas:

                Ejemplos previos:
                {ejemplos_similares}

                Utilizando esta información como referencia, realiza un análisis de causa para el siguiente evento nuevo, aplicando el método de los 5 Porqués y asegurándote de basar cada respuesta específicamente en la descripción del evento proporcionada.

                Evento: {descripcion_hallazgo}

                Instrucciones específicas:
                Realiza un análisis de causa utilizando exactamente cinco porqués, asegurándote de que cada uno esté directamente relacionado con la descripción del evento y las posibles causas asociadas.
                Redacta el análisis de forma estructurada, proporcionando explicaciones claras y concisas para cada porqué.
                Integra posibles fallas en procedimientos, coordinación, comunicación, herramientas o recursos humanos siempre que sean relevantes para el evento descrito.
                Asegúrate de que las respuestas sean lógicas y progresivas, explorando cada nivel de causa hasta llegar a la raíz del problema.
                Concluye con un breve resumen de las causas principales identificadas y, si es necesario, incluye recomendaciones para evitar que este tipo de eventos se repita.
                Formato esperado para el análisis:

                Evento: {descripcion_hallazgo}

                Por qué 1: [Primera causa directa basada en la descripción del evento.]
                Por qué 2: [Causa más profunda que explique la razón detrás del primer porqué.]
                Por qué 3: [Tercer nivel de análisis, conectado con el segundo porqué.]
                Por qué 4: [Cuarta causa, vinculada al nivel anterior.]
                Por qué 5: [Causa raíz última, relacionada directamente con el evento.]
                Conclusión: [Síntesis de las causas principales y recomendaciones relevantes.]
                Nota: Cada porqué debe derivarse directamente del contexto y la descripción del evento proporcionado. Si es útil, utiliza patrones o lecciones aprendidas de los ejemplos previos, pero ajusta las causas al caso específico,
                limitate solo a la estructura definida anteriormente de evento , los Por qué y la Conclusión.
                """
            ),
            (
                "human",
                "{ejemplos_similares}\nEvento: {descripcion_hallazgo}",
            ),
        ]
    )

    # Crear la cadena combinando el modelo y el prompt
    chain = prompt | llm

    # Ejecutar la invocación
    response = chain.invoke(
        {
            "ejemplos_similares": first_element,  
            "descripcion_hallazgo": descripcion_hallazgo 
        }
    )

    # Devolver la respuesta generada
    return response.content

