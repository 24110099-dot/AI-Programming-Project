"""Convert text into normalized vectors with sentence-transformers.

Select the model from an explicit argument, EMBEDDING_MODEL, or a multilingual default.
Cache the most recently requested model within the current Python process.
Return Python lists; reject invalid text before loading the model.
"""
import os 

from functools import lru_cache
DEFAULT_MODEL = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
@lru_cache(maxsize=1)
def get_model(model_name: str = DEFAULT_MODEL):
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)
def embed_texts(
        texts: list[str] , 
        model_name: str | None = None ,  

) -> list[list[float]]:
    if not isinstance(texts, list):
        raise TypeError("texts must be a list of strings")
    for text in texts:
        if not isinstance(text, str):
            raise TypeError("Each text must be a string")
        if not text.strip():
            raise ValueError("Text must not be blank")
        
        
    if not texts:
        return []
    selected_model =(
        model_name
        if model_name is not None 
        else os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL)
                       
    )
    model = get_model(selected_model)
    vectors = model.encode(texts, normalize_embeddings=True)
    return vectors.tolist()

def embed_text(
        text : str  ,
        model_name: str | None = None  ,


)-> list[float]:
    return embed_texts([text], model_name=model_name)[0]



