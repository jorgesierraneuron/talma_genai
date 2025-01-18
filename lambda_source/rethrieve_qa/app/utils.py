import re
from app.connections import get_vector_store

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
