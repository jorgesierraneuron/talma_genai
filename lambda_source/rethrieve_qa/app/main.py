from fastapi import FastAPI, HTTPException
from mangum import Mangum
from app.models import SimilarityRequest
from app.utils import search_filtered, search_unfiltered

app = FastAPI()

@app.get("/similarity_search_filtered")
def similarity_search_filtered(request: SimilarityRequest):
    try:
        return search_filtered(request.descripcion_hallazgo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la búsqueda con filtro: {str(e)}")

@app.get("/similarity_search_unfiltered")
def similarity_search_unfiltered(request: SimilarityRequest):
    try:
        return search_unfiltered(request.descripcion_hallazgo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la búsqueda sin filtro: {str(e)}")

handler = Mangum(app)