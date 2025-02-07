import boto3
import base64

def get_secret(secret_name, region_name):
    '''
        Obtiene un secreto en base al nombre (o el arn) y la region 

        Parameters:
        secret_name(str): Caso el secreto se encuentre en la misma cuenta, con pasarle el nombre del secreto basta, si el secreto existe en otra cuenta, hay que pasar el arn completo
        region(str): Region en la cual el secreto fue creado. 
    '''
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    get_secret_value_response = client.get_secret_value(
        SecretId=secret_name
    )

    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
    else:
        secret = base64.b64decode(get_secret_value_response['SecretBinary'])

    return secret

#-- Obtencion Credenciales ---#

talma_creds = get_secret("talma_project_creds", "us-east-1")
talma_creds = eval(talma_creds)

# --- Creds NEO4J ---#

neo4j_username = talma_creds["neo4j_username"]
neo4j_passwd = talma_creds["neo4j_passwd"]
neo4j_url = talma_creds["neo4j_url"]

# --- Creds Api OpenAi ---#

openai_api_key = talma_creds["openai_api_key"]

# --- Parámetros Nodos ---#

index_name = "incidente_index_2"
text_node_property = "descripcion_hallazgo"
