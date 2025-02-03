from pydantic import BaseModel

class SimilarityRequest(BaseModel):
    descripcion_hallazgo: str
    causa_raiz: str
    feedback: str = None
