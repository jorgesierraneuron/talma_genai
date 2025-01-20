import json
from fastapi import FastAPI, HTTPException
from mangum import Mangum
import uvicorn
from models import SimilarityRequest
from utils import search_filtered, search_unfiltered, generate_cause_analysis
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers=["*"],
)

handler = Mangum(app)

@app.post("/similarity_search_filtered")
def similarity_search_filtered(request: SimilarityRequest):
    try:
        
        print("Busqueda de Similaridad")

        result = search_filtered(request.descripcion_hallazgo)
        result_json = json.dumps(result, indent=4, ensure_ascii=False)
        first_element = result_json[0]

        print("Generacion Analisis de Causas")

        response = generate_cause_analysis(first_element, request.descripcion_hallazgo)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la búsqueda con filtro: {str(e)}")


@app.post("/similarity_search_unfiltered")
def similarity_search_unfiltered(request: SimilarityRequest):
    try:
    
        print("Busqueda de Similaridad")

        result = search_unfiltered(request.descripcion_hallazgo)
        result_json = json.dumps(result, indent=4, ensure_ascii=False)
        first_element = result_json[0]

        print("Generacion Analisis de Causas")

        response = generate_cause_analysis(first_element, request.descripcion_hallazgo)
        
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la búsqueda sin filtro: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, port=8000)