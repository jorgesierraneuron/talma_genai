import json
from fastapi import FastAPI, HTTPException
from mangum import Mangum
import uvicorn
from models import SimilarityRequest
from utils import search_unfiltered, generate_cause_analysis_and_action_plan, apply_feedback
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers=["*"],
)

handler = Mangum(app)

@app.post("/similarity_search_unfiltered")
def similarity_search_unfiltered(request: SimilarityRequest):
    try:
        print("Búsqueda de Similaridad")
        result = search_unfiltered(request.descripcion_hallazgo)
        
        if "resultados_de_busqueda" not in result or not result["resultados_de_busqueda"]:
            return {"mensaje": "No se encontraron resultados similares."}
        
        first_element = result["resultados_de_busqueda"][0]
        print("Generación Informacion para Reporte de Quejas")
        response = generate_cause_analysis_and_action_plan(first_element, request.descripcion_hallazgo, request.causa_raiz)
        
        # Verificar si se proporciona feedback para realizar correcciones
        if request.feedback:
            print("Aplicando feedback a la respuesta generada")
            response = apply_feedback(response, request.feedback)
        
        # Convertir la respuesta en un formato JSON adecuado, con campos estructurados
        return {"respuesta": response}  
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la búsqueda: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, port=8000)
