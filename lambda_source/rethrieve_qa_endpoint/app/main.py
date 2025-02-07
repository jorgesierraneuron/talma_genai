import json
from fastapi import FastAPI, HTTPException
from mangum import Mangum
import uvicorn
from models import SimilarityRequest, GetResult
from fastapi.middleware.cors import CORSMiddleware
from dynamomanager import DynamoDBManager

app = FastAPI()

dynamo_manager=DynamoDBManager("generation_talma_genai")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=["*"],
    allow_headers=["*"],
)

handler = Mangum(app)

@app.post("/similarity_search")
def similarity_search_unfiltered(request: SimilarityRequest):

    try: 
        descripcion_hallazgo = request.descripcion_hallazgo
        id_generation = dynamo_manager.generate_unique_id(descripcion_hallazgo)

        item = {
            "id_generation": id_generation,
            "descripcion_hallazgo": descripcion_hallazgo,
            "causa_raiz": request.causa_raiz,
            "status": "initiated"
        }

        print(dynamo_manager.upload_item(item))
        
        return item 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/get_result")
def similarity_search_unfiltered(result: GetResult):

    try: 
        item = dynamo_manager.retrieve_item(result.id_generation)
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, port=8000)
