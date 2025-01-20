import json
from fastapi import FastAPI, HTTPException
from mangum import Mangum
from models import SimilarityRequest
from utils import search_filtered, search_unfiltered, generate_cause_analysis

app = FastAPI()

@app.get("/similarity_search_filtered")
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


@app.get("/similarity_search_unfiltered")
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

handler = Mangum(app)