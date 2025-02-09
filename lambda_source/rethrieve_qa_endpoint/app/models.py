from pydantic import BaseModel

class SimilarityRequest(BaseModel):
    id_generation: str = None 
    descripcion_hallazgo: str = None
    causa_raiz: str = None
    feedback: str = None

class GetResult(BaseModel):
    id_generation: str
