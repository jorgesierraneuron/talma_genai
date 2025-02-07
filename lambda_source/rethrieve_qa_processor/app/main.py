import json
from fastapi import FastAPI, HTTPException
from mangum import Mangum
import uvicorn
from models import SimilarityRequest
from utils import search_unfiltered, generate_cause_analysis_and_action_plan, apply_feedback
from dynamo_manager import DynamoDBManager
from manuales import Manuales



def handler(event, context = ""):
    
    
    dynamo_manager = DynamoDBManager("generation_talma_genai")
    id_generation = event["id_generation"]

    item = dynamo_manager.retrieve_item(id_generation)

    # Update Status

    item["status"] = "running"
    item.pop("id_generation")
    print(dynamo_manager.update_item(id_generation,item))

    manuales=Manuales(item["descripcion_hallazgo"])
    
    try:    
        

        if item.get("feedback"):
            print("Aplicando feedback a la respuesta generada")
            # se le debe pasar el id del incidente y con eso, trae la respuesta anterior la modifique y la vuelve a subir a dynamo, con la fecha de generación.
            # OJO PENDIENTE 

            feedback = item["feedback"]

            response = apply_feedback(item)

            item["response"] = response
            item["status"] = "completed"

            print(dynamo_manager.update_item(id_generation,item))

            return {"respuesta": f"feedback aplied, feedback: {feedback}"} 
            
    

        print("Búsqueda de Similaridad")
        result = search_unfiltered(item["descripcion_hallazgo"])

        print("Obteniendo info de los manuales")
        result_manuales = manuales.run()

        item["info_manuales"] = result_manuales["response"]
        
        if "resultados_de_busqueda" not in result or not result["resultados_de_busqueda"]:
            return {"mensaje": "No se encontraron resultados similares."}
        
        first_element = result["resultados_de_busqueda"][0]
        print("Generación Informacion para Reporte de Quejas")
        response = generate_cause_analysis_and_action_plan(first_element, item["descripcion_hallazgo"], item["causa_raiz"], result_manuales["response"])
        
        # update the item in dynamo with the response

        item["status"] = "completed"
        item["response"] = response["response"]
        item["ejemplos_similares"] = response["ejemplos_similares"]

        print(dynamo_manager.update_item(id_generation,item))


        return {"status": f"upload response {id_generation}"}  
    
    except Exception as e:
        raise e
    

if __name__ == "__main__":
    
    event = {
        "id_generation": "31f48d89"
    }

    
    print(handler(event))