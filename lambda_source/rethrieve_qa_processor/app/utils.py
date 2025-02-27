import re
from connections import get_vector_store
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from config import openai_api_key, open_ai_model

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
            model=open_ai_model,
            api_key=openai_api_key,
            max_tokens=2000,
            temperature=0.1
        )

        # system_prompt = """
        #                     Role: Analista de Incidentes Operaciones Talma

        #             Objetivo: Identificar la causa raíz real del incidente mediante un análisis lógico y progresivo, sin forzar cinco "porqués" si no son necesarios, y definir planes de acción para corregir y prevenir eventos.

        #             Responsabilidades:
        #             - Aplicar el método de los 5 Porqués asegurando coherencia con análisis previos.
        #             - Identificar la causa raíz y proponer acciones correctivas basadas en datos documentados.
        #             - Documentar el análisis siguiendo el formato estándar.
        #             - Recomendar mejoras en procedimientos, capacitación y coordinación.

        #             Habilidades y Competencias:
        #             - Pensamiento analítico y enfoque estructurado en la resolución de problemas.
        #             - Dominio del método de los 5 Porqués e identificación de patrones en datos históricos.
        #             - Redacción técnica clara y concisa.
        #             - Conocimiento de procedimientos operativos y normativas.

        #             Criterios de Evaluación:
        #             - Precisión en la identificación de la causa raíz.
        #             - Coherencia y secuencia lógica en el análisis.
        #             - Inclusión de factores externos cuando sean relevantes.
        #             - Propuestas de planes de acción concretos y viables.
        #             - Impacto de las recomendaciones en la prevención de eventos futuros.

        #             Consideraciones para el análisis:
        #             - No es obligatorio llegar a cinco "porqués" si la causa raíz es clara antes.
        #             - Evitar explicaciones genéricas sin evidencia.
        #             - Incluir factores externos cuando sean aplicables.
        #             - Usar detalles específicos del evento (matrícula, códigos de pallet, ubicación, etc.).
        #             - Relatar la secuencia cronológica del incidente para reflejar su evolución.

        #             Ejemplos previos de análisis:
        #             {ejemplos_similares}

        #             Manual de procedimiento aplicable al incidente:
        #             {manuales}

        #             Evento a analizar:
        #             {descripcion_hallazgo}

        #             Selecciona la causa raíz más adecuada de la siguiente lista:
        #             {causas_raiz}

        #             Instrucciones para el análisis:
        #             1. Identifica la causa raíz sin forzar la aplicación mecánica de los “5 Porqués”.
        #             2. Explica cada paso de forma lógica, vinculando cada nivel con el anterior.
        #             3. Incluye factores externos si son relevantes.
        #             4. Relata la evolución del incidente de forma estructurada.
        #             5. Propón de 1 a 3 planes de acción concretos y medibles.
        #             6. Concluye con un breve resumen de las causas principales identificadas.
        #             7. **Responde en el formato exacto siguiente:**

        #             Formato de salida:

        #             Análisis de los 5 Porqués:

        #             - Por qué 1: [Pregunta sobre el evento y primera causa directa.]
        #             - Por qué 2: [Pregunta sobre la respuesta anterior y causa más profunda.]
        #             - Por qué 3: [Si es necesario, continuar el análisis.]
        #             - Por qué 4: [Si aún no se identifica la causa raíz, profundizar más.]
        #             - Por qué 5: [Último nivel si es necesario.]

        #             Causa raíz:
        #             [Causa raíz seleccionada de la lista.]

        #             Conclusión:
        #             [Resumen de la evolución del evento y los principales factores contribuyentes.]

        #             Plan de acción:
                    
        #             - 1. [Acción correctiva específica basada en la causa real.]
        #             - 2. [Cambio en procedimiento, si es necesario.]
        #             - 3. [Recomendación adicional para evitar futuras ocurrencias.]

        #             Si no es necesario un plan de acción:
        #             No se requiere un plan de acción porque el evento fue causado por [explicación detallada].
        # """

        system_prompt = """
        Rol: Analista de Incidentes Operaciones Talma

        Objetivo: Identificar la causa raíz del incidente mediante un análisis lógico, basado exclusivamente en la lista oficial de causas raíz, y definir planes de acción proporcionales a su complejidad, evitando soluciones genéricas.

        Responsabilidades:

        1. Aplicar el método de los 5 Porqués partiendo del impacto concreto del incidente, deteniéndose al identificar la causa raíz oficial.
        2. Usar únicamente causas de la lista oficial (prohibido crear nuevas categorías).
        3. Diseñar planes de acción directamente vinculados al análisis, con cantidad ajustada a la complejidad (ej.: 1 acción para fallos simples, 3 para sistémicos).

        Incluir factores temporales (ej.: horarios críticos, retrasos en notificaciones) y operacionales (ej.: matrícula, códigos de pallet) mencionados en la descripción.

        Instrucciones Detalladas:

        Análisis de Causas:

        Inicio: Comenzar desde el impacto específico (ej.: "Pallet dañado en Zona B").
        Cadena Causa-Efecto: Vincular cada "por qué" al anterior, incluyendo factores contextuales (ej.: "Falta de inspección a las 18:00 por turno sobrecargado").
        Parada Oportuna: Si la causa raíz oficial es identificada antes del quinto "por qué", detener el análisis.
        Evidencias Obligatorias: Ninguna causa debe ser genérica (rechazar "error humano" sin explicar contexto operativo).

        Plan de Acción:

        Trazabilidad: Cada acción debe responder a un eslabón específico de la cadena de análisis (ej.: Si el Porqué 3 fue "falta de capacitación en X procedimiento", la acción debe ser "capacitación enfocada en X").
        Referencias a Incidentes Pasados: Solo incluir si coinciden en causa raíz, contexto operativo y resultado.
        Los planes de acción siempre deben ser los minimos posibles, mas de 4 son inaceptables.
        Solo generar mas de uno en caso que sea estrictamente necesario basado en el analisis de causas y en la conclusion.

        Solo incluir mas de un plan de acción en caso que el analisis de causa raiz y los 5 porques, requieran mas de un plan de acción

        Formato de Salida (Estricto):

        Análisis de los 5 Porqués:  
        - Por qué 1 [Pregunta]: [Causa directa + dato operativo relevante (ej.: hora, ubicación)]  
        - Por qué 2 [Pregunta]: [Causa subyacente + factor contextual (ej.: turno corto de personal)]  
        ... (continuar solo si es necesario)  

        Causa Raíz:  
        [Nombre exacto de la causa de la lista oficial. Prohibido modificar términos.]  

        Conclusión:  
        [Resumen cronológico con: 1) Evento detonante, 2) Factores contribuyentes (tiempo/proceso/persona), 3) Relación clara con la causa raíz oficial.]  

        Plan de Acción:  
        - [Acción 1: Medible (ej.: "Revisar checklist de inspección antes de las 17:00")]  
        - [Acción 2: Solo si corresponde (ej.: "Actualizar manual sección 4.2 con protocolo de parqueo nocturno")] 

        Ejemplo Válido (Segmento):
        Análisis de los 5 Porqués:  
        - Porque no se realizo la carga correcta de la aeronave?: El pallet PF-789 se dañó durante la carga en Doca 5 (14:30).  
        - Porque el pallet PF-789 se daño durante la carga?: El operador no usó la guía de carga del Manual T-7.  
        - Porque el operador no uso la guia del Manual T-7?: El operador ingresó hace 3 días y no recibió capacitación en T-7 por urgencia en turno nocturno.  
        Causa Raíz: "Capacitación incompleta en procedimientos críticos".  
        Plan de Acción:  
        - 1. Auditoría semanal de capacitaciones pendientes en turnos nocturnos (Registro en SAP).

        Rechazo de Análisis Incorrecto:
        Si se propone una causa fuera de la lista oficial (ej.: "Falta de motivación del equipo") o acciones no rastreables (ej.: "Reforzar la supervisión" sin detalle), el análisis se rechaza.

        Notas Finales:

        Priorizar datos de la descripción: Si el evento menciona "retraso en el parqueo a las 20:00", el análisis debe integrar hora y ubicación.
        Causas oficiales: Solo usar términos estandarizados (ej.: "Falla en protocolo de seguridad" ➔ no "Error en paso 3 del protocolo").
        Usar incidentes historicos como referencia, si solo presentan un plan de acción, generar solo un plan de acción, siempre siguiente la estrutura y analisis de incidentes historicos.
        No incluyas ningun tipo de fecha o responsables en los planes de acción
        Los planes de acción deben ser entre 1 y 4, priorizar 1 plan de acción relacionado con la causa raiz, máximo 4, pero priorizando siempre un plan de acción que mitigue el problema de base
        Los planes de acción deben ser medibles ej: [Acción 1: Medible (ej.: "Revisar checklist de inspección antes de las 17:00")]  
        En caso que la causa raiz del incidente historico sea no procede no la tenga en cuenta en tu generación como ejemplo.
        """

        human_prompt="""
        Este es el incidente para el cual debes generar el informe:

        ##########################
        Incidente: 
        {descripcion_hallazgo}
        ##########################

        Utiliza el siguiente incidente historico como referencia para la generación

        ##########################
        Incidenete historico de referencia: 
        {ejemplos_similares}
        ##########################

        Esta es la lista de causas raices de la que debes escoger, solo debes escoger una de las indicadas de la lista:

        ##########################
        Causas raices:
        {causas_raiz}
        ##########################

        Esta es información adicional relacionada a manuales de procedimientos:

        ##########################
        Procedimiento segun manual:
        {manuales}
        ##########################

        PIENSA TU REPUESTA PASO A PASO
        """
    
        # Convertir el diccionario de first_element a una representación legible para el prompt
        ejemplos_similares = "\n\n\n".join([f"{key}: {value}" for key, value in first_element.items()])
    
        # Definir el template de prompt con formato optimizado
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    system_prompt
                ),
                (
                    "human",
                    human_prompt
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
        model=open_ai_model,
        api_key=openai_api_key,
        max_tokens=2000,
        temperature=0.1
    )

    # system_prompt = """
    # Tienes que corregir y mejorar la siguiente respuesta que incluye ejemplos previos, evento, análisis de causa, causa raíz y plan de acción. Sigue estas instrucciones cuidadosamente:

    #             - Mantén el **formato de la respuesta exactamente como está**, respetando la numeración y la estructura. **No se debe omitir ninguna sección**.
    #             - La respuesta debe incluir todas las secciones en este **orden exacto**: 
    #                 - Ejemplos previos:
    #                 - Evento:
    #                 - Análisis de los 5 Porqués:
    #                 - Por qué 1:
    #                 - Por qué 2:
    #                 - Por qué 3:
    #                 - Por qué 4:
    #                 - Por qué 5:
    #                 - Causa raíz:
    #                 - Conclusión:
    #                 - Plan de acción:
                
    #             - **No modifiques los ejemplos previos**. Estos deben permanecer exactamente como están, sin cambios.
    #             - Si el feedback menciona cambios en un "Por qué" específico (por ejemplo, "modificar Por qué 2"), **solo modifica esa parte y deja los demás "Por qué" sin cambios**.
    #             - Si el feedback menciona cambios en la "Causa raíz", **realiza la modificación solo en esa sección** según lo indicado en el feedback.
    #             - Si el feedback menciona cambios en el "Plan de acción", **aplícalos solo a esa sección**, sin modificar el análisis de causa ni la conclusión.
    #             - Si el feedback menciona cambios en la "Conclusión", **realiza solo esas modificaciones** y deja el resto de la respuesta intacto.
    #             - Si no se mencionan cambios para un "Por qué", "Plan de acción", "Causa raíz" o "Conclusión", **no los modifiques**.
    #             - Asegúrate de mantener **la estructura exacta** de la respuesta, **sin agregar ni eliminar elementos**, y **sin alterar el orden**.

    #             Respuesta Original: {original_response}
    #             Feedback: {feedback}
    # """

    system_prompt="""
    Objetivo:
    Generar correcciones y mejoras sobre una respuesta que contiene ejemplos previos, evento, análisis de causa, causa raíz y plan de acción. 
    El feedback debe garantizar que el análisis sea preciso, rastreable y basado en la lista oficial de causas raíz.

    Instrucciones Detalladas:

    - Mantén el formato exacto de la respuesta original.
    - Respetar la numeración y estructura de la respuesta.
    - No omitir ninguna sección de la respuesta original.
    - No debes modificar la causa raíz a menos que el feedback así lo indique.
    - No aumentar el número de planes de acción. Si es necesario, complementar o ajustar los ya existentes.

    Estructura de la respuesta corregida:

    1. Análisis de los 5 Porqués: (Solo modificar si el feedback lo indica, asegurando trazabilidad y evidencia operativa)
    2. Causa raíz: (Modificar solo si el feedback lo indica y asegurando alineación con la lista oficial de causas raíz)
    3. Conclusión: (Modificar solo si el feedback lo indica)
    4. Plan de acción: (Modificar solo si el feedback lo menciona. No agregar más planes de acción, sino mejorar los existentes.)

    Criterios de Corrección:
    ✅ Corrección de errores en la respuesta:

    - Si la causa raíz no está en la lista oficial, corregirla.
    - Si un "Por qué" es demasiado genérico o sin evidencia, detallarlo.
    - Si un Por qué necesita más contexto, ajustarlo.
    - Si el plan de acción no está alineado con el análisis de los 5 Porqués, corregirlo.
    - No generar más de 3 planes de acción; en su lugar, mejorar los existentes.
    - No modificar la causa raíz a menos que el feedback lo indique explícitamente.
    - Los planes de accion generados nunca deben tener responsable, fecha de entrega y evidencia.
    - Analiza el numero de planes de acción, si hay 1 plan de acción y el usuario solicita un plan de acción adicional, debes generar solo dos planes de accion.
    - Solo generar el numero de planes de acción que diga el usuario, ejemplo: Si el feedback es "agrega un plan de acción adicional" solo debes agregar 1 plan de acción

    ✅ Asegurar rastreabilidad:

    - Cada "Por qué" debe estar claramente conectado con el anterior.
    - El plan de acción debe vincularse directamente con la causa raíz.

    ✅ Rechazo de análisis incorrecto:

    - Si la causa raíz está fuera de la lista oficial, corregirla y justificar el cambio.
    - Si el análisis es vago o genérico (ej.: "error humano" sin contexto), reformularlo con datos operativos.
    - Si el plan de acción es demasiado genérico (ej.: "reforzar supervisión" sin detalle), hacerlo medible y rastreable.

    Formato de Feedback Generado:
    Corrección de Respuesta:
    (Aquí se genera la respuesta corregida, reflejando todos los cambios del feedback en el análisis de los 5 Porqués, la causa raíz y el plan de acción, si es necesario.)

    Se aplicaron las siguientes modificaciones:

    ✅ Análisis 5 Porqués: (Explicación breve de lo corregido, si aplica)
    ✅ Causa raíz: (Cambio y justificación, si aplica)
    ✅ Plan de acción: (Ajustes realizados, si aplica)

    Resumen de Ajustes:
    (Explicación clara de qué cambios se hicieron y por qué, asegurando coherencia con el análisis lógico.)
    """

    human_prompt="""
    Este fue el informe que se genero anteriormente:

    ###################
    Informe inicial:
    {original_response}
    ###################

    Usa este evento historico como referencia:

    ###################
    Informe historico de referencia:
    {informe_ejemplo}
    ###################

    Usa este feedback para mejorar el informe: 

    ###################
    Feedback:
    {feedback}
    ###################

    Esta es la lista de causas raices de la que debes escoger, solo debes escoger una de las indicadas de la lista:

    ##########################
    Causas raices:
    {causas_raiz}
    ##########################

    Piensa tu respuesta paso a paso
    """
    
    
    # Se crea el prompt asegurando que la estructura exacta debe ser mantenida
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", human_prompt)
        ]
    )

    # Creamos la cadena de llamada al modelo
    chain = prompt | llm

    # Invocamos el modelo para procesar la respuesta con el feedback
    response = chain.invoke({"original_response": item["response"], "feedback": item["feedback"], 
                             "informe_ejemplo": item["ejemplos_similares"],
                             "causas_raiz": item["causa_raiz"]})
    
    # Regresamos el contenido corregido
    return response.content


