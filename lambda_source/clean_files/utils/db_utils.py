
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


def connect_to_mongo(mongo_uri, db_name):
    """
    Establece una conexión con una base de datos de MongoDB y devuelve la referencia a la base de datos.

    Parámetros:
        mongo_uri (str): URI de conexión a MongoDB.
        db_name (str): Nombre de la base de datos a conectar.

    Retorna:
        Database: Referencia a la base de datos conectada.
    """
    try:

        client = MongoClient(mongo_uri, server_api=ServerApi('1'))
        db = client[db_name]

        client.admin.command('ping')
        print(f"Conexión exitosa a la base de datos: {db_name}")

        return db
    except Exception as e:
        print(f"Error al conectar a MongoDB: {e}")
        raise


def create_collection(db, collection_name, validator=None):
    """
    Crea una colección en la base de datos si no existe.

    Parámetros:
        db (Database): La base de datos donde se creará la colección.
        collection_name (str): Nombre de la colección a crear.
        validator (dict, opcional): Esquema de validación para la colección (si se proporciona).

    Comportamiento:
        - Si la colección no existe en la base de datos, la crea.
        - Si un validador es proporcionado, se aplica al crear la colección.
        - Si la colección ya existe, imprime un mensaje informativo.
    """
    # Verificar si la colección ya existe
    if collection_name not in db.list_collection_names():
        if validator:  
            db.create_collection(collection_name, validator=validator)
        else:
            db.create_collection(collection_name)
    else:
        print(f"Collection '{collection_name}' already exists.")


def insert_data_to_mongo(db, collection_name, data_frame):
    """
    Inserta los datos de un DataFrame de pandas en una colección de MongoDB.

    Parámetros:
        db (Database): La base de datos donde se encuentra la colección.
        collection_name (str): Nombre de la colección donde se insertarán los datos.
        data_frame (pd.DataFrame): DataFrame de pandas que contiene los datos a insertar.

    Comportamiento:
        - Convierte el DataFrame en una lista de diccionarios.
        - Inserta todos los registros en la colección especificada.
    """

    collection = db[collection_name]
    records = data_frame.to_dict(orient='records')
    collection.insert_many(records)






