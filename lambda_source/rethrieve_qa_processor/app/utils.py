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
    Realiza una búsqueda de similaridad en toda la base de datos sin filtros,
    incluyendo la información de los nodos relacionados.
    """
    vector_store = get_vector_store("""
        MATCH (node:Incidente)
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

def generate_cause_analysis_and_action_plan(first_element, descripcion_hallazgo, causas_raiz_str, info_manuales):
        """
        Genera un análisis de causa utilizando el método de los 5 Porqués basado en ejemplos previos, 
        identificando la causa raíz real sin forzar una estructura rígida y considerando factores externos. 
        Además, genera un plan de acción concreto y medible si es necesario.
        
        Parámetros:
        - first_element (dict): Diccionario con un solo ejemplo de análisis de causa para eventos similares.
        - descripcion_hallazgo (str): Descripción detallada del evento nuevo.
        - causas_raiz_str (str): Cadena de texto con causas raíz posibles, separadas por comas.
        - info_manuales (str): Procedimientos y regulaciones aplicables.
        
        Retorna:
        - str: La respuesta generada por el modelo con el análisis de causa y el plan de acción (si aplica).
        """
        
        # Convertir las causas raíz a una lista
        causas_raiz = causas_raiz_str.split(',')
    
        # Configuración del modelo LLM
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=openai_api_key,
            max_tokens=2000,
            temperature=0.1
        )
    
        # Convertir el diccionario de first_element a una representación legible para el prompt
        ejemplos_similares = "\n\n\n".join([f"{key}: {value}" for key, value in first_element.items()])
    
        # Definir el template de prompt con formato optimizado
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """
                    Role: Analista de Incidentes Operaciones Talma

                    Objetivo: Identificar la causa raíz real del incidente mediante un análisis lógico y progresivo, sin forzar cinco "porqués" si no son necesarios, y definir planes de acción para corregir y prevenir eventos.

                    Responsabilidades:
                    - Aplicar el método de los 5 Porqués asegurando coherencia con análisis previos.
                    - Identificar la causa raíz y proponer acciones correctivas basadas en datos documentados.
                    - Documentar el análisis siguiendo el formato estándar.
                    - Recomendar mejoras en procedimientos, capacitación y coordinación.

                    Habilidades y Competencias:
                    - Pensamiento analítico y enfoque estructurado en la resolución de problemas.
                    - Dominio del método de los 5 Porqués e identificación de patrones en datos históricos.
                    - Redacción técnica clara y concisa.
                    - Conocimiento de procedimientos operativos y normativas.

                    Criterios de Evaluación:
                    - Precisión en la identificación de la causa raíz.
                    - Coherencia y secuencia lógica en el análisis.
                    - Inclusión de factores externos cuando sean relevantes.
                    - Propuestas de planes de acción concretos y viables.
                    - Impacto de las recomendaciones en la prevención de eventos futuros.

                    Consideraciones para el análisis:
                    - No es obligatorio llegar a cinco "porqués" si la causa raíz es clara antes.
                    - Evitar explicaciones genéricas sin evidencia.
                    - Incluir factores externos cuando sean aplicables.
                    - Usar detalles específicos del evento (matrícula, códigos de pallet, ubicación, etc.).
                    - Relatar la secuencia cronológica del incidente para reflejar su evolución.

                    Ejemplos previos de análisis:
                    {ejemplos_similares}

                    Manual de procedimiento aplicable al incidente:
                    {manuales}

                    Evento a analizar:
                    {descripcion_hallazgo}

                    Selecciona la causa raíz más adecuada de la siguiente lista:
                    {causas_raiz}

                    Instrucciones para el análisis:
                    1. Identifica la causa raíz sin forzar la aplicación mecánica de los “5 Porqués”.
                    2. Explica cada paso de forma lógica, vinculando cada nivel con el anterior.
                    3. Incluye factores externos si son relevantes.
                    4. Relata la evolución del incidente de forma estructurada.
                    5. Propón de 1 a 3 planes de acción concretos y medibles.
                    6. Concluye con un breve resumen de las causas principales identificadas.
                    7. **Responde en el formato exacto siguiente:**

                    Formato de salida:

                    Evento:
                    {descripcion_hallazgo}

                    Análisis de los 5 Porqués:

                    - Por qué 1: [Pregunta sobre el evento y primera causa directa.]
                    - Por qué 2: [Pregunta sobre la respuesta anterior y causa más profunda.]
                    - Por qué 3: [Si es necesario, continuar el análisis.]
                    - Por qué 4: [Si aún no se identifica la causa raíz, profundizar más.]
                    - Por qué 5: [Último nivel si es necesario.]

                    Causa raíz:
                    [Causa raíz seleccionada de la lista.]

                    Conclusión:
                    [Resumen de la evolución del evento y los principales factores contribuyentes.]

                    Plan de acción:
                    
                    - 1. [Acción correctiva específica basada en la causa real.]
                    - 2. [Cambio en procedimiento, si es necesario.]
                    - 3. [Recomendación adicional para evitar futuras ocurrencias.]

                    Si no es necesario un plan de acción:
                    No se requiere un plan de acción porque el evento fue causado por [explicación detallada].

                    """
                ),
                (
                    "human",
                    "Evalúa el evento y genera el análisis de causa con los Porqués necesarios, la causa raíz y un plan de acción concreto."
                ),
            ]
        )
    
        # Crear la cadena combinando el modelo y el prompt
        chain = prompt | llm
    
        # Ejecutar la invocación
        response = chain.invoke(
            {
                "ejemplos_similares": ejemplos_similares,  
                "descripcion_hallazgo": descripcion_hallazgo,
                "causas_raiz": ", ".join(causas_raiz),
                "manuales": info_manuales
            }
        )
    
        # Devolver la respuesta generada
        return {
            "response": response.content,
            "ejemplos_similares": ejemplos_similares,
            "causas_raiz": ", ".join(causas_raiz)
        }

def apply_feedback(item):
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

    # Se crea el prompt asegurando que la estructura exacta debe ser mantenida
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", """
                Tienes que corregir y mejorar la siguiente respuesta que incluye ejemplos previos, evento, análisis de causa, causa raíz y plan de acción. Sigue estas instrucciones cuidadosamente:

                - Mantén el **formato de la respuesta exactamente como está**, respetando la numeración y la estructura. **No se debe omitir ninguna sección**.
                - La respuesta debe incluir todas las secciones en este **orden exacto**: 
                    - Ejemplos previos:
                    - Evento:
                    - Análisis de los 5 Porqués:
                    - Por qué 1:
                    - Por qué 2:
                    - Por qué 3:
                    - Por qué 4:
                    - Por qué 5:
                    - Causa raíz:
                    - Conclusión:
                    - Plan de acción:
                
                - **No modifiques los ejemplos previos**. Estos deben permanecer exactamente como están, sin cambios.
                - Si el feedback menciona cambios en un "Por qué" específico (por ejemplo, "modificar Por qué 2"), **solo modifica esa parte y deja los demás "Por qué" sin cambios**.
                - Si el feedback menciona cambios en la "Causa raíz", **realiza la modificación solo en esa sección** según lo indicado en el feedback.
                - Si el feedback menciona cambios en el "Plan de acción", **aplícalos solo a esa sección**, sin modificar el análisis de causa ni la conclusión.
                - Si el feedback menciona cambios en la "Conclusión", **realiza solo esas modificaciones** y deja el resto de la respuesta intacto.
                - Si no se mencionan cambios para un "Por qué", "Plan de acción", "Causa raíz" o "Conclusión", **no los modifiques**.
                - Asegúrate de mantener **la estructura exacta** de la respuesta, **sin agregar ni eliminar elementos**, y **sin alterar el orden**.

                Respuesta Original: {original_response}
                Feedback: {feedback}
            """),
            ("human", "{original_response}\n{feedback}")
        ]
    )

    # Creamos la cadena de llamada al modelo
    chain = prompt | llm

    # Invocamos el modelo para procesar la respuesta con el feedback
    response = chain.invoke({"original_response": item["response"], "feedback": item["feedback"]})
    
    # Regresamos el contenido corregido
    return response.content


