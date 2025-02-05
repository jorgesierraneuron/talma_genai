import json
import boto3
import base64
from io import StringIO
import pandas as pd
from neo4j import GraphDatabase
from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings

#--- Funcion para homologar nombres de columnas ---#

def homologar_columnas(df, homologacion):
    """
    Homologa los nombres de las columnas en un DataFrame según un diccionario de homologación.

    Args:
        df (pd.DataFrame): DataFrame con las columnas a homologar.
        homologacion (dict): Diccionario donde la clave es el nombre deseado
                             y el valor es una lista de nombres equivalentes.

    Returns:
        pd.DataFrame: DataFrame con las columnas renombradas.
    """
    # Crear un mapeo inverso de nombres actuales a nombres homologados
    mapeo = {}
    for nuevo_nombre, nombres_equivalentes in homologacion.items():
        for nombre in nombres_equivalentes:
            mapeo[nombre] = nuevo_nombre

    # Renombrar las columnas del DataFrame según el mapeo
    df = df.rename(columns=mapeo)

    return df

#--- Funcion para obtener credenciales ---#

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

#--- Funcion para leer un csv desde s3 ---#

def read_csv_from_s3(bucket_name, file_key):
    """
    Descarga un archivo CSV desde S3 y lo carga en un DataFrame de pandas.

    :param bucket_name: Nombre del bucket de S3.
    :param file_key: Ruta del archivo dentro del bucket.
    :return: DataFrame con los datos del CSV.
    """
    try:
        
        s3_client = boto3.client("s3")

        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)

        # Leer contenido del archivo en un DataFrame
        csv_content = response["Body"].read().decode("utf-8")  
        df = pd.read_csv(StringIO(csv_content))  

        return df

    except Exception as e:
        print(f"Error al leer el archivo CSV desde S3: {e}")
        return None

#-- Obtencion Credenciales ---#

talma_creds = get_secret("talma_project_creds", "us-east-1")
talma_creds = eval(talma_creds)

# --- Creds NEO4J ---#

neo4j_username = talma_creds["neo4j_username"]
neo4j_passwd = talma_creds["neo4j_passwd"]
neo4j_url = talma_creds["neo4j_url"]

# --- Creds Api OpenAi ---#

openai_api_key = talma_creds["openai_api_key"]

# --- Parametros Embeddings ---#

index_name= "incidente_index"
node_label= "PendingEmbedding"
text_node_properties= ["descripcion_hallazgo"]
embedding_node_property="incidente_embedding"

#--- variables auxiliares ----#

mapeo_talma = {"codigo_aeropuerto": ["BASE", "Estación"],
               "codigo_talma": ["CODIGO INTERNO", "CODIGO TALMA", "Código", "CODIGO SAC"],
               "nombre_cliente": ["Entidad que Reporta", "NOMBRE CLIENTE"],
               "analisis_causas": [ "ANALISIS DE CAUSA"],
               "plan_accion": ["ACCIONES A TOMAR PARA MINIMIZAR EL RIESGO / RESPONSABLE"]}

#-------------------- logica de lectura archivos talma ------------------------#}

bucket_name = "testtalmagenai"

paths = ["curated/calidad/PROCESADO listado_procesos750050369.csv",
         "curated/seguridad operacional/PROCESADO BASE DE DATOS UNIFICADA BOG CORREGIDA.csv",
         "curated/seguridad operacional/PROCESADO BASE DE DATOS UNIFICADA EXBOG CORREGIDA.csv"]

path_aux = "curated/calidad/PROCESADO Reporte de Accion SAC Multisede Dec 20 2024.csv"

def handler(event, context):

    try:

        #---Conexión a Neo4j y ejecución del script--------#

        driver = GraphDatabase.driver(neo4j_url, auth=(neo4j_username, neo4j_passwd))
        
        with driver.session() as session:
            
            for path in paths:

                df = read_csv_from_s3(bucket_name, path)
                df = homologar_columnas(df, mapeo_talma)
                df = df.dropna(subset=['codigo_talma'])
                df = df.astype(str).replace("nan", " ")
                df['codigo_talma'] = df['codigo_talma'].str.strip()

                #--- Blindaje unicos ---#

                repeticiones = df['codigo_talma'].value_counts()
                unicos = repeticiones[repeticiones == 1].index
                df = df[df['codigo_talma'].isin(unicos)]

                if "listado_procesos" in path:

                    #--- df listado procesos ----------#

                    df = df[df['Fuente'].isin(['Quejas y Reclamos', 'Reporte Reactivo Externo', 'Reporte Reactivo Interno', 'Reporte Proactivo Externo', 'Reporte Proactivo Interno'])]
                    df['origen_archivo'] = "Calidad"
                    df['causa_raiz'] = df[["Categorización Causa - CRITICO","Categorización Causa - IMPORTANTE", "Categorización Causa - MODERADO",
                    "Categorización Causa - TOLERADO", "Categorización Causa - NO SIGNIFICATIVO","Categorización Causa - OM"]].agg(' '.join, axis=1)
                    df['analisis_causas'] = df[["ACR CRÍTICO", "ACR MODERADO", "ACR TOLERADO", "ACR OP. DE MEJORA", "ACR NO SIGNIFICATIVO", "ACR IMPORTANTE"]].agg(' '.join, axis=1)
                    df['descripcion_hallazgo'] = df[["Titulo del Hallazgo", "Descripción del Hallazgo"]].agg(' '.join, axis=1)

                    columnas_calidad_df = ["codigo_aeropuerto", "codigo_talma", "nombre_cliente", "origen_archivo", "descripcion_hallazgo","causa_raiz", "analisis_causas"]
                    df = df[columnas_calidad_df]

                    #--- df listado procesos plan de accion ---#

                    df2 = read_csv_from_s3(bucket_name, path_aux)
                    df2 = homologar_columnas(df2, mapeo_talma)
                    df2 = df2.astype(str).replace("nan", " ")
                    df2['plan_accion'] = df2[["TIPO DE ACCION", "DESCRIPCION DE LA ACCION"]].agg(' '.join, axis=1)

                    columnas_calidad_df2 = ["codigo_talma", "plan_accion"]
                    df2 = df2[columnas_calidad_df2].copy()
                    df2['codigo_talma'] = df2['codigo_talma'].str.strip()
                    df2 = df2.groupby("codigo_talma", as_index=False).agg({"plan_accion": lambda x: " ".join(x)})

                    #--- df final calidad ------#

                    df_final = pd.merge(df, df2, how='left', on='codigo_talma')
                    df_final_calidad_columns = ["codigo_aeropuerto", "codigo_talma","nombre_cliente", "origen_archivo", "descripcion_hallazgo", "causa_raiz", "analisis_causas", "plan_accion"]
                    df_final = df_final[df_final_calidad_columns]
                    num_filas = df.shape[0]

                    print(f"El dataframe de seguridad procesado de la ruta: {path} y {path_aux} contiene {num_filas} registros")

                elif "BASE DE DATOS UNIFICADA" in path:

                    #-------- df seguridad operacional ----------#

                    df['origen_archivo'] = "Seguridad Operacional"

                    if "EXBOG" in path:

                        df['descripcion_hallazgo'] = df[["DESCRIPCIÓN DEL EVENTO", "CARACTERIZACIÓN", "OTRA CARACTERIZACIÓN"]].agg(' '.join, axis=1)
                        df["causa_raiz"] = df[["CAUSA PREDOMINANTE", "OTRAS CAUSAS NO IDENTIFICADAS EN DESPLEGABLE", "FACTOR CONTRIBUYENTE 1", "OTRO FACTOR CONTRIBUYENTE NO IDENTIFICADO EN DESPLEGABLE 1",
                        "FACTOR CONTRIBUYENTE 2", "OTRO FACTOR CONTRIBUYENTE NO IDENTIFICADO EN DESPLEGABLE 2"]].agg(' '.join, axis=1)

                    elif "BOG" in path:

                        df['descripcion_hallazgo'] = df[["DESCRIPCIÓN DEL EVENTO", "CARACTERIZACIÓN", "CARACTERIZACIÓN EVENTOS", "OTRA CARACTERIZACIÓN"]].agg(' '.join, axis=1)
                        df["causa_raiz"] = df[["CAUSA PREDOMINANTE", "OTRAS CAUSAS NO IDENTIFICADA EN DESPEGABLE", "FACTOR CONTRIBUYENTE 1", "OTRO FACTOR CONTRIBUYENTE NO IDENTIFICADO EN DESPLEGABLE 1",
                        "FACTOR CONTRIBUYENTE 2", "OTRO FACTOR CONTRIBUYENTE NO IDENTIFICADO EN DESPLEGABLE 2"]].agg(' '.join, axis=1)
                    else:
                        print("Archivo de seguridad desconocido")

                    #--- df final seguridad operacional ------#

                    columnas_seguridad = ["codigo_aeropuerto", "codigo_talma", "nombre_cliente", "origen_archivo", "descripcion_hallazgo", "causa_raiz", "analisis_causas", "plan_accion"]
                    df_final = df[columnas_seguridad]
                    num_filas = df.shape[0]

                    print(f"El dataframe de seguridad procesado de la ruta: {path} contiene {num_filas} registros")

                else:
                    raise ValueError(f"Error: El archivo '{path}' es desconocido.")

                df_final = df_final.fillna(" ")
                df_final = df_final.apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))
                user_file = df_final.to_json(orient="records")
                user_file_json = json.loads(user_file)

                # --- Crear nodos y asignar etiqueta ---#

                query_create_graph = """
                UNWIND $data AS row
                MERGE (i:Incidente {codigo_talma: row.codigo_talma})
                ON CREATE SET 
                i.codigo_aeropuerto = row.codigo_aeropuerto,
                i.nombre_cliente = row.nombre_cliente,
                i.origen_archivo = row.origen_archivo,
                i.descripcion_hallazgo = row.descripcion_hallazgo
                SET i:PendingEmbedding
                MERGE (a:Aeropuerto {codigo_aeropuerto: row.codigo_aeropuerto})
                MERGE (c:Cliente {nombre_cliente: row.nombre_cliente})
                MERGE (p:PlanAccion {codigo_talma: row.codigo_talma, texto: row.plan_accion})
                MERGE (r:CausaRaiz {codigo_talma: row.codigo_talma, texto: row.causa_raiz})
                MERGE (ac:AnalisisCausas {codigo_talma: row.codigo_talma, texto: row.analisis_causas})
                MERGE (a)-[:TIENE_UN]->(i)
                MERGE (c)-[:OPERA_EN]->(a)
                MERGE (i)-[:TIENE_PLAN_DE_ACCION]->(p)
                MERGE (i)-[:TIENE_CAUSA_RAIZ]->(r)
                MERGE (i)-[:TIENE_ANALISIS]->(ac)
                RETURN COUNT(i) AS created_nodes
                """
                result = session.run(query_create_graph, data=user_file_json)
                created_nodes = result.single()["created_nodes"]

                # --- Verificar si hay nodos con etiqueta `PendingEmbedding` ---#

                query_pending_nodes = f"""
                MATCH (n:{node_label})
                RETURN COUNT(n) AS pending_count
                """
                pending_result = session.run(query_pending_nodes)
                pending_count = pending_result.single()["pending_count"]

                if created_nodes > 0 or pending_count > 0:
                    
                    print(f"Se crearon {created_nodes} nodos con etiqueta 'PendingEmbedding'.")
                    print(f"Hay pendientes {pending_count} nodos con etiqueta 'PendingEmbedding'.")

                    try:

                        # --- Generar embeddings solo para nodos con la etiqueta `PendingEmbedding` --- #

                        print("Generando embeddings para nodos incidente con la etiqueta `PendingEmbedding`...")

                        Neo4jVector.from_existing_graph(
                            embedding=OpenAIEmbeddings(openai_api_key=openai_api_key),
                            url=neo4j_url,
                            username=neo4j_username,
                            password=neo4j_passwd,
                            index_name=index_name,
                            node_label=node_label,  
                            text_node_properties=text_node_properties,
                            embedding_node_property=embedding_node_property,
                        )
                        
                        # --- Actualizar etiquetas de los nodos incidente --- #

                        print("Actualizando etiquetas de los nodos incidente...")
                        
                        session.run(f"""
                        MATCH (n:{node_label})
                        REMOVE n:{node_label}
                        """)
                        
                    except Exception as e:
                        print(f"Error durante la generación de embeddings: {e}")

                else:
                    print("No se crearon nuevos nodos o no hay nodos con embeddings pendientes.")  

    except Exception as e:
        print(f"Ocurrió un error en la generacion de nodos y embeddings el cual es el siguiente: {e}")
    finally:
        driver.close()
        print("Conexión con la base de datos cerrada.")














            