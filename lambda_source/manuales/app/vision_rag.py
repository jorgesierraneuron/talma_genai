from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd
from datasets import load_dataset, Dataset
import re
from datasets import Dataset
from PIL import Image
from io import BytesIO
from colpali_engine.models import ColPali, ColPaliProcessor
import torch
from qdrant_client import QdrantClient, models
from qdrant_client.models import Filter, FieldCondition, MatchValue, SearchParams, QuantizationSearchParams
#from transformers import ColPali, ColPaliProcessor
import base64
from openai import OpenAI
from config import qdrant_key,qdrant_url,openai_api_key

class ChainManuales: 

    

    llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=openai_api_key
    )

    prompt_manuales = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Eres un operario experto en mmanuales de operación aeroportuario, basado en la descripcion de un evento y la lista de manuales disponinbles debes escoger 
            el nombre del manual correcto para el evento, manuales_disponibles: {manuales_disponibles}
            
            GUIDELINE: SOLO DEBES GENERAR EL NOMBRE EXACTO DEL MANUAL
            EN CASO DE NO EXISTIR UN MANUAL PARA LA AEROPLINEA USA MANUALES DE SAI O LASA
            """,
        ),
        ("human", "descripcion ddel evento: {descripcion_evento}"),
    ]
    )

    prompt_query_manual = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """Eres un operario experto en manuales de operación aeroportuarios, debes convertir la descripcion del evento a un texto del manual de operacion, un resumen, incluye palabras clave para una mejor 
            busqueda en el manual siempre basado en la descripicion del evento

            GUIDELINE: NO MAS DE 300 CARACTERES
            """,
        ),
        ("human", "descripcion ddel evento: {descripcion_evento}, manual a utilizar: {manual_name}"),
    ]
    )


    def __init__(self):

        self.chain_manual_name = self.prompt_manuales | self.llm
        self.chain_query_manuales = self.prompt_query_manual | self.llm
        



class VisionRAG: 

    openai_client = OpenAI(api_key=openai_api_key)

    chain_manuales = ChainManuales()

    qdrant_client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_key,
    )

    # # Initialize ColPali model and processor
    # model_name = (
    #     "vidore/colpali-v1.3"  # Use the latest version available
    # )
    # colpali_model = ColPali.from_pretrained(
    #     model_name,
    #     torch_dtype=torch.bfloat16,
    #     device_map="mps",  # Use "cuda:0" for GPU, "cpu" for CPU, or "mps" for Apple Silicon
    # )

    # colpali_processor = ColPaliProcessor.from_pretrained(
    #     "vidore/colpaligemma-3b-pt-448-base"
    # )

    # Load from local paths
    colpali_model = ColPali.from_pretrained(
        "./local_model",  # Path to downloaded model
        torch_dtype=torch.bfloat16,
        device_map="auto"  # Auto-detect CPU/GPU
    )

    colpali_processor = ColPaliProcessor.from_pretrained("./local_processor")





    df_markdown = pd.read_csv("manuales_guia.csv").to_markdown()

    def __base64_image(self,dataset_path, index):
        """
        Lee un dataset local de Hugging Face y muestra una imagen basada en un índice.
        
        Args:
            dataset_path (str): Ruta al directorio del dataset guardado.
            index (int): Índice de la imagen que se desea mostrar.
            
        Returns:
            None
        """
        try:
            # Cargar el dataset desde disco
            dataset = Dataset.load_from_disk(dataset_path)
            print(f"Dataset cargado con {len(dataset)} registros.")
            
            # Verificar si el índice es válido
            if index < 0 or index >= len(dataset):
                print(f"Índice inválido. El dataset contiene {len(dataset)} registros.")
                return
            
            # Obtener la imagen en formato bytes
            image_data_bytes = dataset[index]["image"]
            
            # # Convertir los bytes en un objeto PIL Image
            # image = Image.open(BytesIO(image_data_bytes))
            
            # # Mostrar la imagen
            # image.show()
            # print(f"Mostrando la imagen en el índice {index}.")
        
        except Exception as e:
            print(f"Error al mostrar la imagen: {e}")

        return image_data_bytes
    
    def __search_qdrant(self,query, collection_name, manual_name): 
        query_text = query
        with torch.no_grad():
            batch_query = self.colpali_processor.process_queries([query_text]).to(
                self.colpali_model.device
            )
            query_embedding = self.colpali_model(**batch_query)
        
        multivector_query = query_embedding[0].cpu().float().numpy().tolist()

        # Define the filter
        filter_condition = models.Filter(
            must=[
                models.FieldCondition(
                    key="nombre_documento",
                    match=models.MatchValue(value=manual_name),
                )
            ]
        )

        # Search with the filter
        search_result = self.qdrant_client.query_points(
            collection_name=collection_name,
            query=multivector_query,
            limit=1,
            timeout=100,
            #query_filter=filter_condition,
            search_params=SearchParams(
                quantization=QuantizationSearchParams(
                    ignore=False,
                    rescore=True,
                    oversampling=2.0,
                )
            ),
            
        )
        
        #self.qdrant_client.close()
        return search_result.points[0].id
    
    @staticmethod
    def __bytes_to_base64(bytes_imagen): 
        base64_string = base64.b64encode(bytes_imagen).decode("utf-8")
        return base64_string
    
    def __get_response(self, query_manuales, descripcion_evento, base64_image):
  
        text = f"""
        Eres un experto operario aeroportuario, que utiliza los manuales de operación para generar las mejores practicas

        Usa la informacion que encuentras en la imagen para dar contexto sobre este procedimiento: 

        {query_manuales}

        Como contexto el incidente presentado fue el siguiente: 

        {descripcion_evento}

        Solo debes generar el procedimiento adecuando a seguir segun la imagen. 
        """

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": text,
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            ],
        )
        
        return response.choices[0].message.content

    def __get_manual_name_query_manuals(self, query): 
        

        manual_name = self.chain_manuales.chain_manual_name.invoke(
            {
                "manuales_disponibles": self.df_markdown,
                "descripcion_evento": query,
            }
        )

        query_manual = self.chain_manuales.chain_query_manuales.invoke(
                            {
                                "manuales_disponibles": self.df_markdown,
                                "descripcion_evento": query,
                                "manual_name": manual_name.content
                            }
                        )
        
        return query_manual.content,manual_name.content
    
    def run(self, query): 


        query_manual, manual_name = self.__get_manual_name_query_manuals(query)

        idx = self.__search_qdrant(query_manual, "manuales_talma_dev",manual_name)
        
        print(f"Manual name: {manual_name}")


        manual_name_dataset =  re.sub(r"(REV[^.]*)\..*", r"\1", manual_name)

        path = f"datasets_local/{manual_name_dataset}"
        
        bytes_image = self.__base64_image(path, idx)

        base64_image = self.__bytes_to_base64(bytes_image)

        return self.__get_response(query_manual, query, base64_image)


# def handler():

#     import os
#     import logging

#     logging.basicConfig(level=logging.INFO)

#     # Read input from environment
#     descripcion_evento = os.getenv("DESCRIPCION_EVENTO", "No input")

#     # Log the result (Lambda will retrieve from CloudWatch Logs)
#     logging.info(f"Processed Event: {descripcion_evento}")
    
#     vision_rag = VisionRAG()

#     # descripcion_evento = """
#     # INCUMPLIMIENTO DE LAS SEÑALES DE LLEGADA (LINTERNAS O VARAS OPERATIVAS 2 X CADA PUNTA DE ALA Y PARQUEADOR, TOTAL 6), CONEXIÓN DE EQUIPOS (GPU) Y SEÑALES DE CONEXIÓN.

#     # AVIANCA
#     # """

#     logging.info(vision_rag.run(descripcion_evento))


# if __name__ == "__main__":
#     handler()
