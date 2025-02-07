import boto3
import json
import json

class Manuales: 

    def __init__(self, descripcion_evento):
        self.descripcion_evento = descripcion_evento
        self.sagemaker_runtime = boto3.client("sagemaker-runtime", region_name="us-east-1")

    def run(self):

        payload = {"descripcion_evento": self.descripcion_evento}

        
        response = self.sagemaker_runtime.invoke_endpoint(
            EndpointName="visionrag-endpoint",
            ContentType="application/json",
            Body=json.dumps(payload),
        )

        return json.loads(response["Body"].read().decode("iso-8859-1"))
        # result = response["Body"].read().decode("utf-8")
        # print(result)

        
