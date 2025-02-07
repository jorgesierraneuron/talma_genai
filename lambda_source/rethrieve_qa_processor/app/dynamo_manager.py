import boto3
from botocore.exceptions import BotoCoreError, ClientError
import hashlib

class DynamoDBManager:
    def __init__(self, table_name, region_name='us-east-1'):
        self.dynamodb = boto3.resource('dynamodb', region_name=region_name)
        self.table = self.dynamodb.Table(table_name)

    def upload_item(self, item_data):
        """
        Upload an item to DynamoDB.
        :param pk: Primary key value.
        :param item_data: Dictionary containing item attributes.
        """
        try:
            #item_data['pk'] = pk  # Ensure PK is included
            self.table.put_item(Item=item_data)
            return {"message": "Item uploaded successfully"}
        except (BotoCoreError, ClientError) as e:
            return {"error": str(e)}

    def retrieve_item(self, pk):
        """
        Retrieve an item from DynamoDB.
        :param pk: Primary key value.
        :return: Dictionary containing the item data or an error message.
        """
        try:
            response = self.table.get_item(Key={'id_generation': pk})
            return response.get('Item', {})
        except (BotoCoreError, ClientError) as e:
            return {"error": str(e)}

    def update_item(self, pk, update_data):
        """
        Update an item in DynamoDB.
        :param pk: Primary key value.
        :param update_data: Dictionary containing attributes to update.
        """
        try:
            update_expression = "SET " + ", ".join(f"#{k} = :{k}" for k in update_data.keys())
            expression_attribute_names = {f"#{k}": k for k in update_data.keys()}
            expression_attribute_values = {f":{k}": v for k, v in update_data.items()}
            
            self.table.update_item(
                Key={'id_generation': pk},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values
            )
            return {"message": "Item updated successfully"}
        except (BotoCoreError, ClientError) as e:
            return {"error": str(e)}
        
    @staticmethod
    def generate_unique_id(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:8]  # Take the first 8 characters





if __name__ == "__main__":

    

    dynamo_manager = DynamoDBManager("generation_talma_genai")

    # Example usage
    text = "Some unique text"
    unique_id = dynamo_manager.generate_unique_id(text)
    print(unique_id)

    new_item = {"descripcion_hallazgo": "aeropuerto BOG y con el cliente JET SMART , El día de hoy el personal de Talma olvidó correr parte de la escalera que se acopla al avion cerca de la puerta, dejando un espacio que puede causar algún accidente o incidente con los pasajeros. Ninguno en rampa se percató para corregir el error y el desembarque se hizo así en su totalidad.",
                "causa_raiz": "Área de trabajo/entorno: Congestión de tráfico, Área de trabajo/entorno: Vientos fuertes, Área de trabajo/entorno: Peligro de tropiezo, Área de trabajo/entorno: Marcas en rampas, Área de trabajo/entorno: Nieve/hielo, Área de trabajo/entorno: Ruido, Área de trabajo/entorno: Referencia visual, Área de trabajo/entorno: Lluvia, Área de trabajo/entorno: Tormenta de polvo, Área de trabajo/entorno: Juicio espacial, Área de trabajo/entorno: Rayos, Área de trabajo/entorno: Calor (temperatura ambiente), Área de trabajo/entorno: Superficie resbaladiza, Equipo/Herramientas: Mal funcionamiento del equipo (verificado), Equipo/Herramientas: Uso inadecuado del equipo, Equipo/Herramientas: Lista de verificación previa a la operación no completada, Equipo/Herramientas: No se proporcionaron instrucciones, Equipo/Herramientas: Mantenimiento preventivo no completado, Equipo/Herramientas: Uso incorrecto del equipo, Equipo/Herramientas: No se retiró del servicio el equipo defectuoso, Equipo/Herramientas: Se pasó por alto el dispositivo de seguridad, Equipo/Herramientas: Uso de equipo inseguro o poco confiable, Equipo/Herramientas: Uso a velocidades excesivas, Equipo/Herramientas: Uso de equipo difícil, Equipo/Herramientas: No se recibió capacitación sobre el equipo, Equipo/Herramientas: No se dispuso del equipo adecuado, Equipo/Herramientas: Problema de diseño, Equipo/Herramientas: No se estaba familiarizado con el equipo, Comunicación: Informe de turno, Comunicación: Mensaje incompleto, Comunicación: Comunicación, tierra a/desde cabina de mando, Comunicación: Mensaje confuso, Comunicación: Comunicación, tierra a/desde tierra, Comunicación: Señales manuales, Comunicación: Comunicación, supervisor a/desde agente, Ergonomía: Repetitivo/monótono, Ergonomía: Difícil de agarrar, Ergonomía: Esfuerzos enérgicos, Ergonomía: Larga duración, Ergonomía: Arrodillarse/doblarse/agacharse, Ergonomía: Calor/frío, Ergonomía: Torsión, Ergonomía: Posición incómoda, Ergonomía: Vibración, Ergonomía: Estrés por contacto, Procedimientos/Tareas/Capacitación: Falta de habilidad o capacitación, Procedimientos/Tareas/Capacitación: Procedimiento no comunicado, Procedimientos/Tareas/Capacitación: No se planificó la tarea, Procedimientos/Tareas/Capacitación: No estaba familiarizado con el procedimiento, Procedimientos/Tareas/Capacitación: Tarea demasiado difícil, Procedimientos/Tareas/Capacitación: El procedimiento no anticipó el peligro, Procedimientos/Tareas/Capacitación: Se desvió del procedimiento, Procedimientos/Tareas/Capacitación: La tarea fomenta la desviación del procedimiento, Procedimientos/Tareas/Capacitación: Procedimiento no documentado, Procedimientos/Tareas/Capacitación: Nueva tarea o cambio de tarea, Procedimientos/Tareas/Capacitación: Procedimiento no capacitado, Procedimientos/Tareas/Capacitación: Nueva herramienta o equipo, Procedimientos/Tareas/Capacitación: Procedimiento o capacitación no reforzados, Factores individuales: Salud física (audición/vista), Factores individuales: Pérdida de memoria (olvido), Factores individuales: Fatiga, Factores individuales: Conciencia situacional (no identificó el peligro), Factores individuales: Presión de grupo, Factores individuales: Estrés, Factores individuales: Tamaño o fuerza corporal, Factores individuales: Limitaciones de tiempo, Factores individuales: Evento personal (problema familiar, accidente de automóvil), Factores individuales: Experiencia laboral/tarea, Factores individuales: Distracción/interrupción en el lugar de trabajo, Liderazgo/Supervisión/Organización: Planificación/Organización de tareas, Liderazgo/Supervisión/Organización: Responsabilidad no asignada, Liderazgo/Supervisión/Organización: Priorización del trabajo, Liderazgo/Supervisión/Organización: No se comunicó, Liderazgo/Supervisión/Organización: Delegación de tareas, Liderazgo/Supervisión/Organización: No coordinó, Liderazgo/Supervisión/Organización: Actitud o expectativas poco realistas, Liderazgo/Supervisión/Organización: Gestión de la carga de trabajo, Liderazgo/Supervisión/Organización: Nivel de supervisión o disponibilidad, Factores organizacionales: Calidad de la gestión/ingeniería/planificación del soporte, Factores organizacionales: Proceso de trabajo, Factores organizacionales: Políticas de la empresa, Factores organizacionales: Personal insuficiente, Factores organizacionales: Cambio/reestructuración corporativa, Factores organizacionales: Las normas locales permiten conductas de riesgo, Factores organizacionales: Acción sindical, Factores organizacionales: Práctica normal",
                "status": "initiated"}
    
    new_item["id_generation"] = dynamo_manager.generate_unique_id(new_item["descripcion_hallazgo"])
    
    
    print(dynamo_manager.upload_item(new_item))


    # print(dynamo_manager.retrieve_item("1"))

    # update_item = {
    #     "descripcion_evento": "ABC",
    #     "status": "running",
    #     "response": "ABC"
    #     }
    
    # print(dynamo_manager.update_item("1", update_item))
    

