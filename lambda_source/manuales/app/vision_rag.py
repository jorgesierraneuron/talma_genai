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
import logging
import io


logging.basicConfig(level=logging.INFO)

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
            """Eres un experto en manuales de operación aeroportuarios. Convierte la descripción del evento en una entrada de manual clara y precisa (máx. 300 caracteres). 
            Incluye un resumen estructurado y palabras clave relevantes para facilitar la búsqueda, siempre basado en la descripción del evento.

            Ejemplos: 
            
            1. Procedimiento para limpieza de asientos
            - Limpieza. 
            - pernoctas. 
            -insumos

            Para la limpieza de la aeronave se debe seguir estos pasos...

            2. Procedimiento carga de aeronave. 
            - Distribucion peso
            - Carga
            - Balance de carga

            El procedimiento de carga se debe iniciar...

            Debes generar queries de ese estilo pero profundizando en el procedimiento.
            NO DEBES DAR INSTRUCCIONES, SOLO PALABRAS CLAVE QUE PUEDA ENCONTRAR EN EL MANUAL
            Las palabras claves son relacionadas al procedimiento, no al evento

            Escribe un parrafo de lo que puedes encontrar en el manual
            """,
        ),
        ("human", "descripcion del evento: {descripcion_evento}, manual a utilizar: {manual_name}"),
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

            image = Image.open(io.BytesIO(image_data_bytes))

            image.show()
        
        except Exception as e:
            logging.info(f"Error al mostrar la imagen: {e}")

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
        return search_result.points[0].id, search_result.points[0].payload.get("nombre_documento")
    
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

        Tu deber es explicar cual es el procedimiento a seguir segun el manual de operación el cual encuentras en la iamgen
        """

        user_prompt = """
        Con base en la imagen dame el procedimiento que debo seguir para cumplir con el procedimiento relacionado al evento que recibiste

        Usa el procedimiento indicado en la imagen para describir el procedimiento adecuado
        NO DEBES DAR DESCRIPCIONES ADICIONALES ACERCA DEL EVENTO
        Siempre enumera los pasos y el nombre colocalo en negrita.
        """

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "text",
                            "text": text,
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_prompt,
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


        query_manual, manual_name_ia = self.__get_manual_name_query_manuals(query)

        logging.info(f"query_manual: {query_manual}")

        #idx, manual_name = self.__search_qdrant(query_manual, "manuales_talma_dev",manual_name_ia)

        idx, manual_name = self.__search_qdrant(query_manual, "manuales_talma_dev",manual_name_ia)
        
        logging.info(f"Manual name: {manual_name}")

        manual_name_dataset =  re.sub(r"(REV[^.]*)\..*", r"\1", manual_name)

        path = f"datasets_local/{manual_name_dataset}"
        
        bytes_image = self.__base64_image(path, idx)

        base64_image = self.__bytes_to_base64(bytes_image)

        return self.__get_response(query_manual, query, base64_image)


# def handler():

#     import os
#     import logging

#     logging.basicConfig(level=logging.INFO)

#     # # Read input from environment
#     # descripcion_evento = os.getenv("DESCRIPCION_EVENTO", "No input")

#     # # Log the result (Lambda will retrieve from CloudWatch Logs)
#     # logging.info(f"Processed Event: {descripcion_evento}")
    
#     vision_rag = VisionRAG()

#     descripcion_evento = """
#     aeropuerto CTG y con el cliente WINGO.

# El 10 de enero del presente año, en el Aeropuerto Internacional Rafael Núñez de Cartagena (CTG), a las 20:36 HL, y durante el desembarque de pasajeros, se produjo un contacto entre la escalera LEA052 y la puerta 4L de la aeronave, ocasionando un daño en el panel protector de esta.

# La aeronave no venía cargada adelante, lo que genera un desbalance sin tener la ventaja de peso adicional en la bodega delantera, tal como se menciona en el procedimiento
# referenciado.

# La aeronave que operaba el vuelo P57605 con destino MDE, es un B737-8 de la aerolínea P5 de matrícula HP-1714. Luego de análisis general, se logra identificar que los efectos físicos de la aeronave al desarrollar desembarque simultáneo de pasajeros, genera las siguientes afectaciones:

# 1. Se evidencia que no se cuenta con información sobre el cargue del vuelo llegando a
# CTG (LPM / LDM)
# 2. Al inspeccionar las bodegas, se identifica que la aeronave no tiene carga en la bodega
# delantera, la cual no genera contrapeso para garantizar el ground stability.
# 3. Al momento en el que se descarga la bodega trasera la aeronave pierde el equilibrio del
# ground stability aumentando la carga aerodinámica (Fuerza hacia abajo)
# 4. Se inicia desembarque simultáneo lo que genera un movimiento del centro de presión, y
# desarrollando un efecto Lift (Fuerza hacia arriba) en la aeronave.
# 5. Como resultante, estas condiciones generan el Tail Tipping y por consiguiente el
# movimiento de la aeronave que de manera directa al encontrarse acoplada la escalera
# genera el contacto y fractura del panel protector de la puerta.


# La escalera utilizada para la atención de la aeronave, identificada como LEA 052, se
# encontraba en óptimas condiciones operativas, verificadas previamente a su uso en el vuelo. Además, cumple con su programa de mantenimiento preventivo y es apta para atender aeronaves del tipo B-737.

# No se detectan desviaciones, reportes o fallas en el sistema de entrega de información por
# correo electrónico que pudiera limitar la recepción de información en el día del evento.

# La aeronave programada para vuelo P57605 se encontraba ubicada en la posición 7 del
# aeropuerto internacional Rafael Núñez. Durante la atención de la aeronave se operaba con luz artificial propia de la infraestructura del aeropuerto, operación nocturna. No se encuentran condiciones de irregularidad en la plataforma pudieran contribuir al desarrollo del evento.

# El líder a cargo del vuelo no contaba con la información de la ubicación del equipaje llegando por lo cual debe esperar el parqueo de la aeronave para realizar la revisión de las bodegas y luego proceder con el descargue de los equipajes.
# En diversas ocasiones, se ha venido solicitando al cliente la información del LDM para garantizar una planificación adecuada de recursos y coreografías alineadas a considerar los
# procedimientos de balanceo de aeronave considerados por Talma; al momento sin una confirmación formal de información para la estación CTG.

# El personal involucrado en el evento cuenta con sus turnos programados cumpliendo los
# descansos requeridos por ley, así mismo, cuenta con sus capacitaciones requeridas por la
# aerolínea, la empresa y la autoridad para desarrollar sus funciones en la operación.

#     """

#     logging.info(vision_rag.run(descripcion_evento))


# if __name__ == "__main__":
#     handler()