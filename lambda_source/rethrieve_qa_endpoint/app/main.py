import json
from fastapi import FastAPI, HTTPException
from mangum import Mangum
import uvicorn
from models import SimilarityRequest, GetResult
from fastapi.middleware.cors import CORSMiddleware
from dynamomanager import DynamoDBManager
from utils import send_sns_message
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
        if not request.feedback:
            descripcion_hallazgo = request.descripcion_hallazgo
            id_generation = dynamo_manager.generate_unique_id(descripcion_hallazgo)

            item = {
                "id_generation": id_generation,
                "descripcion_hallazgo": descripcion_hallazgo,
                "causa_raiz": request.causa_raiz,
                "status": "initiated"
            }

            print(dynamo_manager.upload_item(item))

            message = {
                "id_generation": id_generation
            }

            print(send_sns_message("arn:aws:sns:us-east-1:242201272670:test_rethrieve_qa", message))
            
            return {
                "upload": "success",
                "item": item
            }
        
        else:
            item = dynamo_manager.retrieve_item(request.id_generation)
            if not item:
                return {"error": "Item no encontrado en DynamoDB"}
            
            item["feedback"] = request.feedback
            update_response = dynamo_manager.update_item(request.id_generation, {"feedback": request.feedback})
            print(update_response)

            message = {
                "id_generation": request.id_generation
            }

            sns_response = send_sns_message("arn:aws:sns:us-east-1:242201272670:test_rethrieve_qa", message)
            print(sns_response)

            return {
                "update": "success",
                "item": item
            }

    except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    
        
@app.post("/get_result")
def get_result(result: GetResult):

    try: 
        item = dynamo_manager.retrieve_item(result.id_generation)
        return {
                "result": item
        }
    except Exception as e:
       raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# if __name__ == "__main__":
#     uvicorn.run(app, port=8000)
