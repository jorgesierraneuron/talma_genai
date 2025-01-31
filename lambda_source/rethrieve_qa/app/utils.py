import re
from connections import get_vector_store
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from config import openai_api_key

def extraer_codigo_y_cliente(texto):
    """
    Extrae el código de aeropuerto y nombre del cliente desde un texto.
    Si ocurre un error, maneja la excepción y devuelve None para ambos campos.
    Además, maneja casos especiales como "Jet Smart" o "Viva Air", y devuelve todo en mayúsculas.
    """
    try:
        # Buscar el código de aeropuerto (lo que está entre "aeropuerto" y "y")
        codigo_aeropuerto = re.search(r'aeropuerto\s+(\w+)\s+y', texto, re.IGNORECASE)
        if codigo_aeropuerto:
            codigo_aeropuerto = codigo_aeropuerto.group(1).strip().upper()  # Elimina cualquier espacio extra y pasa a mayúsculas
        else:
            codigo_aeropuerto = None

        # Casos especiales de nombres de clientes (Jet Smart, Viva Air)
        nombres_especiales = ["Jet Smart", "Viva Air"]
        nombre_cliente = None

        for nombre in nombres_especiales:
            if nombre.lower() in texto.lower():
                nombre_cliente = nombre
                break
        
        if not nombre_cliente:
            # Buscar el nombre del cliente (lo que está entre "cliente" y la primera palabra siguiente)
            nombre_cliente = re.search(r'cliente\s+([\w\s-]+?)(?=\s+\w|$)', texto, re.IGNORECASE)
            if nombre_cliente:
                nombre_cliente = nombre_cliente.group(1).strip().replace(" ", "").upper()  # Elimina los espacios y pasa a mayúsculas
            else:
                nombre_cliente = None

        # Convertir ambos valores a mayúsculas
        if codigo_aeropuerto:
            codigo_aeropuerto = codigo_aeropuerto.upper()
        if nombre_cliente:
            nombre_cliente = nombre_cliente.upper()

        return codigo_aeropuerto, nombre_cliente

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        return None, None

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

def generate_cause_analysis_and_action_plan(first_element, descripcion_hallazgo):
    """
    Genera un análisis de causa utilizando el método de los 5 Porqués basado en ejemplos previos, 
    y además genera un plan de acción para abordar las causas identificadas, basándose en planes de acción previos. 
    Si no es necesario un plan de acción, el modelo avisará.
    
    Parámetros:
    - first_element (str): Ejemplos previos de análisis de causa para eventos similares, incluyendo análisis y planes de acción.
    - descripcion_hallazgo (str): Descripción detallada del evento nuevo.
    - openai_api_key (str): Clave API para acceder al modelo OpenAI.
    
    Retorna:
    - str: La respuesta generada por el modelo con el análisis de causa y el plan de acción (si aplica).
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
                Estos ejemplos incluyen análisis detallados que contienen múltiples campos relevantes, como las causas identificadas, así como los planes de acción implementados para corregir y prevenir los eventos. 

                Ejemplos previos:
                {ejemplos_similares}

                Utilizando estos ejemplos como referencia, realiza un análisis de causa para el siguiente evento nuevo, aplicando el método de los 5 Porqués y asegurándote de basar cada respuesta específicamente en la descripción del evento proporcionada.

                Evento: {descripcion_hallazgo}

                Instrucciones específicas:
                Realiza un análisis de causa utilizando exactamente cinco porqués, asegurándote de que cada uno esté directamente relacionado con la descripción del evento y las posibles causas asociadas.
                Redacta el análisis de forma estructurada, proporcionando explicaciones claras y concisas para cada porqué.
                Integra posibles fallas en procedimientos, coordinación, comunicación, herramientas o recursos humanos siempre que sean relevantes para el evento descrito.
                Asegúrate de que las respuestas sean lógicas y progresivas, explorando cada nivel de causa hasta llegar a la raíz del problema.
                Concluye con un breve resumen de las causas principales identificadas.

                Luego, en función del análisis de causa, genera un plan de acción si es necesario. El plan de acción debe estar basado en los planes de acción de eventos previos (de los ejemplos previos), pero adaptado al evento actual. Si no es necesario un plan de acción debido a la naturaleza del evento, debes decirlo explícitamente.

                El plan de acción debe incluir:

                - Acciones correctivas inmediatas, si son necesarias.
                - Propuestas de cambios en procedimientos o políticas, si son necesarias.
                - Recomendaciones para mejorar la capacitación o recursos humanos, si son necesarias.
                - Otras acciones relevantes para evitar la repetición del evento, si es necesario.

                Si no se necesita un plan de acción (por ejemplo, porque el evento fue debido a causas externas que no pueden corregirse internamente), indica que no se requiere plan de acción y explica por qué.

                Formato esperado para el análisis:

                Evento: {descripcion_hallazgo}

                Por qué 1: [Primera causa directa basada en la descripción del evento.]
                Por qué 2: [Causa más profunda que explique la razón detrás del primer porqué.]
                Por qué 3: [Tercer nivel de análisis, conectado con el segundo porqué.]
                Por qué 4: [Cuarta causa, vinculada al nivel anterior.]
                Por qué 5: [Causa raíz última, relacionada directamente con el evento.]
                Conclusión: [Síntesis de las causas principales identificadas y recomendaciones relevantes.]

                Plan de acción:
                [Si es necesario]
                1. [Acción correctiva inmediata 1 basada en el ejemplo previo.]
                2. [Acción correctiva inmediata 2 basada en el ejemplo previo.]
                3. [Cambio en procedimientos, si es necesario, basado en los ejemplos previos.]
                4. [Recomendaciones para mejorar capacitación o recursos humanos basadas en ejemplos previos.]
                5. [Acciones adicionales para prevenir la repetición del evento basadas en lo aprendido previamente.]

                [Si NO es necesario el plan de acción]
                No se requiere un plan de acción porque el evento fue causado por [explicación detallada de por qué no se necesita un plan de acción].
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


def apply_feedback(original_response, feedback):
    """
    Aplica el feedback recibido a la respuesta generada, tanto al análisis de causa como al plan de acción.
    
    Parámetros:
    - original_response (str): Respuesta original generada por el análisis de causa y el plan de acción.
    - feedback (str): Correcciones o mejoras sugeridas.
    
    Retorna:
    - str: Respuesta corregida basada en el feedback.
    """
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=openai_api_key,
        max_tokens=2000,
        temperature=0.1
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", """
                Tienes que corregir y mejorar la siguiente respuesta que incluye un análisis de causa y un plan de acción siguiendo estas instrucciones:
                
                - Mantén el formato de la respuesta con la siguiente estructura, respetando la numeración exacta:
                  Evento:
                  Por qué 1:
                  Por qué 2:
                  Por qué 3:
                  Por qué 4:
                  Por qué 5:
                  Conclusión:
                  Plan de acción:
                  (Si no es necesario plan de acción, indica explícitamente que no se requiere un plan y explica por qué.)

                - Si el feedback solo menciona cambios en un "Por qué" específico, solo modifica esa parte y deja los demás "Por qué" sin cambios.
                - Si el feedback menciona cambios en el "Plan de acción", aplica los cambios solo a esa sección, sin modificar el análisis de causa.
                - Si se menciona una modificación para la conclusión, modifícala según las sugerencias, sin alterar el resto del análisis o plan.
                - Si no se mencionan cambios para un "Por qué" o para el plan de acción, no los modifiques.
                - Asegúrate de respetar el orden y estructura sin agregar o eliminar elementos. No agregues nueva información si no se menciona en el feedback.

                Respuesta Original: {original_response}
                Feedback: {feedback}
            """),
            ("human", "{original_response}\n{feedback}")
        ]
    )

    chain = prompt | llm
    response = chain.invoke({"original_response": original_response, "feedback": feedback})
    
    return response.content


