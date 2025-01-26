from pydantic import BaseModel

class SimilarityRequest(BaseModel):
    descripcion_hallazgo: str
    feedback: str = None
