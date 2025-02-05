import json
from fastapi import FastAPI, HTTPException
from mangum import Mangum
import uvicorn
from models import SimilarityRequest
from utils import search_filtered, search_unfiltered, generate_cause_analysis, apply_feedback
from fastapi.middleware.cors import CORSMiddleware
from vision_rag import VisionRAG

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers=["*"],
)

handler = Mangum(app)

vision_rag = VisionRAG()

@app.post("/similarity_search_filtered")
def similarity_search_filtered(request: SimilarityRequest):
    try:
        print("Búsqueda de Similaridad")
        result = search_filtered(request.descripcion_hallazgo)

        manuales_info = vision_rag.run(request.descripcion_hallazgo)

        print(f"info manuales: {manuales_info}")
        
        if "resultados_de_busqueda" not in result or not result["resultados_de_busqueda"]:
            return {"mensaje": "No se encontraron resultados similares con los filtros aplicados."}
        
        first_element = result["resultados_de_busqueda"][0]
        print("Generación Análisis de Causas")
        response = generate_cause_analysis(first_element, request.descripcion_hallazgo)
        
        # Verificar si se proporciona feedback para realizar correcciones
        if request.feedback:
            print("Aplicando feedback a la respuesta generada")
            response = apply_feedback(response, request.feedback)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la búsqueda con filtro: {str(e)}")

@app.post("/similarity_search_unfiltered")
def similarity_search_unfiltered(request: SimilarityRequest):
    try:
        print("Búsqueda de Similaridad")
        result = search_unfiltered(request.descripcion_hallazgo)
        
        if "resultados_de_busqueda" not in result or not result["resultados_de_busqueda"]:
            return {"mensaje": "No se encontraron resultados similares."}
        
        first_element = result["resultados_de_busqueda"][0]
        print("Generación Análisis de Causas")
        response = generate_cause_analysis(first_element, request.descripcion_hallazgo)
        
        # Verificar si se proporciona feedback para realizar correcciones
        if request.feedback:
            print("Aplicando feedback a la respuesta generada")
            response = apply_feedback(response, request.feedback)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la búsqueda sin filtro: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, port=8000)