from langchain_community.vectorstores import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from config import neo4j_url, neo4j_username, neo4j_passwd, openai_api_key, index_name, text_node_property

def get_vector_store(retrieval_query=None):
    """
    Configura la conexión a Neo4jVector con o sin retrieval_query.
    """
    return Neo4jVector.from_existing_index(
        embedding=OpenAIEmbeddings(openai_api_key=openai_api_key),
        url=neo4j_url,
        username=neo4j_username,
        password=neo4j_passwd,
        index_name=index_name,
        text_node_property=text_node_property,
        retrieval_query=retrieval_query  
    )

